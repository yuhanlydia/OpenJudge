"""Resumable, idempotent read-only capture. Raw note pages stay in ignored workdir."""
import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
from .fetch import RetryingClient,fetch_forum

def dump(path,obj):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp'); tmp.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)); os.replace(tmp,path)
def now(): return datetime.now(timezone.utc).isoformat()
def digest(obj): return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def _checkpoint_notes(workdir,pages):
    seen={}
    expected=0
    for page in pages:
        if page['offset']!=expected or page['count']<=0: raise ValueError('checkpoint_offset_mismatch')
        notes=json.loads((workdir/'pages'/f"{page['offset']}.json").read_text())
        if digest(notes)!=page['sha256'] or len(notes)!=page['count']: raise ValueError('checkpoint_hash_mismatch')
        expected+=len(notes)
        for note in notes: seen[note['id']]=note
    return seen,expected

def capture_corpus(config,workdir,resume=False,client=None):
    client=client or RetryingClient(); workdir=Path(workdir); workdir.mkdir(parents=True,exist_ok=True)
    path=workdir/'capture.json'; config_hash=digest({**{k:v for k,v in config.items() if k!='fetch_limits'},'page_size':config.get('fetch_limits',{}).get('page_size',1000)})
    previous=json.loads(path.read_text()) if resume and path.exists() else None
    if previous and previous.get('config_hash')!=config_hash: raise ValueError('checkpoint_config_mismatch')
    # A completed capture must be refreshed from page zero, including all child notes.
    if previous and previous.get('capture_complete'):
        previous=None
    if previous:
        seen,offset=_checkpoint_notes(workdir,previous['pages'])
        manifest=previous
    else:
        seen={};offset=0
        manifest={'schema_version':'1.0','capture_id':now(),'config_hash':config_hash,
          'venue_schema_hash':config.get('schema_hash'),'started_at':now(),'pages':[],
          'forums':{},'capture_complete':False,'errors':[]}
    manifest['capture_complete']=False
    manifest['errors']=[]
    dump(path,manifest)
    size=config.get('fetch_limits',{}).get('page_size',1000)
    try:
        while True:
            response=client.get_notes(invitation=config['submission_invitation'],limit=size,offset=offset,details='replies')
            page=response['notes']
            if not isinstance(page,list): raise ValueError('invalid_page')
            if page:
                dump(workdir/'pages'/f'{offset}.json',page)
                manifest['pages'].append({'offset':offset,'count':len(page),'new_count':len({n['id'] for n in page}-seen.keys()),
                    'sha256':digest(page),'api_count':response.get('count')})
                for n in page: seen[n['id']]=n
                offset+=len(page);dump(path,manifest)
            if len(page)<size:
                if response.get('count') is not None and response['count']!=offset: raise ValueError('page_count_mismatch')
                break
        # Every forum receives a fresh child query in this capture. A failure is recorded per forum,
        # never interpreted as an empty discussion. Resumed partial checkpoints recheck existing forums.
        for forum in sorted(seen):
            try:
                notes=fetch_forum(forum,client)
                if not any(n.get('id')==forum for n in notes):
                    # Some APIs return only replies on forum query; the submission is already captured.
                    notes=[seen[forum],*notes]
                dump(workdir/'forums'/f'{forum}.json',notes)
                manifest['forums'][forum]={'count':len(notes),'sha256':digest(notes),'ok':True}
            except Exception as e:
                manifest['forums'][forum]={'ok':False,'code':type(e).__name__}
                manifest['errors'].append({'code':'forum_fetch_failed','forum_id':forum})
                if 'permission_403' in str(e) or 'permission_401' in str(e):
                    dump(path,manifest);break
            dump(path,manifest)
        for forum in sorted(seen):
            if forum not in manifest['forums']:
                manifest['forums'][forum]={'ok':False,'code':'not_attempted_after_access_failure'}
                manifest['errors'].append({'code':'forum_not_attempted','forum_id':forum})
        manifest['capture_complete']=True
    except Exception as e:
        manifest['errors'].append({'code':type(e).__name__,'offset':offset})
    manifest['success_count']=len(seen)
    manifest['failure_count']=sum(not v.get('ok') for v in manifest['forums'].values())
    manifest['forum_count']=len(manifest['forums'])
    manifest['completed_at']=now();dump(path,manifest)
    return manifest
