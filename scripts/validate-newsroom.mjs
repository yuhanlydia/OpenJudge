import fs from 'node:fs';import path from 'node:path';import crypto from 'node:crypto';
import {validateNewsroom} from '../apps/web/src/lib/newsroom.ts';
const root=path.resolve(import.meta.dirname,'../data/newsroom');
const bytes=fs.readFileSync(path.join(root,'articles.json'));
const articles=validateNewsroom(JSON.parse(bytes),'public');
const release=JSON.parse(fs.readFileSync(path.join(root,'release.json'),'utf8'));
const sha=value=>crypto.createHash('sha256').update(value).digest('hex');
const check=(ok,message)=>{if(!ok)throw new Error(message);};
check(release.authorization?.basis==='owner_requested_publication','Missing publication authorization');
check(release.human_technical_review===false&&release.original_pdfs_verified===false,'Unsupported review claim');
check(sha(bytes)===release.articles_sha256,'Article release digest changed');
check(articles.length===release.cases.length&&new Set(articles.map(a=>a.forum_id)).size===articles.length,'Edition requires distinct cases matching source manifest');
check(new Set(release.cases.map(c=>c.forum_id)).size===articles.length,'Duplicate source manifest case');
check(release.review_audit?.case_count===articles.length&&release.review_audit?.human_technical_review===false,'Missing reviewer-method audit scope');
check(articles.every(a=>a.audit.reviewed_at===release.review_audit.date),'Audit dates do not match release');
const current=articles.filter(a=>a.selection_status!=='historical');
check(release.selection_policy.current_case_count===current.length,'Current article count mismatch');
check(release.selection_policy.historical_case_count===articles.length-current.length,'Historical article count mismatch');
check(release.selection_policy.low_accepted_max_mean===4&&release.selection_policy.high_rejected_min_mean===7,'Strict thresholds changed');
const coverageBytes=fs.readFileSync(path.join(root,'coverage.json'));
check(sha(coverageBytes)===release.coverage_sha256,'Coverage digest mismatch');
const coverage=JSON.parse(coverageBytes);
check(coverage.paper_count===19814&&coverage.note_count===284355&&coverage.notes_by_kind.Official_Review===75859,'Full corpus inventory mismatch');
check(coverage.all_manuscripts_read===false&&coverage.screening_is_semantic_review===false,'Screening cannot claim complete semantic review');
let noteCount=0;
for(const a of articles){
 const entry=release.cases.find(e=>e.forum_id===a.forum_id);check(entry,'Missing source manifest');
 const bytes=fs.readFileSync(path.join(root,'evidence',a.forum_id+'.json'));check(sha(bytes)===entry.sha256,'Evidence digest mismatch');
 const {paper,notes}=JSON.parse(bytes);noteCount+=notes.length;
 check(notes.length===entry.notes,'Per-case note inventory mismatch');
 check(new Set(notes.map(n=>n.id)).size===notes.length,'Duplicate note IDs');
 check(notes.every(n=>n.license==='CC BY 4.0'),'Source license missing');
 check(a.title===paper.title,'Original paper title must match source');
 check(!/Withdrawn|Desk_Rejected/.test(paper.venueid),'Excluded paper status');
 check(paper.decisions.length===1&&paper.decisions[0].decision===a.decision,'Decision mismatch');
 check(['low-accepted','accepted'].includes(a.category)?/^Accept/.test(a.decision):a.decision==='Reject','Category does not match decision');
 const reviews=notes.filter(n=>n.kind==='Official_Review'&&!entry.excluded_rating_note_ids.includes(n.id));
 const scores=reviews.map(n=>n.content.rating).sort((a,b)=>a-b);
 check(JSON.stringify(scores)===JSON.stringify([...a.ratings].sort((a,b)=>a-b)),'Raw rating mismatch');
 const checks=a.checks.reviewers;
 check(JSON.stringify(checks.map(r=>r.note_id))===JSON.stringify(paper.reviews),'Every official reviewer must be checked in source order');
 for(const r of checks){
  const note=notes.find(n=>n.id===r.note_id);
  check(note?.kind==='Official_Review'&&note.content.rating===r.score,'Reviewer check score or note mismatch');
  check(r.included===!entry.excluded_rating_note_ids.includes(r.note_id),'Reviewer score inclusion mismatch');
  check(r.source_ids.some(id=>new URL(a.sources.find(s=>s.id===id).url).searchParams.get('noteId')===r.note_id),'Reviewer check must cite its own review');
 }
 check(a.checks.ac.source_ids.some(id=>paper.meta_ids.includes(new URL(a.sources.find(s=>s.id===id).url).searchParams.get('noteId'))),'AC check must cite meta-review');
 for(const id of entry.excluded_rating_note_ids){check(a.score_note&&notes.some(n=>n.id===id&&n.content.rating===0),'Undocumented score exclusion');}
 const ids=new Set(notes.map(n=>n.id));
 for(const s of a.sources){const url=new URL(s.url);if(url.hostname==='openreview.net'&&url.pathname==='/forum'){check(url.searchParams.get('id')===a.forum_id,'Wrong forum citation');if(url.searchParams.has('noteId'))check(ids.has(url.searchParams.get('noteId')),'Unknown cited note');}}
}
check(noteCount===release.public_note_count,'Source note inventory changed');
console.log(JSON.stringify({ok:true,edition:release.edition,articles:articles.length,public_notes:noteCount,human_technical_review:false}));
