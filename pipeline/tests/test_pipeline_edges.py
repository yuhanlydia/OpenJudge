import json,urllib.error
from pathlib import Path
from datetime import datetime,timezone
from reviewcase.capture import capture_corpus,dump
from reviewcase.fetch import RetryingClient,FetchError,fetch_forum
from reviewcase.normalize import normalize_capture
from reviewcase.score import resolve_decision
from reviewcase.rank import build_rankings
from reviewcase.report import validate_report,approve_report
from reviewcase.release import add_months,redact_all
from reviewcase.export import export_public
from helpers import paper,corpus,ranks

CFG={'venue_id':'V','submission_invitation':'V/-/Submission','review_name':'Official_Review','decision_name':'Decision','decision_field':'decision',
'decision_labels':{'Accept':'Accept','Reject':'Reject'},'verified':True,'score_schema':{'field_name':'rating','scale_id':'x','allowed_values':['2: Low','4: Medium','6: High']},'fetch_limits':{'page_size':2}}

def note(id,details=None): return {'id':id,'forum':id,'number':1,'content':{'title':{'value':'Title'},'venueid':{'value':'V'}},'details':{'replies':details or []}}
def review(id,alias,rating): return {'id':id,'invitations':['V/Submission1/-/Official_Review'],'signatures':['V/Submission1/'+alias], 'content':{'rating':{'value':rating},'confidence':{'value':'4'}}}

def test_pagination_failure_is_not_empty_page_and_resume(tmp_path):
    class Client:
        failed=True
        def get_notes(self,**kwargs):
            if 'forum' in kwargs:return {'notes':[note(kwargs['forum'])]}
            if kwargs['offset']==0: return {'notes':[note('a'),note('b')], 'count':3}
            if self.failed: raise TimeoutError()
            return {'notes':[note('c')], 'count':3}
    client=Client()
    first=capture_corpus(CFG,tmp_path,client=client)
    assert first['capture_complete'] is False and first['success_count']==2
    client.failed=False
    second=capture_corpus(CFG,tmp_path,resume=True,client=client)
    assert second['capture_complete'] and second['success_count']==3 and [p['offset'] for p in second['pages']]==[0,2]

def test_retry_after_and_permission_no_bypass():
    calls=[]; waits=[]
    def transport(path):
        calls.append(path)
        if len(calls)<3: raise urllib.error.HTTPError('u',429,'limit',{'Retry-After':'2'},None)
        return {'notes':[]}
    c=RetryingClient(transport,delay=0,sleep=waits.append)
    assert c.request('/notes')['notes']==[] and waits.count(2)==2 and len(calls)==3
    def deny(path): raise urllib.error.HTTPError('u',403,'challenge',{},None)
    c=RetryingClient(deny,delay=0,sleep=lambda _:None)
    try: c.request('/notes')
    except FetchError as e: assert str(e)=='permission_403'
    else: assert False

def test_nested_reply_and_alias_conflict(tmp_path):
    deep={'id':'child','replyto':'comment','content':{'comment':{'value':'reply'}}}
    comment={'id':'comment','replyto':'a','content':{'comment':{'value':'hello'}},'details':{'replies':[deep]}}
    a=note('a',[review('r1','Reviewer_A','2: Low'),review('r2','Reviewer_A','4: Medium'),comment])
    class Client:
        def get_notes(self,**kwargs): return {'notes':[a]}
    assert {'r1','r2','comment','child'} <= {x['id'] for x in fetch_forum('a',Client())}
    dump(tmp_path/'pages'/'0.json',[a]); cap={'directory':str(tmp_path),'pages':[{'offset':0}],'capture_id':'x','capture_complete':True,'completed_at':'2026-09-27T00:00:00+00:00'}
    corpus=normalize_capture(cap,CFG)
    p=corpus['papers'][0]
    assert 'duplicate_reviewer_alias' in p['issues'] and p['score_summary']['valid_review_count']==0
    assert any(d['note_id']=='child' and d['replyto']=='comment' for d in p['discussion'])
    assert p['paper_versions'][0]['version_role']=='unknown' and not p['coverage']['original_available']

def test_decision_conflict_and_status():
    d=lambda id,text:{'id':id,'invitations':['V/Submission1/-/Decision'],'content':{'decision':{'value':text}}}
    assert resolve_decision([d('a','Accept'),d('b','Reject')],CFG)['decision']=='Conflict'
    assert resolve_decision([],dict(CFG,rejected_venue_id='R'),'R')['source_kind']=='status_only'

def test_missing_original_blocks_contradiction_and_approval():
    report={'forum_id':'a','evidence_bundle_hash':'h','claims':[{'claim_id':'c','claim_status':'contradicted','original_submission_claim':True,'supporting_evidence_ids':['e']}], 'model_provenance':'user_reported'}
    bundle={'forum_id':'a','bundle_hash':'h','coverage':{'original_available':False},'evidence':[{'evidence_id':'e','quote':'abc','source_text':'abc'}]}
    assert any(e['code']=='original_unavailable' for e in validate_report(report,bundle)['errors'])
    try: approve_report(report,'Editor',{})
    except ValueError: pass
    else: assert False

def test_calendar_end_of_month_and_redaction_all(tmp_path):
    assert add_months(datetime(2026,1,31,tzinfo=timezone.utc)).date().isoformat()=='2026-04-30'
    data=corpus()
    ranking=ranks()
    public=tmp_path/'public';release=tmp_path/'releases'/'R1'
    export_public(data,ranking,public);export_public(data,ranking,release)
    redact_all(public,tmp_path/'releases',{'a'},denylist_path=tmp_path/'denylist.json',content_dir=tmp_path/'reports')
    for root in [public,release]:
        assert not (root/'papers'/'a.json').exists()
        assert json.loads((root/'index'/'iclr2026.json').read_text())['papers']==[]
        assert json.loads((root/'rankings.json').read_text())['low_score_accepted']==[]
