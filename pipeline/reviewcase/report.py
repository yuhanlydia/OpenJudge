"""Content-bound report validation; approval is supplied by an external editor."""
import hashlib,json
from pathlib import Path
from jsonschema import Draft202012Validator
from .capture import digest

REPORT_FIELDS=('schema_version','report_id','forum_id','snapshot_id','evidence_bundle_hash','rubric_version',
 'model_requested','model_reported','model_provenance','api_verification_record','prompt_version','generated_at','claims',
 'writing_diagnosis','decision_explanation','limitations','editorial_state','reviewer_of_report',
 'approved_at','approval_record_id','approval_binding','rewrites','fact_ids','reused_from_snapshot')
APPROVAL_FIELDS={'editorial_state','reviewer_of_report','approved_at','approval_record_id','approval_binding','reused_from_snapshot'}
CLAIM_FIELDS=('claim_id','review_id','quote','claim_type','claim_status','severity','supporting_evidence_ids','counter_evidence_ids','explanation','limitations','human_reviewed','original_submission_claim')
def public_report(report):
    clean={k:report[k] for k in REPORT_FIELDS if k in report}
    clean['claims']=[{k:c[k] for k in CLAIM_FIELDS if k in c} for c in report.get('claims',[])]
    if 'rewrites' in clean: clean['rewrites']=[{k:r[k] for k in ('text','fact_ids') if k in r} for r in clean['rewrites']]
    if isinstance(clean.get('writing_diagnosis'),dict): clean['writing_diagnosis']={k:v for k,v in clean['writing_diagnosis'].items() if k in ('paper','review','limitations')}
    return clean
def report_digest(report):
    clean=public_report(report)
    return digest({k:v for k,v in clean.items() if k not in APPROVAL_FIELDS})
def bundle_digest(bundle):
    return digest({k:bundle[k] for k in ('forum_id','versioned_sources','coverage','evidence','rubric_version') if k in bundle})
def schema_errors(obj,name):
    schema=json.loads((Path(__file__).resolve().parents[2]/'schemas'/f'{name}.schema.json').read_text())
    return list(Draft202012Validator(schema).iter_errors(obj))
def validate_report(report,bundle):
    errors=[]
    def add(code,id=None): errors.append({'code':code,'record_id':id})
    for e in schema_errors(report,'analysis-report'): add('report_schema:'+e.validator)
    for e in schema_errors(bundle,'evidence-bundle'): add('bundle_schema:'+e.validator)
    if bundle.get('bundle_hash')!=bundle_digest(bundle): add('bundle_hash_invalid')
    if report.get('evidence_bundle_hash')!=bundle.get('bundle_hash'): add('bundle_mismatch')
    if report.get('forum_id')!=bundle.get('forum_id'): add('forum_mismatch')
    if report.get('rubric_version')!=bundle.get('rubric_version'): add('rubric_mismatch')
    evidence={e.get('evidence_id'):e for e in bundle.get('evidence',[])}
    for e in evidence.values():
        text=e.get('source_text')
        start=e.get('character_start');end=e.get('character_end')
        if not isinstance(text,str) or not isinstance(start,int) or not isinstance(end,int) or start<0 or end<=start or end>len(text) or text[start:end]!=e.get('quote'):
            add('quote_span_invalid',e.get('evidence_id'))
        if not isinstance(text,str) or hashlib.sha256(text.encode()).hexdigest()!=e.get('source_hash'):
            add('source_hash_invalid',e.get('evidence_id'))
    for claim in report.get('claims',[]):
        cid=claim.get('claim_id');refs=claim.get('supporting_evidence_ids',[])+claim.get('counter_evidence_ids',[])
        if not refs: add('claim_without_evidence',cid)
        for id in refs:
            if id not in evidence: add('missing_evidence_id',cid)
        if claim.get('claim_status')=='contradicted' and claim.get('original_submission_claim') and not bundle.get('coverage',{}).get('original_available'):
            add('original_unavailable',cid)
    for rewrite in report.get('rewrites',[]):
        if set(rewrite.get('fact_ids',[]))-set(report.get('fact_ids',[])): add('rewrite_new_fact')
    if report.get('model_provenance')=='api_verified' and not report.get('api_verification_record'): add('model_provenance_unverified')
    if report.get('editorial_state') in ('approved','published'):
        binding=report.get('approval_binding',{})
        if not isinstance(binding,dict) or any(binding.get(k)!=v for k,v in {'record_id':report.get('approval_record_id'),'report_id':report.get('report_id'),'report_digest':report_digest(report),'bundle_hash':report.get('evidence_bundle_hash'),'rubric_version':report.get('rubric_version'),'actor':report.get('reviewer_of_report'),'approved_at':report.get('approved_at')}.items()): add('approval_binding_invalid')
    return {'ok':not errors,'errors':errors,'warnings':[]}
def mark_stale(report,current_bundle_hash,current_rubric=None):
    return {**report,'editorial_state':'stale'} if report.get('evidence_bundle_hash')!=current_bundle_hash or (current_rubric and report.get('rubric_version')!=current_rubric) else report

def approve_report(report,actor,approval_record):
    required={'record_id','actor','approved_at','report_id','report_digest','bundle_hash','rubric_version'}
    if not actor or not isinstance(approval_record,dict) or not required<=approval_record.keys() or approval_record['actor']!=actor or approval_record['report_id']!=report.get('report_id') or approval_record['report_digest']!=report_digest(report) or approval_record['bundle_hash']!=report.get('evidence_bundle_hash') or approval_record['rubric_version']!=report.get('rubric_version'):
        raise ValueError('external approval must bind exact report, bundle, rubric and editor')
    return {**public_report(report),'editorial_state':'approved','reviewer_of_report':actor,'approved_at':approval_record['approved_at'],'approval_record_id':approval_record['record_id'],'approval_binding':{k:approval_record[k] for k in required}}
