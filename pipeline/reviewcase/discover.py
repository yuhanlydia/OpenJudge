import hashlib,json
from .models import DiscoveryResult

def value(content,key,default=None):
    x=content.get(key,default)
    return x.get('value',default) if isinstance(x,dict) else x

def discover_venue(venue_id,client):
    group=client.get_group(venue_id); content=group['content']
    name=value(content,'submission_name')
    invitation=value(content,'submission_id') or f'{venue_id}/-/{name}'
    errors=[]; schema={}
    try:
        inv=client.get_invitation(invitation)
        schema=inv.get('edit',{}).get('note',{}).get('content',{})
    except Exception as e: errors.append(f'submission_schema_unavailable:{type(e).__name__}')
    cfg={'venue_id':venue_id,'submission_invitation':invitation,'submission_name':name,
         'review_name':value(content,'review_name'),'rating_field':value(content,'review_rating'),
         'confidence_field':value(content,'review_confidence'), 'decision_name':value(content,'decision_name'),
         'decision_field':value(content,'decision_field_name'),
         'accept_labels':value(content,'accept_decision_options',[]),
         'submission_venue_id':value(content,'submission_venue_id'),
         'withdrawn_venue_id':value(content,'withdrawn_venue_id'),
         'desk_rejected_venue_id':value(content,'desk_rejected_venue_id'),
         'rejected_venue_id':value(content,'rejected_venue_id'), 'submission_schema':schema}
    raw=json.dumps(cfg,sort_keys=True).encode()
    return DiscoveryResult(cfg,hashlib.sha256(raw).hexdigest(),validation_errors=errors)
