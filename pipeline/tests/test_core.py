import json
from decimal import Decimal
from pathlib import Path
import pytest
from reviewcase.config import load_config
from reviewcase.discover import discover_venue
from reviewcase.fetch import fetch_forum, RetryingClient
from reviewcase.score import parse_rating, summarize, resolve_decision
from reviewcase.rank import build_rankings, score_percentile
from reviewcase.export import export_public
from reviewcase.validate import validate_public
from reviewcase.report import validate_report, mark_stale
from helpers import paper,corpus,ranks


def test_config_public_only_and_no_paid_api(tmp_path):
    p=tmp_path/'c.json'; p.write_text(json.dumps({'public_only':False,'api_enabled':True,'api_budget_usd':1}))
    with pytest.raises(ValueError): load_config(p)


def test_discover_uses_submission_name():
    class C:
        def get_group(self, id): return {'content':{'submission_name':{'value':'Paper'},'submission_id':{'value':'x/-/Paper'}}}
        def get_invitation(self,id): return {'id':id,'edit':{'note':{'content':{}}}}
    assert discover_venue('x',C()).discovered_config['submission_invitation']=='x/-/Paper'


def test_rating_is_not_confidence_and_missing_not_zero():
    schema={'scale_id':'x','allowed_values':['4','6'],'field_name':'rating'}
    assert parse_rating({'confidence':{'value':4}},schema) is None
    s=summarize([Decimal(4),Decimal(6),None],schema,'s')
    assert s['mean']==5 and s['valid_review_count']==2 and s['missing_rating_count']==1
    assert parse_rating({'rating':{'value':'8: High'}},schema) is None


def test_decision_comment_not_decision_and_withdrawn():
    cfg={'decision_labels':{'Accept (Poster)':'Accept','Reject':'Reject'}}
    assert resolve_decision([{'invitations':['x/-/Official_Comment'],'content':{'comment':{'value':'reject'}}}],cfg)['decision']=='Unknown'
    assert resolve_decision([{'invitations':['x/-/Decision'],'content':{'decision':{'value':'Reject'}}}],cfg)['decision']=='Reject'
    assert resolve_decision([],dict(cfg,withdrawn_venue_id='Withdrawn'),venueid='Withdrawn')['decision']=='Withdrawn'


def test_rank_direction_ties_and_midrank():
    def p(id,d,s): return {'forum_id':id,'decision':d,'score_summary':{'valid_review_count':3,'mean':s,'scale_id':'x','scores':[s]*3},'issues':[]}
    papers=[p('a','Accept',5),p('b','Accept',3),p('c','Reject',7),p('d','Reject',4)]
    r=build_rankings({'papers':papers},candidate_n=1)
    assert r['low_score_accepted']==['b','a'] and r['high_score_rejected']==['c','d']
    assert score_percentile(Decimal(5),[Decimal(5),Decimal(5)])==Decimal('0.5')


def test_production_rejects_fixture_and_incomplete_capture(tmp_path):
    (tmp_path/'manifest.json').write_text(json.dumps({'schema_version':'1.0','is_fixture':True,'capture_complete':False}))
    assert not validate_public(tmp_path,'production')['ok']


def test_export_allowlist(tmp_path):
    p=paper('abc');p['authors']=['Secret'];p['email']='secret@example.com'
    p['reviews']=[{'review_id':'r','forum_id':'abc','rating_value':None,'scale_id':'x','source_hash':'h','content_fields':{},'email':'secret@example.com'}]
    export_public(corpus([p]), ranks(['abc']),tmp_path/'public')
    txt=''.join(x.read_text() for x in (tmp_path/'public').rglob('*.json'))
    assert 'secret@example.com' not in txt and 'Secret' not in txt


def test_report_rejects_missing_evidence_and_stale():
    report={'evidence_bundle_hash':'old','claims':[{'supporting_evidence_ids':['absent']}]}
    bundle={'bundle_hash':'old','evidence':[]}
    assert not validate_report(report,bundle)['ok']
    assert mark_stale(report,'new')['editorial_state']=='stale'
