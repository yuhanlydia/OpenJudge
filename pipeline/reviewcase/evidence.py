import hashlib
from .capture import digest
from .report import bundle_digest

def build_evidence_bundle(forum_id,corpus,source_dir=None):
    paper=next(p for p in corpus['papers'] if p['forum_id']==forum_id)
    sources=[]
    for record,kind,id_field in [(r,'review','review_id') for r in paper.get('reviews',[])]+[(r,'discussion','note_id') for r in paper.get('discussion',[])]:
        for field,text in record.get('content_fields',{}).items():
            if isinstance(text,str): sources.append({'evidence_id':f"{record[id_field]}:{field}",'source_type':kind,
                'note_id':record[id_field],'source_hash':hashlib.sha256(text.encode()).hexdigest(),'paper_version_id':None,
                'character_start':0,'character_end':len(text),'quote':text,'source_text':text,
                'source_url':paper['source_url']})
    coverage={'original_available':any(v['version_role']=='original_submission' and v.get('public_available') for v in paper.get('paper_versions',[]))}
    bundle={'bundle_id':digest({'forum_id':forum_id,'sources':sources})[:20],'forum_id':forum_id,
            'snapshot_id':corpus['snapshot_id'],'rubric_version':'1.0',
            'versioned_sources':paper.get('paper_versions',[]),'coverage':coverage,'evidence':sources}
    bundle['bundle_hash']=bundle_digest(bundle)
    return bundle
