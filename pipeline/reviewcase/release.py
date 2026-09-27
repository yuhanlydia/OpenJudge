import calendar,json,shutil,hashlib
from pathlib import Path
from datetime import datetime,timezone
from .capture import dump
from .validate import validate_public

def add_months(date,months=3):
    month=date.month-1+months; year=date.year+month//12; month=month%12+1
    return date.replace(year=year,month=month,day=min(date.day,calendar.monthrange(year,month)[1]))
def release_snapshot(public_dir,releases_dir,release_id,metadata):
    validation=validate_public(public_dir,'production')
    if not validation['ok']: raise ValueError(validation['errors'])
    started=datetime.fromisoformat(metadata['collection_started_at']); completed=datetime.fromisoformat(metadata['collection_completed_at'])
    if completed<started: raise ValueError('invalid_collection_window')
    source_manifest=json.loads((Path(public_dir)/'manifest.json').read_text())
    if metadata['snapshot_id']!=source_manifest['snapshot_id']: raise ValueError('release_snapshot_mismatch')
    if not metadata.get('approval_record_id'): raise ValueError('release_approval_required')
    releases_dir=Path(releases_dir); dest=releases_dir/release_id
    if dest.exists(): raise FileExistsError('release already exists')
    stage=releases_dir/(release_id+'.tmp')
    if stage.exists(): shutil.rmtree(stage)
    shutil.copytree(public_dir,stage)
    prior_due=None
    if metadata.get('release_kind')=='correction' and metadata.get('previous_release_id'):
        prior_path=releases_dir/metadata['previous_release_id']/'release-manifest.json'
        if not prior_path.exists(): raise ValueError('previous_release_missing')
        prior_due=json.loads(prior_path.read_text()).get('next_review_due')
    release={'schema_version':'1.0','release_id':release_id,'snapshot_id':metadata['snapshot_id'],'previous_release_id':metadata.get('previous_release_id'),
      'release_kind':metadata.get('release_kind','quarterly'),'collection_started_at':started.isoformat(),
      'collection_completed_at':completed.isoformat(),'generated_at':metadata['generated_at'],'published_at':None,
      'next_review_due':prior_due,'refresh_interval_months':3,'cadence_mode':'quarterly_manual',
      'score_stage':'observed_public_snapshot','file_hashes':json.loads((stage/'manifest.json').read_text())['file_hashes'],
      'change_summary':metadata.get('change_summary',[]),'coverage':json.loads((stage/'coverage.json').read_text()),
      'approval_record_id':metadata['approval_record_id']}
    dump(stage/'release-manifest.json',release); stage.rename(dest)
    index_path=releases_dir/'index.json'; index=json.loads(index_path.read_text()) if index_path.exists() else {'releases':[]}
    index['releases'].append({'release_id':release_id,'snapshot_id':release['snapshot_id']});dump(index_path,index)
    return release

def mark_published(release_dir,published_at):
    path=Path(release_dir)/'release-manifest.json'
    manifest=json.loads(path.read_text())
    date=datetime.fromisoformat(published_at)
    if date.tzinfo is None: raise ValueError('publication_timezone_required')
    if manifest.get('published_at'): raise ValueError('release_already_published')
    manifest['published_at']=date.isoformat()
    if manifest['release_kind']=='quarterly':manifest['next_review_due']=add_months(date).isoformat()
    dump(path,manifest)
    return manifest

def redact_all(public_dir,releases_dir,denylist,content_dir=None,denylist_path=None):
    """Durable emergency removal across current, historical, and report surfaces."""
    from .export import _denylist
    denylist=set(denylist)
    if denylist_path is None: denylist_path=Path(__file__).resolve().parents[2]/'config'/'denylist.json'
    denylist_path=Path(denylist_path)
    prior=_denylist(denylist_path); all_denied=prior|denylist
    dump(denylist_path,{'schema_version':'1.0','forum_ids':sorted(all_denied),'reason':'emergency_correction'})
    if content_dir is None:content_dir=Path(__file__).resolve().parents[2]/'content'/'reports'
    for forum in all_denied:
        shutil.rmtree(Path(content_dir)/forum,ignore_errors=True)
    for root in [Path(public_dir),*Path(releases_dir).glob('*/')]:
        index_path=root/'index'/'iclr2026.json'
        if not index_path.exists():continue
        index=json.loads(index_path.read_text());old={p['forum_id'] for p in index['papers']}
        removed=old&all_denied
        index['papers']=[p for p in index['papers'] if p['forum_id'] not in all_denied]
        dump(index_path,index)
        for forum in all_denied:
            for folder in ('papers','evidence','reports','bundles'):
                (root/folder/f'{forum}.json').unlink(missing_ok=True)
                shutil.rmtree(root/folder/forum,ignore_errors=True)
        rank_path=root/'rankings.json'
        if rank_path.exists():
            ranks=json.loads(rank_path.read_text())
            for k in ('low_score_accepted','high_score_rejected','candidate_ids'):
                ranks[k]=[i for i in ranks.get(k,[]) if i not in all_denied]
            ranks['eligible_count']=len(ranks.get('low_score_accepted',[]))+len(ranks.get('high_score_rejected',[]))
            ranks['ties']={k:0 for k in ranks.get('ties',{})}
            dump(rank_path,ranks)
        cov_path=root/'coverage.json';coverage=json.loads(cov_path.read_text())
        coverage['processed_count']=len(index['papers'])
        coverage['unprocessed_count']=coverage.get('discovered_count',0)-coverage['processed_count']
        coverage['redacted_count']=coverage.get('redacted_count',0)+len(removed)
        dump(cov_path,coverage)
        dump(root/'redactions.json',{'schema_version':'1.0','removed_forum_ids':sorted(all_denied),'reason':'emergency_correction'})
        manifest_path=root/'manifest.json';manifest=json.loads(manifest_path.read_text())
        manifest['coverage']=coverage
        manifest['file_hashes']={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*.json') if p.name not in ('manifest.json','release-manifest.json')}
        dump(manifest_path,manifest)
        release_path=root/'release-manifest.json'
        if release_path.exists():
            release=json.loads(release_path.read_text());release['file_hashes']=manifest['file_hashes'];release['coverage']=coverage
            release['change_summary']=release.get('change_summary',[])+[{'kind':'redaction','forum_ids':sorted(removed)}]
            dump(release_path,release)
