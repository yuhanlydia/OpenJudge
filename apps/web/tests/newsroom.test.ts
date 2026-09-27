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
