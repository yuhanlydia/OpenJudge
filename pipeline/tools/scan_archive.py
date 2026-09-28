#!/usr/bin/env python3
"""Reproduce a private, archive-wide ICLR 2026 score screening checkpoint.

This program does NOT review paper PDFs or certify review correctness/substance.
It preserves exact arithmetic and anonymous evidence, and excludes mechanically
identifiable review artifacts. A candidate is an evidence queue, not a finding.

Input JSONL notes must be contiguous by forum. We fail rather than silently
count a split forum twice. Peak note memory is a single forum. Authors/signatures
are used only to assign generic roles and are not exported.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

YEAR = 2026
CONF = 'ICLR.cc/2026/Conference'
ARCHIVE_SHA256 = '350071daf25ebf1aef854ee1d5dc3a81834e1c468917c82a4f78af5548de34fc'
OBSERVED_RATING_VALUES = {0, 2, 4, 6, 8, 10}
PROSE_FIELDS = ('summary', 'strengths', 'weaknesses', 'questions')
SERIOUS_IDS = {'fENEDBJAV3','uKrcWZ2V0F','Gba02UMvrG','aJd636PxP1',
               'dZKl7uc0XQ','ulTRUwrzt9','s9Ej5SQs5z','F7rUng23nw',
               'itUo64aUeK','kGEuZXaXU6','b1ITgc4J4M'}
KINDS = {'Official_Review', 'Official_Comment', 'Meta_Review', 'Decision'}
# Narrow patterns deliberately avoid 'review ... missing', which matches
# missing experiments, and 'no response', which is normal discussion behavior.
ARTIFACT_PATTERNS = {
 'blank_empty_review': r'\b(?:blank|empty|placeholder)\s+(?:official\s+)?reviews?\b',
 'duplicate_review': r'\bduplicat(?:e|ed)\s+(?:official\s+)?reviews?\b',
 'missing_review': r'\bmissing\s+(?:official\s+)?reviews?\b',
 'no_review': r'\bno\s+(?:official\s+)?reviews?\b(?=\s+(?:submitted|provided|available|from)\b|\s*(?:[\n.;]|$))',
 'review_not_provided': r'\breviews?\s+(?:(?:was|were|is|are|has been|have been)\s+)?not\s+(?:submitted|provided|available)\b',
 'reviewer_not_provided': r'\breviewer\s+[A-Za-z0-9]{4}\s*:\s*not\s+(?:provided|submitted)\b',
 'review_appears_missing': r'\breviews?\s+(?:[A-Za-z0-9]{4}\s*:\s*)?(?:appears?\s+|is\s+|was\s+)?(?:missing|incomplete)\b(?=\s*[.\n;]|$)',
 'unfinished_review': r'\b(?:didn[’\']t|did not)\s+(?:submit|finish)\s+(?:(?:the|a|their)\s+)?review\b',
 'no_substantive_review': r'\b(?:did|does)\s+not\s+provide\s+(?:a|an)\s+(?:substantive|meaningful)\s+review\b',
}
ARTIFACT_RES = {k: re.compile(v, re.I) for k,v in ARTIFACT_PATTERNS.items()}
# A strictly textual non-assessment flag, not a broad short-review penalty.
NONASSESSMENT = re.compile(r"(?:unable|cannot|can't|not (?:confident|qualified) enough)\s+(?:to\s+)?(?:assess|review|provide (?:a )?(?:technical|meaningful))|outside my (?:area of )?expertise|not an expert in this area|out of my expertise|cannot assess", re.I)
# Preserve exact keyword flags as pending audit rather than turn every mention
# (including negations and cleared accusations) into a disqualification.
POLICY_AUDIT = re.compile(r'\bdesk[ -]?reject(?:ed|ion)?\b|\b(?:duplicate|dual)[ -]submission\b', re.I)
PLACEHOLDER = re.compile(r'^(?:n\s*[/\\.]?\s*a\.?|none|no|nil|not applicable|tbd|to be (?:added|completed)|[-./?*\s]+)?$', re.I)


def canonical(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()


def sha_file(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''): h.update(block)
    return h.hexdigest()


def unwrap(content):
    return {k:(v.get('value') if isinstance(v,dict) and 'value' in v else v)
            for k,v in content.items()}


def text(value):
    if value is None: return ''
    if isinstance(value,str): return value
    if isinstance(value,(dict,list)): return json.dumps(value,ensure_ascii=False)
    return str(value)


def iso(ms):
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat() if isinstance(ms,(int,float)) else None


def json_write(path, obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')


def score(value):
    """Do not use truthiness: integer zero is a valid observed rating."""
    if value is None or isinstance(value,bool): return None
    raw=text(value).strip()
    m=re.fullmatch(r'(\d+(?:\.\d+)?)(?:\s*:.*)?',raw,re.S)
    if not m: return None
    try: number=Decimal(m[1])
    except InvalidOperation: return None
    if number not in OBSERVED_RATING_VALUES: return None
    return int(number)


def decision_for(paper, notes):
    venue=paper['venueid'] or ''
    if venue.endswith('/Withdrawn_Submission'): return 'Withdrawn',[]
    if venue.endswith('/Desk_Rejected_Submission'): return 'Desk Reject',[]
    values=[]
    for n in notes:
        if n['_kind']=='Decision':
            value=text(unwrap(n.get('content',{})).get('decision'))
            values.append('Accept' if value.startswith('Accept') else 'Reject' if value=='Reject' else value)
    unique=set(values)
    expected='Accept' if venue==CONF else 'Reject' if venue.endswith('/Rejected_Submission') else None
    issues=[]
    if len(unique)!=1: issues.append('missing_or_conflicting_decision')
    actual=next(iter(unique)) if len(unique)==1 else 'Unknown'
    if expected!=actual: issues.append('venue_decision_conflict')
    return actual,issues


def artifact_hits(notes):
    hits=[]; audit=[]
    for n in notes:
        if n['_kind']!='Meta_Review': continue
        for key,value in unwrap(n.get('content',{})).items():
            t=text(value)
            for reason,pat in ARTIFACT_RES.items():
                for match in pat.finditer(t):
                    tail=t[match.end():match.end()+45]
                    # Explicit absence of missing reviews is not an artifact.
                    if reason=='missing_review' and re.match(r'(?:\(s\))?\s*:\s*(?:none|not applicable)\b',tail,re.I): continue
                    hits.append({'reason':reason,'note_id':n['id'],'field':key,
                                 'start':match.start(),'end':match.end(),'quote':match.group(),
                                 'context':t[max(0,match.start()-60):match.end()+120]})
            for match in POLICY_AUDIT.finditer(t):
                audit.append({'reason':'policy_mention_needs_semantic_audit','note_id':n['id'],
                              'field':key,'start':match.start(),'end':match.end(),
                              'quote':match.group(),'context':t[max(0,match.start()-70):match.end()+160]})
    return hits,audit


def normalized_notes(notes):
    # Local ordinal aliases carry no cross-forum identity linkage.
    aliases={}
    for n in notes:
        if n['_kind']=='Official_Review':
            sig=tuple(n.get('signatures',[]))
            if sig and sig not in aliases: aliases[sig]=f'reviewer_{len(aliases)+1}'
    result=[]
    for n in notes:
        sig=' '.join(n.get('signatures',[]))
        role=('author' if re.search(r'/Authors?$',sig) else
              'program_chair' if '/Program_Chairs' in sig else
              'senior_area_chair' if '/Senior_Area_Chair' in sig else
              'area_chair' if '/Area_Chair' in sig else
              'reviewer' if '/Reviewer_' in sig or n['_kind']=='Official_Review' else 'unknown')
        item={'id':n['id'],'kind':n['_kind'],'replyto':n.get('replyto'),
              'role':role,'content':unwrap(n.get('content',{})),
              'date':iso(n.get('cdate')),'modified':iso(n.get('mdate')),
              'url':f"https://openreview.net/forum?id={n['_paper_forum']}&noteId={n['id']}",
              'license':n.get('license'),
              'source_hash':hashlib.sha256(canonical(n)).hexdigest()}
        alias=aliases.get(tuple(n.get('signatures',[])))
        if alias is not None: item['public_alias']=alias
        result.append(item)
    return result


def groups(path, stats):
    seen=set(); current=None; buf=[]
    with path.open() as f:
        for line_number,line in enumerate(f,1):
            n=json.loads(line); forum=n.get('_paper_forum') or n.get('forum')
            if not forum: raise ValueError(f'Missing forum line {line_number}')
            kind=n.get('_kind')
            if kind not in KINDS: raise ValueError(f'Unexpected kind {kind}')
            invitation='/-/'+kind
            if not any(i.endswith(invitation) for i in n.get('invitations',[])):
                raise ValueError(f'Kind/invitation mismatch: {n["id"]}')
            if n.get('forum')!=forum: raise ValueError('Forum mismatch')
            stats['notes']+=1; stats[kind]+=1
            if current is not None and current!=forum:
                yield current,buf
                seen.add(current);buf=[]
                if forum in seen: raise ValueError(f'Noncontiguous forum: {forum}')
            current=forum;buf.append(n)
        if current is not None: yield current,buf


def process(paper, notes):
    forum=paper['id']; decision,issues=decision_for(paper,notes)
    reviews=[n for n in notes if n['_kind']=='Official_Review']
    scores=[];invalid=[];blank=[];nonassessment=[];sigs=[]
    for n in reviews:
        c=unwrap(n.get('content',{}));s=score(c.get('rating'))
        if s is None:invalid.append({'review_id':n['id'],'raw':c.get('rating')})
        else:scores.append(s)
        prose=[text(c.get(k,'')) for k in PROSE_FIELDS]
        if all(PLACEHOLDER.fullmatch(v.strip()) for v in prose): blank.append(n['id'])
        # Only explicit inability plus very little technical body. Long ethics
        # concerns remain available, but do not turn placeholders into a review.
        if len(' '.join(prose))<350 and NONASSESSMENT.search(' '.join(prose)):
            nonassessment.append(n['id'])
        if n.get('signatures'): sigs.append(tuple(n['signatures']))
    repeated=Counter(n['id'] for n in notes)
    dup_notes=[id for id,count in repeated.items() if count>1]
    if dup_notes: issues.append('duplicate_note_id')
    dup_reviewer=len(sigs)!=len(set(sigs))
    if dup_reviewer:issues.append('duplicate_reviewer_notes')
    if invalid:issues.append('invalid_or_missing_rating')
    if len(scores)<3:issues.append('fewer_than_three_valid_reviews')
    if blank:issues.append('blank_placeholder_review')
    if nonassessment:issues.append('explicit_nonassessment_review')
    if any('everyone' not in n.get('readers',[]) for n in notes):issues.append('nonpublic_note')
    hits,audit=artifact_hits(notes)
    if hits:issues.append('ac_review_artifact')
    if decision=='Withdrawn':issues.insert(0,'withdrawn')
    elif decision=='Desk Reject':issues.insert(0,'desk_rejected')
    elif decision not in ('Accept','Reject'):issues.append('ineligible_decision')
    fraction=Fraction(sum(scores),len(scores)) if scores else None
    threshold=('low_score_accepted' if decision=='Accept' and fraction is not None and fraction<=4 else
               'high_score_rejected' if decision=='Reject' and fraction is not None and fraction>=7 else None)
    # Broad policy mentions remain flags: negations and cleared allegations
    # require semantic adjudication, not a generic regex exclusion.
    eligible=not issues
    classification=(f'{threshold}_pending_semantic_review' if eligible and threshold else
                    'excluded_score_threshold_match' if threshold else
                    'requested_serious_case_lead' if forum in SERIOUS_IDS else
                    'eligible_outside_score_threshold' if eligible else 'excluded')
    row={'forum_id':forum,'title':paper['title'],'decision':decision,
         'scores':scores,'review_count':len(reviews),'valid_review_count':len(scores),
         'nonplaceholder_review_count':len(reviews)-len(blank),
         'explicit_nonassessment_count':len(nonassessment),
         'mean':float(fraction) if fraction is not None else None,
         'mean_exact':f'{fraction.numerator}/{fraction.denominator}' if fraction is not None else None,
         'mean_display':f'{float(fraction):.2f}' if fraction is not None else None,
         'mechanically_eligible':eligible,'classification':classification,
         'threshold_group':threshold,'serious_case_lead':forum in SERIOUS_IDS,
         'issues':list(dict.fromkeys(issues)),'blank_review_ids':blank,
         'nonassessment_review_ids':nonassessment,'invalid_scores':invalid,
         'ac_artifact_hits':hits,'policy_audit_hits':audit,
         'source_url':f'https://openreview.net/forum?id={forum}',
         'semantic_review_status':'not_performed','paper_pdf_review_status':'not_performed',
         'editorial_state':'private_research_checkpoint'}
    return row


def run(args):
    args.out.mkdir(parents=True,exist_ok=True);evidence=args.out/'evidence';evidence.mkdir(exist_ok=True)
    papers={};venue_counts=Counter();paper_hash=hashlib.sha256()
    with args.papers.open('rb') as f:
        for line in f:
            paper_hash.update(line);n=json.loads(line);c=unwrap(n.get('content',{}));id=n['id']
            if id in papers:raise ValueError(f'Duplicate paper {id}')
            if 'everyone' not in n.get('readers',[]):raise ValueError(f'Nonpublic paper {id}')
            papers[id]={'id':id,**{k:c.get(k) for k in ('title','abstract','venue','venueid','pdf','keywords','primary_area')},
                        'number':n.get('number'),'license':n.get('license'),
                        'source_hash':hashlib.sha256(canonical(n)).hexdigest()}
            venue_counts[c.get('venueid')]+=1
    stats=Counter();seen=set();rows=[];evidence_ids=[];score_distribution=Counter();review_ids=set()
    for forum,notes in groups(args.reviews,stats):
        if forum not in papers:raise ValueError(f'Orphan note forum {forum}')
        seen.add(forum);paper=papers[forum];row=process(paper,notes);rows.append(row)
        for n in notes:
            if n['_kind']=='Official_Review':
                if n['id'] in review_ids:raise ValueError(f'Duplicate global review ID {n["id"]}')
                review_ids.add(n['id']);score_distribution[text(unwrap(n['content']).get('rating'))]+=1
        if row['threshold_group'] or forum in SERIOUS_IDS:
            pn={**paper,'scores':row['scores'],'invalid_scores':row['invalid_scores'],
                'decisions':[{'id':n['id'],'decision':unwrap(n['content']).get('decision')} for n in notes if n['_kind']=='Decision'],
                'meta_ids':[n['id'] for n in notes if n['_kind']=='Meta_Review'],
                'reviews':[n['id'] for n in notes if n['_kind']=='Official_Review'],
                'comments':sum(n['_kind']=='Official_Comment' for n in notes)}
            json_write(evidence/f'{forum}.json',{'paper':pn,'notes':normalized_notes(notes),
                'screening':row,'provenance':{'archive_sha256':ARCHIVE_SHA256,
                'source_capture_time':None,'source_snapshot_date_author_reported':'2026-05-08','score_stage':'current_archive_snapshot_unknown_review_stage',
                'pdf_version_role':'unknown','semantic_review_performed':False}})
            evidence_ids.append(forum)
    for forum in set(papers)-seen:rows.append(process(papers[forum],[]))
    eligible=[r for r in rows if r['mechanically_eligible']]
    sortkey=lambda r:(Fraction(r['mean_exact']),r['forum_id'])
    accept=sorted([r for r in eligible if r['decision']=='Accept'],key=sortkey)
    reject=sorted([r for r in eligible if r['decision']=='Reject'],key=lambda r:(-Fraction(r['mean_exact']),r['forum_id']))
    low=[r for r in accept if r['threshold_group']=='low_score_accepted']
    high=[r for r in reject if r['threshold_group']=='high_score_rejected']
    selected=low+high
    exclusions=Counter(r['issues'][0] for r in rows if r['issues'])
    all_issues=Counter(x for r in rows for x in r['issues'])
    checked=datetime.now(timezone.utc).isoformat()
    coverage={'schema_version':'private_screening_v1','generated_at':checked,
       'scope':'entire ICLR 2026 year within the supplied archive; not certified current OpenReview completeness',
       'source':{'archive_sha256':ARCHIVE_SHA256,'archive_source_url':args.source_url,
                 'source_capture_time':None,'source_snapshot_date_author_reported':'2026-05-08','papers_sha256':paper_hash.hexdigest(),'reviews_sha256':sha_file(args.reviews)},
       'paper_count':len(papers),'note_count':stats['notes'],'notes_by_kind':{k:stats[k] for k in sorted(KINDS)},
       'paper_venue_counts':dict(venue_counts),'papers_with_notes':len(seen),'papers_without_notes':len(papers)-len(seen),
       'observed_rating_distribution':dict(sorted(score_distribution.items(),key=lambda kv:int(kv[0]))),
       'rating_schema_status':'observed archive values only; official invitation schema not independently fetched',
       'zero_rating_is_valid':True,'eligible_count':len(eligible),'eligible_accept':len(accept),'eligible_reject':len(reject),
       'threshold_candidates':{'accepted_mean_at_most_4':len(low),'rejected_mean_at_least_7':len(high),'total':len(selected)},
       'exclusion_counts_primary_exclusive':dict(exclusions),'issue_counts_nonexclusive':dict(all_issues),
       'evidence_bundle_count':len(evidence_ids),'requested_serious_ids_missing':sorted(SERIOUS_IDS-set(evidence_ids)),
       'all_archive_records_parsed':True,'pdfs_reviewed':0,'papers_semantically_reviewed':0,'articles_created':0,
       'prior_checkpoint_for_comparison_only':{'eligible':13673,'accept':5336,'reject':8337,'low':329,'high':1},
       'limitations':[
          'Mechanical screening does not certify substantive reviews, review correctness, paper correctness, or serious misconduct.',
          'Known artifact patterns are documented heuristics; semantic false negatives remain possible.',
          'Desk/duplicate-submission meta-review mentions are audit flags, not automatically exclusions; they require semantic adjudication before case selection.',
          'Archival score snapshot is not assigned to an original/rebuttal/final stage without version evidence.',
          'Full current website coverage, original paper versions, and API invitation schema were not independently verified.',
          'This is a private recovery checkpoint; no publication approval or site release is implied.']}
    json_write(args.out/'coverage.json',coverage)
    json_write(args.out/'candidate_metadata.json',{'status':'private_screening_candidates_not_completed_cases','selection':{'low':'Accept with exact mean <= 4','high':'Reject with exact mean >= 7','minimum_valid_reviews':3},'low_score_accepted':low,'high_score_rejected':high,'serious_case_leads':[r for r in sorted(rows,key=lambda r:r['forum_id']) if r['serious_case_lead']]})
    json_write(args.out/'strict_rankings.json',{'low_score_accepted':accept,'high_score_rejected':reject})
    json_write(args.out/'exclusion_audit.json',sorted([r for r in rows if r['issues']],key=lambda r:r['forum_id']))
    json_write(args.out/'evidence_index.json',{'forum_ids':sorted(evidence_ids),'count':len(evidence_ids)})
    json_write(args.out/'methodology.json',{'prose_fields':PROSE_FIELDS,'placeholder_regex':PLACEHOLDER.pattern,
       'nonassessment_regex':NONASSESSMENT.pattern,'nonassessment_max_prose_characters':350,
       'ac_artifact_patterns':ARTIFACT_PATTERNS,'policy_audit_regex':POLICY_AUDIT.pattern,
       'mean':'Fraction(sum(valid official ratings), count); original rating 0 is included',
       'sort':'accept: exact mean asc, forum_id asc; reject: exact mean desc, forum_id asc',
       'privacy':'No authors, profiles, emails, writer/reader lists, or signature identifiers exported. Generic roles and forum-local reviewer ordinal aliases only.'})
    json_write(args.out/'manifest.json',{'generated_at':checked,'files':{str(p.relative_to(args.out)):sha_file(p) for p in sorted(args.out.rglob('*')) if p.is_file() and p.name!='manifest.json'}})
    print(json.dumps({k:coverage[k] for k in ('paper_count','note_count','eligible_count','eligible_accept','eligible_reject','threshold_candidates','exclusion_counts_primary_exclusive','evidence_bundle_count')},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--papers',type=Path,required=True)
    parser.add_argument('--reviews',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--source-url',default=None)
    run(parser.parse_args())
