from decimal import Decimal

def score_percentile(mean,cohort):
    if not cohort: return None
    return (sum(x<mean for x in cohort)+Decimal('0.5')*sum(x==mean for x in cohort))/len(cohort)
def build_rankings(corpus,min_reviews=3,candidate_n=50):
    papers=corpus['papers']; groups={}
    if corpus.get('coverage',{}).get('score_schema_verified') is False:
        return {'low_score_accepted':[],'high_score_rejected':[],'candidate_ids':[],'ties':{},'eligible_count':0,'ranking_scope':'observed_sample'}
    scales={p['score_summary'].get('scale_id') for p in papers if p.get('score_summary',{}).get('mean') is not None}
    if len(scales)>1: raise ValueError('mixed_rating_scales')
    for decision in ('Accept','Reject'):
        eligible=[p for p in papers if p['decision']==decision and p['score_summary']['valid_review_count']>=min_reviews and p['score_summary']['mean'] is not None and p['score_summary'].get('scale_id') and not p.get('issues')]
        eligible.sort(key=lambda p:(Decimal(str(p['score_summary'].get('mean_exact') or p['score_summary']['mean']))*(1 if decision=='Accept' else -1),p['forum_id']))
        groups[decision]=eligible
    ordered={d:[p['forum_id'] for p in arr] for d,arr in groups.items()}
    candidates=[]; ties={}
    for d,arr in groups.items():
        cutoff=(Decimal(str(arr[min(candidate_n,len(arr))-1]['score_summary'].get('mean_exact') or arr[min(candidate_n,len(arr))-1]['score_summary']['mean'])) if arr else None)
        kept=[p['forum_id'] for p in arr if cutoff is not None and (Decimal(str(p['score_summary'].get('mean_exact') or p['score_summary']['mean']))<=cutoff if d=='Accept' else Decimal(str(p['score_summary'].get('mean_exact') or p['score_summary']['mean']))>=cutoff)]
        candidates+=kept; ties[d]=max(0,len(kept)-candidate_n)
    return {'low_score_accepted':ordered['Accept'],'high_score_rejected':ordered['Reject'],'candidate_ids':candidates,'ties':ties,
            'eligible_count':sum(map(len,groups.values())),'ranking_scope':corpus.get('coverage',{}).get('ranking_scope','observed_sample')}
