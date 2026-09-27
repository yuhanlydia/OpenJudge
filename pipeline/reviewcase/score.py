import statistics
from decimal import Decimal,InvalidOperation
from .discover import value

def parse_rating(raw,schema):
    if not schema: return None
    text=value(raw.get('content',raw),schema['field_name'])
    if text is None: return None
    candidate=str(text).split(':',1)[0].strip()
    allowed={str(x).split(':',1)[0].strip() for x in schema['allowed_values']}
    if candidate not in allowed: return None
    try: return Decimal(candidate)
    except InvalidOperation: return None

def summarize(values,schema,snapshot_id):
    valid=[Decimal(str(v)) for v in values if v is not None]
    def number(v): return float(v) if v is not None else None
    return {'valid_review_count':len(valid),'missing_rating_count':len(values)-len(valid),
            'scores':[number(v) for v in valid], 'mean':number(sum(valid)/len(valid)) if valid else None,
            'mean_exact':str(sum(valid)/len(valid)) if valid else None,
            'median':number(statistics.median(valid)) if valid else None,
            'min':number(min(valid)) if valid else None,'max':number(max(valid)) if valid else None,
            'std_population':number(Decimal(str(statistics.pstdev(valid)))) if valid else None,
            'scale_id':schema.get('scale_id') if schema else None,'score_stage':'observed_public_snapshot','snapshot_id':snapshot_id}

def resolve_decision(notes,config,venueid=None):
    name=config.get('decision_name','Decision'); field=config.get('decision_field','decision')
    labels=config.get('decision_labels',{}); decisions=[]
    for n in notes:
        invitations=n.get('invitations') or [n.get('invitation','')]
        if any(str(x).endswith('/-/'+name) for x in invitations):
            decisions.append((labels.get(value(n.get('content',{}),field),'Unknown'),n.get('id')))
    statuses=[(config.get('withdrawn_venue_id'),'Withdrawn'),(config.get('desk_rejected_venue_id'),'Desk Reject'),(config.get('rejected_venue_id'),'Reject')]
    status=next((d for id,d in statuses if id and id==venueid),None)
    distinct={d for d,_ in decisions}
    if len(distinct)>1 or (status and distinct and distinct!={status}):
        return {'decision':'Conflict','source_kind':'conflict','source_id':None,'conflicts':[i for _,i in decisions]}
    if decisions:
        d,i=decisions[-1];return {'decision':d,'source_kind':'decision_note','source_id':i,'conflicts':[]}
    if status:return {'decision':status,'source_kind':'status_only','source_id':None,'conflicts':[]}
    return {'decision':'Unknown','source_kind':'unknown','source_id':None,'conflicts':[]}
