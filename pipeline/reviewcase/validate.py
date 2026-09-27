"""Validate exact public inventory, JSON contracts, provenance and ranking links."""
import hashlib,json,re
from pathlib import Path
from jsonschema import Draft202012Validator

def validate_public(output,mode='production'):
    output=Path(output); errors=[]
    def add(code,id=None): errors.append({'code':code,'record_id':id})
    def read(name): return json.loads((output/name).read_text())
    try:
        manifest=read('manifest.json');coverage=read('coverage.json');index=read('index/iclr2026.json');rankings=read('rankings.json')
    except (OSError,ValueError): return {'ok':False,'errors':[{'code':'missing_or_invalid_core','record_id':None}],'warnings':[]}
    schema_dir=Path(__file__).resolve().parents[2]/'schemas'
    for name,obj,schema in [('index/iclr2026.json',index,'public-index'),('coverage.json',coverage,None),('rankings.json',rankings,None)]:
        if schema:
            validator=Draft202012Validator(json.loads((schema_dir/f'{schema}.schema.json').read_text()))
            for e in validator.iter_errors(obj): add('schema_invalid',name)
    sid=manifest.get('snapshot_id');fixture=manifest.get('is_fixture')
    if not sid or manifest.get('schema_version')!='1.0': add('invalid_manifest_identity')
    forbidden=re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
    for artifact in output.rglob('*'):
        if artifact.is_file() and artifact.suffix=='.json' and forbidden.search(artifact.read_text()): add('private_email_in_public_artifact',str(artifact.relative_to(output)))
    for name,obj in [('coverage.json',coverage),('index/iclr2026.json',index),('rankings.json',rankings)]:
        if any(obj.get(k)!=manifest.get(k) for k in ('schema_version','snapshot_id','generated_at','is_fixture')): add('metadata_mismatch',name)
    ids=[]
    for row in index.get('papers',[]):
        forum=row.get('forum_id');ids.append(forum)
        if not isinstance(forum,str) or not re.fullmatch(r'[A-Za-z0-9_-]+',forum): add('invalid_forum_id');continue
        try: detail=read(f'papers/{forum}.json')
        except (OSError,ValueError): add('missing_paper',forum);continue
        validator=Draft202012Validator(json.loads((schema_dir/'paper-detail.schema.json').read_text()))
        if list(validator.iter_errors(detail)): add('schema_invalid',forum)
        if any(detail.get(k)!=manifest.get(k) for k in ('schema_version','snapshot_id','generated_at','is_fixture')): add('metadata_mismatch',forum)
        for k in row:
            if row[k]!=detail.get(k): add('index_detail_mismatch',forum);break
        if detail.get('report_state') in ('published','approved'):
            report=detail.get('report')
            try: public_evidence=read(f'evidence/{forum}.json')
            except (OSError,ValueError): public_evidence=None
            if not isinstance(report,dict) or not isinstance(public_evidence,dict): add('report_evidence_missing',forum)
            else:
                from .report import report_digest
                report_schema=Draft202012Validator(json.loads((schema_dir/'analysis-report.schema.json').read_text()))
                if list(report_schema.iter_errors(report)): add('report_schema_invalid',forum)
                binding=report.get('approval_binding',{})
                if not isinstance(binding,dict) or binding.get('report_digest')!=report_digest(report) or binding.get('bundle_hash')!=report.get('evidence_bundle_hash') or binding.get('report_id')!=report.get('report_id') or binding.get('record_id')!=report.get('approval_record_id') or binding.get('actor')!=report.get('reviewer_of_report') or binding.get('approved_at')!=report.get('approved_at') or binding.get('rubric_version')!=report.get('rubric_version'):
                    add('report_approval_invalid',forum)
                cards=public_evidence.get('evidence',[])
                refs={c.get('evidence_id') for c in cards}
                if public_evidence.get('forum_id')!=forum or public_evidence.get('snapshot_id')!=sid or public_evidence.get('bundle_hash')!=report.get('evidence_bundle_hash') or detail.get('evidence')!=cards:
                    add('evidence_binding_invalid',forum)
                for claim in report.get('claims',[]):
                    if not set(claim.get('supporting_evidence_ids',[])+claim.get('counter_evidence_ids',[]))<=refs:
                        add('missing_evidence_id',forum)
                if any('source_text' in c or not re.fullmatch(r'[a-f0-9]{64}',str(c.get('source_hash',''))) for c in cards):
                    add('unsafe_public_evidence',forum)

    if len(ids)!=len(set(ids)): add('duplicate_papers')
    if coverage.get('discovered_count')!=coverage.get('processed_count',0)+coverage.get('unprocessed_count',0): add('count_mismatch')
    if coverage.get('processed_count')!=len(ids): add('index_count_mismatch')
    for board in ('low_score_accepted','high_score_rejected','candidate_ids'):
        if not isinstance(rankings.get(board),list) or any(i not in ids for i in rankings.get(board,[])): add('invalid_ranking_membership',board)
    files=manifest.get('file_hashes')
    actual={str(p.relative_to(output)) for p in output.rglob('*') if p.is_file() and p.name!='manifest.json'}
    expected={'coverage.json','rankings.json','index/iclr2026.json'}|{f'papers/{i}.json' for i in ids}|{f'evidence/{i}.json' for i in ids if (output/'evidence'/f'{i}.json').exists()}
    if 'redactions.json' in actual: expected.add('redactions.json')
    if actual!=expected or not isinstance(files,dict) or set(files)!=actual: add('inventory_mismatch')
    for name,sha in (files or {}).items():
        p=output/name
        if not p.is_file() or not re.fullmatch(r'[a-f0-9]{64}',str(sha)) or hashlib.sha256(p.read_bytes()).hexdigest()!=sha:
            add('file_hash_mismatch',name)
    capture=manifest.get('capture_manifest',{})
    if mode=='production':
        if fixture is not False or any(x.get('is_fixture') is not False for x in (index,rankings,coverage)): add('fixture_forbidden')
        if not manifest.get('capture_complete') or not capture.get('capture_complete') or not coverage.get('capture_complete'): add('incomplete_enumeration')
        if not coverage.get('score_schema_verified') or not re.fullmatch(r'[a-f0-9]{64}',str(capture.get('venue_schema_hash',''))): add('unverified_score_schema')
        if (not ids and not (output/'redactions.json').exists()) or not capture.get('capture_id') or not capture.get('completed_at') or not capture.get('started_at'): add('missing_capture_provenance')
        pages=capture.get('pages');forums=capture.get('forums')
        redacted=set(read('redactions.json').get('removed_forum_ids',[])) if (output/'redactions.json').exists() else set()
        if not isinstance(pages,list) or not pages or not isinstance(forums,dict) or set(forums)-redacted!=set(ids): add('capture_inventory_mismatch')
        else:
            offset=0
            for p in pages:
                if p.get('offset')!=offset or not isinstance(p.get('count'),int) or p['count']<=0 or not re.fullmatch(r'[a-f0-9]{64}',str(p.get('sha256',''))): add('capture_page_invalid')
                offset+=p.get('count',0)
            failures=sum(not f.get('ok') for f in forums.values())
            if capture.get('success_count')!=len(forums) or capture.get('failure_count')!=failures or coverage.get('forum_failure_count')!=failures or any((not f.get('code')) if not f.get('ok') else not re.fullmatch(r'[a-f0-9]{64}',str(f.get('sha256',''))) for f in forums.values()): add('capture_forum_invalid')
            expected_scope='observed_sample' if failures else 'complete_capture'
            if coverage.get('ranking_scope')!=expected_scope: add('ranking_scope_mismatch')
    return {'ok':not errors,'errors':errors,'warnings':[]}
