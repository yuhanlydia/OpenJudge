import json,hashlib
from pathlib import Path
import pytest
from reviewcase.capture import capture_corpus,dump,digest
from reviewcase.normalize import normalize_capture
from reviewcase.score import resolve_decision
from reviewcase.export import export_public
from reviewcase.validate import validate_public
from reviewcase.evidence import build_evidence_bundle
from reviewcase.report import validate_report,approve_report,report_digest
from reviewcase.rank import build_rankings
from reviewcase.release import redact_all
from helpers import paper,corpus,ranks

CFG={'venue_id':'V','submission_invitation':'V/-/Submission','review_name':'Official_Review','rating_field':'rating','score_schema':{'scale_id':'x','field_name':'rating','allowed_values':['2: Low']},'verified':True,'fetch_limits':{'page_size':10}}
def submission():return {'id':'a','forum':'a','content':{'title':{'value':'Title'}},'mdate':1}
def review(text):return {'id':'r','forum':'a','replyto':'a','invitations':['V/Submission1/-/Official_Review'],'content':{'rating':{'value':'2: Low'},'summary':{'value':text}}}
class Client:
    def __init__(self):self.child='old';self.fail=False;self.calls=[]
    def get_notes(self,**kwargs):
        self.calls.append(kwargs)
        if self.fail:raise TimeoutError()
        if 'forum' in kwargs:return {'notes':[submission(),review(self.child)]}
        return {'notes':[submission()],'count':1}

def test_refresh_child_changes_snapshot_without_parent_mdate(tmp_path):
    c=Client();one=capture_corpus(CFG,tmp_path,client=c)
    assert one['capture_complete'] and one['forums']['a']['ok']
    before=normalize_capture(dict(one,directory=str(tmp_path)),CFG)['snapshot_id']
    c.child='new';two=capture_corpus(CFG,tmp_path,resume=True,client=c)
    after=normalize_capture(dict(two,directory=str(tmp_path)),CFG)['snapshot_id']
    assert before!=after and sum('forum' in q for q in c.calls)==2

def test_complete_resume_timeout_invalidates_completion_and_checkpoint_hash(tmp_path):
    c=Client();capture_corpus(CFG,tmp_path,client=c);c.fail=True
    result=capture_corpus(CFG,tmp_path,resume=True,client=c)
    assert result['capture_complete'] is False
    c.fail=False
    with pytest.raises(ValueError,match='checkpoint_config_mismatch'):
        capture_corpus(dict(CFG,venue_id='DIFFERENT'),tmp_path,resume=True,client=c)
    # Build a partial checkpoint with a successful first page then a failed second page.
    partial=dict(CFG,fetch_limits={'page_size':1})
    class Partial(Client):
        def get_notes(self,**kwargs):
            if 'forum' not in kwargs and kwargs['offset']==1:raise TimeoutError()
            return super().get_notes(**kwargs)
    capture_corpus(partial,tmp_path/'partial',client=Partial())
    (tmp_path/'partial'/'pages'/'0.json').write_text('[]')
    with pytest.raises(ValueError,match='checkpoint_hash_mismatch'):
        capture_corpus(partial,tmp_path/'partial',resume=True,client=c)

def test_stub_manifest_cannot_pass_production(tmp_path):
    dump(tmp_path/'manifest.json',{'schema_version':'1.0','snapshot_id':'s','is_fixture':False,'capture_complete':True})
    dump(tmp_path/'coverage.json',{'schema_version':'1.0','snapshot_id':'s','is_fixture':False,'capture_complete':True,'score_schema_verified':True,'discovered_count':0,'processed_count':0,'unprocessed_count':0})
    dump(tmp_path/'index'/'iclr2026.json',{'schema_version':'1.0','snapshot_id':'s','is_fixture':False,'papers':[]})
    dump(tmp_path/'rankings.json',{'schema_version':'1.0','snapshot_id':'s','is_fixture':False,'low_score_accepted':[],'high_score_rejected':[]})
    assert not validate_public(tmp_path,'production')['ok']

def test_export_preserves_valid_snapshot_when_incomplete_or_bad(tmp_path):
    out=tmp_path/'public'
    export_public(corpus(complete=True),ranks(),out)
    prior=(out/'manifest.json').read_bytes()
    with pytest.raises(ValueError,match='cannot_replace_valid'):
        export_public(corpus([]),ranks([]),out)
    assert (out/'manifest.json').read_bytes()==prior and (out/'papers'/'a.json').exists()
    with pytest.raises(ValueError):export_public(corpus([dict(paper(),forum_id='../bad')]),ranks(),out)
    assert (out/'manifest.json').read_bytes()==prior

