def paper(id='a',decision='Accept'):
    return {'forum_id':id,'title':'Title','keywords':[],'decision':decision,'source_url':f'https://openreview.net/forum?id={id}',
      'score_summary':{'scores':[2,4,6],'mean':4,'valid_review_count':3,'missing_rating_count':0,'scale_id':'x','score_stage':'observed_public_snapshot','snapshot_id':'s'},
      'report_state':'not_generated','issues':[],'reviews':[],'discussion':[],'paper_versions':[], 'coverage':{'original_available':False}}
def corpus(papers=None,complete=False):
    papers=papers if papers is not None else [paper()]
    return {'papers':papers,'snapshot_id':'s','coverage':{'capture_complete':complete,'discovered_count':len(papers),'processed_count':len(papers),'unprocessed_count':0,'forum_failure_count':0,'score_schema_verified':complete,'ranking_scope':'complete_capture' if complete else 'observed_sample'},
       'capture_manifest':{'capture_id':'test','started_at':'2026-09-27T00:00:00+00:00','completed_at':'2026-09-27T01:00:00+00:00','capture_complete':complete,'venue_schema_hash':'a'*64,'pages':[{'offset':0,'count':len(papers),'sha256':'a'*64}], 'forums':{p['forum_id']:{'ok':True,'sha256':'b'*64} for p in papers},'success_count':len(papers),'failure_count':0}}
def ranks(ids=None):
    ids=ids if ids is not None else ['a']
    return {'low_score_accepted':ids,'high_score_rejected':[],'candidate_ids':ids,'ties':{},'eligible_count':len(ids),'ranking_scope':'complete_capture'}
