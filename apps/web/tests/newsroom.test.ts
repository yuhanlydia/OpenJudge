import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {loadNewsroom, validateNewsroom} from '../src/lib/newsroom.ts';

const article = () => ({
  slug:'synthetic-case', forum_id:'SYNTHETIC', title:'Synthetic source title',
  headline:'测试文章', deck:'仅供工程验证的测试文章。', topic:'测试主题',
  category:'low-accepted', decision:'Accept (Poster)', ratings:[4,4,6], mean:14/3,
  archive_date:'2026-05-08', read_minutes:8, review_state:'draft_private',
  sections:[{heading:'公开事实',kind:'facts',paragraphs:['<script>unsafe()</script>'],sources:['forum']}],
  sources:[{id:'forum',label:'公开讨论页',url:'https://openreview.net/forum?id=SYNTHETIC'}],
});

test('default build does not read a private article file even when one is supplied',()=>{
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),'newsroom-private-'));
  const filename=path.join(directory,'articles.json');
  fs.writeFileSync(filename,'PRIVATE INVALID JSON MUST NOT BE READ');
  try {
    assert.deepEqual(loadNewsroom({NEWSROOM_FILE:filename}),[]);
    assert.deepEqual(loadNewsroom({NEWSROOM_FILE:filename,NEWSROOM_PREVIEW:'0'}),[]);
    assert.deepEqual(loadNewsroom({NEWSROOM_FILE:'/cannot/read',NEWSROOM_PREVIEW:'true'}),[]);
  } finally { fs.rmSync(directory,{recursive:true}); }
});
test('explicit preview loads private article content while preserving plain text',()=>{
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),'newsroom-preview-'));
  const filename=path.join(directory,'articles.json');
  fs.writeFileSync(filename,JSON.stringify([article()]));
  try { assert.equal(loadNewsroom({NEWSROOM_FILE:filename,NEWSROOM_PREVIEW:'1'})[0].sections[0].paragraphs[0],'<script>unsafe()</script>'); }
  finally { fs.rmSync(directory,{recursive:true}); }
});
test('preview with no source file has an honest empty state',()=>{
  assert.deepEqual(loadNewsroom({NEWSROOM_PREVIEW:'1'}),[]);
});
test('a section cannot cite a missing source',()=>{
  const item=article(); item.sections[0].sources=['missing'];
  assert.throws(()=>validateNewsroom([item]),/source.*missing|missing.*source/i);
});
test('article means must agree with the exact reviewer scores',()=>{
  const item=article(); item.mean=5;
  assert.throws(()=>validateNewsroom([item]),/mean/i);
});
test('unsafe source links and duplicate slugs are rejected',()=>{
  const item=article(); item.sources[0].url='javascript:alert(1)';
  assert.throws(()=>validateNewsroom([item]),/https/i);
  assert.throws(()=>validateNewsroom([article(),article()]),/duplicate.*slug/i);
});
test('the preview loader never converts an approval label into a publication claim',()=>{
  const item=article(); item.review_state='approved';
  assert.throws(()=>validateNewsroom([item]),/draft_private/i);
});

test('a substantive zero rating is valid and unsupported odd-number ratings are rejected',()=>{
  const item=article(); item.ratings=[6,0,0,6]; item.mean=3;
  assert.deepEqual(validateNewsroom([item])[0].ratings,[6,0,0,6]);
  for(const value of [1,5]){item.ratings=[value];item.mean=value;assert.throws(()=>validateNewsroom([item]),/ratings/i);}
});

const publicArticle=()=>({...article(),ratings:[4,4,4],mean:4,review_state:'commentary_public',
 desk:'low-accepted',desk_reason:'录取且归档均分较低。',
 brief:{gap:'旧方法缺口。',method:'方法内容。',results:'比较结果。',result_scope:'仅测试材料。',source_ids:['forum'],contribution:{kind:'method',module:'核心模块',why:'解决缺口。',evidence:'消融证据。',caveat:'尚未复现。'}},
 checks:{reviewers:[4,4,4].map((score,index)=>({note_id:`review${index}`,label:`R${index+1}`,score,included:true,claim:'具体意见',assessment:'unverifiable',analysis:'证据不足。',author_reply:'回复内容。',source_ids:['forum']})),ac:{claim:'决定理由',assessment:'value-judgment',analysis:'贡献标准。',source_ids:['forum']},authors:{claim:'作者主张',assessment:'unverifiable',analysis:'没有复现。',data_verdict:'不能认定编造。',source_ids:['forum']},takeaway:'分数不替代证据。'},
 publication:{basis:'owner_requested_publication',human_reviewed:false,date:'2026-09-28'},
 finding:{level:'record-conflict',target:'ac',summary:'测试中的记录冲突',rationale:'两条记录并不一致。',source_ids:['forum']},
 audit:{reviewed_at:'2026-09-28',claim:'争议原句',evidence:'可核对记录',alternative:'另一种合理解释',verdict:'局部记录冲突',impact:'不能确定决定影响',scope:'仅测试材料',source_ids:['forum']},
 sections:['facts','reviews','response','decision','analysis','lessons','limits'].map(kind=>({heading:kind,kind,paragraphs:['测试用公开评论'],sources:['forum']}))});

