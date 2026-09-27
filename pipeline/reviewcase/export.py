"""Allowlisted and staged public JSON export."""
import hashlib,json,os,shutil,tempfile,re
from pathlib import Path
from .capture import dump,now
from .validate import validate_public
from .evidence import build_evidence_bundle
from .report import public_report,validate_report,mark_stale
PAPER_FIELDS=('forum_id','submission_number','title','abstract','keywords','conference','track','decision','decision_source_id','decision_source_kind','decision_time','observed_at','paper_versions','source_url','license','coverage','issues','score_summary','report_state')
REVIEW_FIELDS=('review_id','forum_id','public_alias','invitation','content_fields','rating_raw','rating_value','scale_id','confidence_raw','created_at','modified_at','revision_id','source_hash','visibility_checked_at')
VERSION_FIELDS=('version_id','note_id','available_at','source_url','sha256','version_role','public_available')
DISCUSSION_FIELDS=('note_id','replyto','invitation','content_fields','source_hash')
CONTENT_FIELDS=('summary','strengths','weaknesses','questions','limitations','rating','confidence','comment','recommendation','decision')
def allow(obj,fields): return {k:obj[k] for k in fields if k in obj}
def hash_file(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def _denylist(path):
    if path is None: path=Path(__file__).resolve().parents[2]/'config'/'denylist.json'
    return set(json.loads(Path(path).read_text()).get('forum_ids',[])) if Path(path).exists() else set()
def export_public(corpus,rankings,output,reports_dir=None,denylist_path=None):
    output=Path(output); output.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix=f'.{output.name}-candidate-',dir=output.parent))
    stamp=now();sid=corpus['snapshot_id'];fixture=corpus.get('is_fixture',False)
    common={'schema_version':'1.0','snapshot_id':sid,'generated_at':stamp,'is_fixture':fixture}
    denied=_denylist(denylist_path);index=[]
    try:
        for raw in corpus['papers']:
            forum=raw['forum_id']
            if forum in denied: continue
            if not forum or '/' in forum or '..' in forum: raise ValueError('invalid_forum_id')
            p=allow(raw,PAPER_FIELDS)
            p['reviews']=[{**allow(r,REVIEW_FIELDS),'content_fields':allow(r.get('content_fields',{}),CONTENT_FIELDS)} for r in raw.get('reviews',[])]
            p['discussion']=[{**allow(d,DISCUSSION_FIELDS),'content_fields':allow(d.get('content_fields',{}),CONTENT_FIELDS)} for d in raw.get('discussion',[])]
            p['paper_versions']=[allow(v,VERSION_FIELDS) for v in raw.get('paper_versions',[])]
            p['report_state']='not_generated'
            if reports_dir:
                for report_file in sorted((Path(reports_dir)/forum).glob('*.json')):
                    report=json.loads(report_file.read_text())
                    if report.get('editorial_state') not in ('approved','published'): continue
                    bundle=build_evidence_bundle(forum,corpus)
                    report=mark_stale(report,bundle['bundle_hash'],bundle['rubric_version'])
                    if report['editorial_state']=='stale':p['report_state']='stale';continue
                    if validate_report(report,bundle)['ok']:
                        p['report']=public_report(report)
                        p['evidence_bundle_id']=bundle['bundle_id']
                        cards=[allow(e,('evidence_id','source_type','note_id','source_hash','paper_version_id','page_number','section','table','character_start','character_end','quote','source_url','translation')) for e in bundle['evidence']]
                        p['evidence']=cards
                        dump(stage/'evidence'/f'{forum}.json',{**common,'forum_id':forum,'bundle_hash':bundle['bundle_hash'],'evidence':cards})
                        if report['snapshot_id']!=sid:p['report']['reused_from_snapshot']=report['snapshot_id']
                        p['report_state']='published';break
            dump(stage/'papers'/f'{forum}.json',{**common,**p})
            index.append(allow(p,('forum_id','title','keywords','decision','source_url','score_summary','report_state','issues')))
        coverage={**common,**corpus['coverage']}
        if denied:
            coverage['redacted_count']=len({p['forum_id'] for p in corpus['papers']} & denied)
            coverage['processed_count']=len(index)
            coverage['unprocessed_count']=coverage.get('discovered_count',0)-len(index)
            removed={p['forum_id'] for p in corpus['papers']} & denied
            if removed:
                reason='emergency_correction'
                source=Path(denylist_path) if denylist_path else Path(__file__).resolve().parents[2]/'config'/'denylist.json'
                if source.exists(): reason=json.loads(source.read_text()).get('reason',reason)
                dump(stage/'redactions.json',{'schema_version':'1.0','removed_forum_ids':sorted(removed),'reason':reason})
        clean_rankings={k:([i for i in v if i not in denied] if k in ('low_score_accepted','high_score_rejected','candidate_ids') else v) for k,v in rankings.items()}
        clean_rankings['eligible_count']=len(clean_rankings.get('low_score_accepted',[]))+len(clean_rankings.get('high_score_rejected',[]))
        clean_rankings={**common,**clean_rankings}
        dump(stage/'index'/'iclr2026.json',{**common,'papers':index})
        dump(stage/'coverage.json',coverage);dump(stage/'rankings.json',clean_rankings)
        files={str(p.relative_to(stage)):hash_file(p) for p in sorted(stage.rglob('*.json'))}
        capture=corpus.get('capture_manifest',{})
        manifest={**common,'file_hashes':files,'coverage':coverage,'capture_complete':coverage.get('capture_complete',False),
                  'capture_manifest':{k:v for k,v in capture.items() if k in ('capture_id','config_hash','venue_schema_hash','started_at','completed_at','pages','forums','forum_count','success_count','failure_count','capture_complete','errors')}}
        dump(stage/'manifest.json',manifest)
        for artifact in stage.rglob('*.json'):
            if re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',artifact.read_text()):
                raise ValueError('private_email_in_public_artifact')
        result=validate_public(stage,'production' if coverage.get('capture_complete') else 'fixture')
        if not result['ok']:raise ValueError(f'candidate_invalid:{[e["code"] for e in result["errors"]]}')
        if output.exists() and validate_public(output,'production')['ok'] and not validate_public(stage,'production')['ok']:
            raise ValueError('cannot_replace_valid_public_with_incomplete_capture')
        backup=output.with_name(output.name+'.previous')
        if backup.exists():shutil.rmtree(backup)
        if output.exists():output.rename(backup)
        try:stage.rename(output)
        except Exception:
            if backup.exists():backup.rename(output)
            raise
        if backup.exists():shutil.rmtree(backup)
        return manifest
    finally:
        if stage.exists():shutil.rmtree(stage)