def test_decision_status_conflict_and_mixed_scales():
    d={'id':'d','invitations':['V/Submission1/-/Decision'],'content':{'decision':{'value':'Accept'}}}
    c={'decision_labels':{'Accept':'Accept'},'withdrawn_venue_id':'Withdrawn'}
    assert resolve_decision([d],c,'Withdrawn')['decision']=='Conflict'
    p1=paper('a');p2=paper('b');p2['score_summary']['scale_id']='other'
    with pytest.raises(ValueError,match='mixed_rating_scales'):build_rankings({'papers':[p1,p2]})

def bundle_and_report():
    p=paper();p['reviews']=[{'review_id':'r','forum_id':'a','content_fields':{'summary':'hello'},'rating_value':2,'scale_id':'x','source_hash':'h'}]
    data=corpus([p]);bundle=build_evidence_bundle('a',data)
    report={'schema_version':'1.0','report_id':'rep','forum_id':'a','snapshot_id':'s','evidence_bundle_hash':bundle['bundle_hash'],
        'rubric_version':'1.0','model_provenance':'user_reported','generated_at':'2026-09-27T00:00:00+00:00',
        'claims':[{'claim_id':'c','claim_status':'supported','supporting_evidence_ids':['r:summary'],'counter_evidence_ids':[]}],
        'editorial_state':'evidence_checked'}
    return data,bundle,report

def test_evidence_exact_spans_hash_and_approval_binding():
    _,bundle,report=bundle_and_report()
    assert validate_report(report,bundle)['ok']
    altered=json.loads(json.dumps(bundle));altered['evidence'][0]['character_start']=1
    altered['bundle_hash']=__import__('reviewcase.report',fromlist=['bundle_digest']).bundle_digest(altered)
    report2=dict(report,evidence_bundle_hash=altered['bundle_hash'])
    assert any(e['code']=='quote_span_invalid' for e in validate_report(report2,altered)['errors'])
    record={'record_id':'external-1','actor':'Editor','approved_at':'2026-09-27T01:00:00+00:00','report_id':'rep','report_digest':report_digest(report),'bundle_hash':bundle['bundle_hash'],'rubric_version':'1.0'}
    approved=approve_report(report,'Editor',record)
    assert validate_report(approved,bundle)['ok']
    tampered=dict(approved,decision_explanation='New assertion')
    assert any(e['code']=='approval_binding_invalid' for e in validate_report(tampered,bundle)['errors'])
    with pytest.raises(ValueError):approve_report(dict(report,claims=[]),'Editor',record)

def test_approved_report_attached_allowlisted_and_reused(tmp_path):
    data,bundle,report=bundle_and_report()
    record={'record_id':'external-1','actor':'Editor','approved_at':'2026-09-27T01:00:00+00:00','report_id':'rep','report_digest':report_digest(report),'bundle_hash':bundle['bundle_hash'],'rubric_version':'1.0'}
    report['private_secret']='never publish';approved=approve_report(report,'Editor',record)
    reports=tmp_path/'reports'/'a';reports.mkdir(parents=True);dump(reports/'rep.json',approved)
    out=tmp_path/'public';export_public(data,ranks(),out,reports_dir=reports.parent)
    detail=json.loads((out/'papers'/'a.json').read_text())
    assert detail['report_state']=='published' and detail['report']['claims'][0]['claim_id']=='c'
    assert 'never publish' not in ''.join(p.read_text() for p in out.rglob('*.json'))
    data2=dict(data,snapshot_id='s2');data2['papers']=[dict(data['papers'][0],score_summary=dict(data['papers'][0]['score_summary'],snapshot_id='s2'))]
    export_public(data2,ranks(),tmp_path/'next',reports_dir=reports.parent)
    assert json.loads((tmp_path/'next'/'papers'/'a.json').read_text())['report_state']=='published'
    data2['papers'][0]['reviews'][0]['content_fields']['summary']='changed'
    export_public(data2,ranks(),tmp_path/'changed',reports_dir=reports.parent)
    assert json.loads((tmp_path/'changed'/'papers'/'a.json').read_text())['report_state']=='stale'

def test_redaction_durable_and_all_surfaces(tmp_path):
    data,bundle,report=bundle_and_report();out=tmp_path/'public';archive=tmp_path/'releases'/'R1'
    export_public(data,ranks(),out);export_public(data,ranks(),archive)
    reports=tmp_path/'reports'/'a';reports.mkdir(parents=True);dump(reports/'rep.json',report)
    deny=tmp_path/'denylist.json';redact_all(out,tmp_path/'releases',{'a'},reports.parent,deny)
    assert not reports.exists() and json.loads(deny.read_text())['forum_ids']==['a']
    for root in (out,archive):
        assert not (root/'papers'/'a.json').exists()
        assert validate_public(root,'fixture')['ok']
    export_public(data,ranks(),tmp_path/'new',denylist_path=deny)
    assert not (tmp_path/'new'/'papers'/'a.json').exists()

