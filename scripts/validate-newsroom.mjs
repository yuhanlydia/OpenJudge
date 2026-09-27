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
check(articles.length===10&&new Set(articles.map(a=>a.forum_id)).size===10,'Edition requires ten distinct cases');
check(articles.filter(a=>a.category==='low-accepted').length===5,'Edition requires five accepted and five rejected cases');
check(release.review_audit?.case_count===10&&release.review_audit?.human_technical_review===false,'Missing reviewer-method audit scope');
check(articles.every(a=>a.audit.reviewed_at===release.review_audit.date),'Audit dates do not match release');
let noteCount=0;
for(const a of articles){
 const entry=release.cases.find(e=>e.forum_id===a.forum_id);check(entry,'Missing source manifest');
 const bytes=fs.readFileSync(path.join(root,'evidence',a.forum_id+'.json'));check(sha(bytes)===entry.sha256,'Evidence digest mismatch');
 const {paper,notes}=JSON.parse(bytes);noteCount+=notes.length;
 check(a.title===paper.title,'Original paper title must match source');
 check(!/Withdrawn|Desk_Rejected/.test(paper.venueid),'Excluded paper status');
 check(paper.decisions.length===1&&paper.decisions[0].decision===a.decision,'Decision mismatch');
 check(a.category==='low-accepted'?/Accept/.test(a.decision):a.decision==='Reject','Category does not match decision');
 const reviews=notes.filter(n=>n.kind==='Official_Review'&&!entry.excluded_rating_note_ids.includes(n.id));
 const scores=reviews.map(n=>n.content.rating).sort((a,b)=>a-b);
 check(JSON.stringify(scores)===JSON.stringify([...a.ratings].sort((a,b)=>a-b)),'Raw rating mismatch');
 for(const id of entry.excluded_rating_note_ids){check(a.score_note&&notes.some(n=>n.id===id&&n.content.rating===0),'Undocumented score exclusion');}
 const ids=new Set(notes.map(n=>n.id));
 for(const s of a.sources){const url=new URL(s.url);if(url.hostname==='openreview.net'&&url.pathname==='/forum'){check(url.searchParams.get('id')===a.forum_id,'Wrong forum citation');if(url.searchParams.has('noteId'))check(ids.has(url.searchParams.get('noteId')),'Unknown cited note');}}
}
check(noteCount===176,'Source note inventory changed');
console.log(JSON.stringify({ok:true,edition:release.edition,articles:articles.length,public_notes:noteCount,human_technical_review:false}));
