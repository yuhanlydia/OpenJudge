import json,re
from pathlib import Path
from .capture import digest,now
from .score import parse_rating,summarize,resolve_decision
from .discover import value

SAFE_CONTENT=('summary','strengths','weaknesses','questions','limitations','rating','confidence','comment','recommendation','decision')
def sanitize_content(content):
    return {k:value(content,k) for k in SAFE_CONTENT if k in content and isinstance(value(content,k),(str,int,float,bool))}
def normalize_capture(capture,config):
    directory=Path(capture['directory']) if 'directory' in capture else Path(capture['workdir'])
    notes=[]
    for page in capture['pages']:
        notes.extend(json.loads((directory/'pages'/f"{page['offset']}.json").read_text()))
    unique={n['id']:n for n in notes}
    forum_sources={}
    for forum,record in capture.get('forums',{}).items():
        if record.get('ok'):
            source=json.loads((directory/'forums'/f'{forum}.json').read_text())
            if digest(source)!=record.get('sha256'): raise ValueError('forum_source_hash_mismatch')
            forum_sources[forum]=source
    snapshot_id=digest({'submissions':{i:digest(n) for i,n in unique.items()},'forums':{i:digest(v) for i,v in forum_sources.items()}})[:20]
    papers=[]; issues=[]; all_reviews=[]
    schema=config.get('score_schema') if config.get('verified') is True else None; review_name=config.get('review_name','Official_Review')
    for n in unique.values():
        forum=n.get('forum',n['id']); replies=[x for x in forum_sources.get(forum,[]) if x.get('id')!=n['id']] if forum in forum_sources else n.get('details',{}).get('replies',[])
        # Cached detailed replies are flattened recursively when supplied by API.
        children=[]; queue=list(replies); child_ids=set()
        while queue:
            child=queue.pop(0)
            if child.get('id') in child_ids: continue
            child_ids.add(child.get('id')); children.append(child)
            queue.extend(child.get('details',{}).get('replies',[]))
        review_notes=[x for x in children if any(str(i).endswith('/-/'+review_name) for i in (x.get('invitations') or [x.get('invitation','')]))]
        aliases={}; reviews=[]; paper_issues=[]
        for r in review_notes:
            alias=next((s.split('/')[-1] for s in r.get('signatures',[]) if re.fullmatch(r'Reviewer_[A-Za-z0-9]+',s.split('/')[-1])),None)
            if alias: aliases.setdefault(alias,[]).append(r['id'])
            rating=parse_rating(r,schema)
            if schema and value(r.get('content',{}),config.get('rating_field','rating')) is not None and rating is None:
                issues.append({'forum_id':forum,'code':'invalid_rating_label','record_id':r['id']})
                paper_issues.append('invalid_rating_label')
            reviews.append({'review_id':r['id'],'forum_id':forum,'public_alias':alias,'invitation':next(iter(r.get('invitations',[])),r.get('invitation')),
              'content_fields':sanitize_content(r.get('content',{})), 'rating_raw':value(r.get('content',{}),config.get('rating_field','rating')),
              'rating_value':float(rating) if rating is not None else None,'scale_id':schema.get('scale_id') if schema else None,
              'confidence_raw':value(r.get('content',{}),config.get('confidence_field','confidence')),
              'created_at':r.get('cdate'),'modified_at':r.get('mdate'),'revision_id':None,'source_hash':digest(sanitize_content(r.get('content',{}))),
              'visibility_checked_at':capture.get('completed_at')})
        conflicts=[a for a,ids in aliases.items() if len(set(ids))>1]
        if conflicts: paper_issues.append('duplicate_reviewer_alias')
        if not schema: paper_issues.append('unverified_score_schema')
        decision=resolve_decision(children,config,value(n.get('content',{}),'venueid'))
        if decision['decision']=='Conflict': paper_issues.append('decision_conflict')
        if decision['source_kind']=='status_only': paper_issues.append('decision_status_only')
        selected=[r for r in reviews if not r['public_alias'] or r['public_alias'] not in conflicts]
        # An available revised submission cannot be assumed to be the original submission.
        version={'version_id':n['id'],'note_id':n['id'],'available_at':n.get('cdate'),'source_url':f'https://openreview.net/forum?id={forum}',
                 'sha256':digest({'id':n['id'],'content':n.get('content',{})}),'version_role':'unknown','public_available':True}
        paper={'forum_id':forum,'submission_number':n.get('number'),'title':value(n.get('content',{}),'title'),
          'abstract':value(n.get('content',{}),'abstract'),'keywords':value(n.get('content',{}),'keywords',[]),
          'conference':config['venue_id'],'track':value(n.get('content',{}),'track'),**decision,
          'decision_source_id':decision['source_id'],'decision_source_kind':decision['source_kind'],
          'decision_time':None,'observed_at':capture.get('completed_at'),'paper_versions':[version],
          'source_url':f'https://openreview.net/forum?id={forum}','license':value(n.get('content',{}),'license'),
          'coverage':{'original_available':False,'forum_replies_observed':forum in forum_sources,'forum_fetch_ok':forum in forum_sources}, 'issues':paper_issues,
          'reviews':reviews,'discussion':[{'note_id':x.get('id'),'replyto':x.get('replyto'),'invitation':x.get('invitations',[]),
                         'content_fields':sanitize_content(x.get('content',{})),'source_hash':digest(sanitize_content(x.get('content',{})))} for x in children if x not in review_notes],
          'score_summary':summarize([r['rating_value'] for r in selected],schema,snapshot_id), 'report_state':'not_generated'}
        if conflicts: issues.append({'forum_id':forum,'code':'duplicate_reviewer_alias'})
        papers.append(paper); all_reviews+=reviews
    coverage={'capture_complete':capture['capture_complete'],'discovered_count':len(unique),'processed_count':len(papers),
              'unprocessed_count':0,'forum_failure_count':capture.get('failure_count',0), 'ranking_scope':'observed_sample' if not capture['capture_complete'] or capture.get('failure_count',0) or not schema else 'complete_capture',
              'score_schema_verified':bool(schema) and config.get('verified') is True}
    return {'papers':papers,'reviews':all_reviews,'coverage':coverage,'issues':issues,'snapshot_id':snapshot_id,
            'capture_manifest':capture}