test('public mode loads explicit public commentary without declaring human approval',()=>{
 const directory=fs.mkdtempSync(path.join(os.tmpdir(),'newsroom-public-'));
 const filename=path.join(directory,'articles.json');fs.writeFileSync(filename,JSON.stringify([publicArticle()]));
 try {const rows=loadNewsroom({NEWSROOM_PUBLIC:'1',NEWSROOM_PUBLIC_FILE:filename});assert.equal(rows.length,1);assert.equal(rows[0].review_state,'commentary_public');assert.equal(rows[0].publication?.human_reviewed,false);}
 finally{fs.rmSync(directory,{recursive:true});}
});
test('public mode refuses private drafts and missing publication metadata',()=>{
 assert.throws(()=>validateNewsroom([article()],'public'),/commentary_public/);
 const item=publicArticle();delete (item as any).publication;
 assert.throws(()=>validateNewsroom([item],'public'),/publication/);
 assert.throws(()=>loadNewsroom({NEWSROOM_PUBLIC:'1',NEWSROOM_FILE:'/private-draft'}),/public source/i);
});
test('public findings must cite existing sources and retain limits',()=>{
 const item=publicArticle();item.finding.source_ids=['missing'];
 assert.throws(()=>validateNewsroom([item],'public'),/finding.*source/i);
 item.finding.source_ids=['forum'];item.sections=item.sections.filter(s=>s.kind!=='limits');
 assert.throws(()=>validateNewsroom([item],'public'),/sections/i);
});

test('public audit refuses missing counterevidence or untraceable citations',()=>{
 const item=publicArticle();
 item.audit.alternative=' ';assert.throws(()=>validateNewsroom([item],'public'),/audit alternative/i);
 item.audit.alternative='另一种合理解释';item.audit.source_ids=['missing'];
 assert.throws(()=>validateNewsroom([item],'public'),/audit source/i);
 item.audit.source_ids=['forum'];delete (item as any).audit;
 assert.throws(()=>validateNewsroom([item],'public'),/audit/i);
});

test('public reviewer assessments cannot silently drop or swap a score',()=>{
 const item=publicArticle();item.checks.reviewers[0].score=6;
 assert.throws(()=>validateNewsroom([item],'public'),/reviewer.*score/i);
 item.checks.reviewers[0].score=4;item.checks.reviewers.pop();
 assert.throws(()=>validateNewsroom([item],'public'),/reviewer.*score/i);
});

test('serious-error desk cannot turn an unestablished accusation into a finding',()=>{
 const item=publicArticle();item.desk='serious-errors';item.finding.level='not-established';
 assert.throws(()=>validateNewsroom([item],'public'),/serious.*finding/i);
});


test('current score desks require strict 4 and 7 thresholds but retain historical routes',()=>{
 const item:any=publicArticle();item.ratings=[4,4,6];item.mean=14/3;item.checks.reviewers[2].score=6;
 assert.throws(()=>validateNewsroom([item],'public'),/threshold/i);
 item.selection_status='historical';assert.equal(validateNewsroom([item],'public').length,1);
 item.selection_status='current';item.category='high-rejected';item.desk='high-rejected';item.decision='Reject';item.ratings=[6,6,8];item.mean=20/3;
 item.checks.reviewers.forEach((r:any,i:number)=>r.score=item.ratings[i]);assert.throws(()=>validateNewsroom([item],'public'),/threshold/i);
});
test('serious desk requires material core consequence and attributable evidence',()=>{
 const item:any=publicArticle();item.desk='serious-errors';
 assert.throws(()=>validateNewsroom([item],'public'),/serious.*basis/i);
 item.serious_basis={core_claim:'核心基线比较',consequence:'修正后领先变落后',source_ids:['forum']};
 assert.equal(validateNewsroom([item],'public').length,1);
 item.serious_basis.source_ids=['missing'];assert.throws(()=>validateNewsroom([item],'public'),/serious.*source/i);
});
test('reader-first records require full structured checks without duplicate legacy sections',()=>{
 const item:any=publicArticle();item.format='reader-first';item.sections=[];
 assert.equal(validateNewsroom([item],'public').length,1);
 delete item.checks.ac;assert.throws(()=>validateNewsroom([item],'public'),/check/i);
});