def test_release_dates_and_snapshot_binding(tmp_path):
    from reviewcase.release import release_snapshot,mark_published
    out=tmp_path/'public';export_public(corpus(complete=True),ranks(),out)
    metadata={'snapshot_id':'wrong','collection_started_at':'2026-09-27T00:00:00+00:00','collection_completed_at':'2026-09-27T01:00:00+00:00','generated_at':'2026-09-27T02:00:00+00:00','approval_record_id':'external-release'}
    with pytest.raises(ValueError,match='snapshot_mismatch'):release_snapshot(out,tmp_path/'releases','R1',metadata)
    metadata['snapshot_id']='s'
    release=release_snapshot(out,tmp_path/'releases','R1',metadata)
    assert release['published_at'] is None and release['next_review_due'] is None
    old=(tmp_path/'releases'/'R1'/'papers'/'a.json').read_bytes()
    published=mark_published(tmp_path/'releases'/'R1','2026-09-30T10:00:00+00:00')
    assert published['next_review_due'].startswith('2026-12-30')
    assert (tmp_path/'releases'/'R1'/'papers'/'a.json').read_bytes()==old
    with pytest.raises(FileExistsError):release_snapshot(out,tmp_path/'releases','R1',metadata)

def test_production_redaction_recounts_and_inventory(tmp_path):
    out=tmp_path/'public';export_public(corpus(complete=True),ranks(),out)
    assert validate_public(out,'production')['ok']
    redact_all(out,tmp_path/'releases',{'a'},tmp_path/'reports',tmp_path/'denylist.json')
    assert validate_public(out,'production')['ok']
    (out/'secret.txt').write_text('private')
    assert any(e['code']=='inventory_mismatch' for e in validate_public(out,'production')['errors'])

def test_forum_page_count_mismatch_and_page_size_checkpoint(tmp_path):
    from reviewcase.fetch import fetch_forum,FetchError
    class Bad:
        def get_notes(self,**kwargs):return {'notes':[submission()],'count':2}
    with pytest.raises(FetchError,match='forum_page_count_mismatch'):fetch_forum('a',Bad())
    class Partial(Client):
        def get_notes(self,**kwargs):
            if 'forum' not in kwargs and kwargs['offset']==1:raise TimeoutError()
            return super().get_notes(**kwargs)
    config=dict(CFG,fetch_limits={'page_size':1})
    capture_corpus(config,tmp_path,client=Partial())
    with pytest.raises(ValueError,match='checkpoint_config_mismatch'):
        capture_corpus(dict(CFG,fetch_limits={'page_size':2}),tmp_path,resume=True,client=Client())

def test_invalid_rating_issue_is_local_to_each_paper(tmp_path):
    first=submission()
    first['details']={'replies':[review('bad')]}
    first['details']['replies'][0]['content']['rating']['value']='3: Not in schema'
    second={'id':'b','forum':'b','content':{'title':{'value':'Second'}},'details':{'replies':[]}}
    dump(tmp_path/'pages'/'0.json',[first,second])
    capture={'directory':str(tmp_path),'capture_id':'c','pages':[{'offset':0}], 'capture_complete':True,'failure_count':0}
    result=normalize_capture(capture,CFG)
    by_id={p['forum_id']:p for p in result['papers']}
    assert by_id['a']['issues']==['invalid_rating_label']
    assert by_id['a']['score_summary']['valid_review_count']==0
    assert by_id['b']['issues']==[]
    assert result['issues']==[{'forum_id':'a','code':'invalid_rating_label','record_id':'r'}]

def test_full_capture_export_with_persistent_denial_is_production_valid(tmp_path):
    data=corpus(complete=True)
    deny=tmp_path/'denylist.json'
    dump(deny,{'schema_version':'1.0','forum_ids':['a'],'reason':'verified_removal'})
    out=tmp_path/'public'
    export_public(data,ranks(),out,denylist_path=deny)
    redactions=json.loads((out/'redactions.json').read_text())
    assert redactions=={'schema_version':'1.0','removed_forum_ids':['a'],'reason':'verified_removal'}
    assert not (out/'papers'/'a.json').exists()
    assert validate_public(out,'production')['ok']
