import {test,expect} from '@playwright/test';
import fs from 'node:fs';
const articles=JSON.parse(fs.readFileSync(new URL('../../../data/newsroom/articles.json',import.meta.url),'utf8'));
const release=JSON.parse(fs.readFileSync(new URL('../../../data/newsroom/release.json',import.meta.url),'utf8'));
test('public edition exposes every complete attributed article and working internal navigation',async({page},testInfo)=>{
 test.setTimeout(240000);
 test.skip(process.env.NEWSROOM_PUBLIC!=='1','Public edition build required');
 const outbound:string[]=[];const base=process.env.PREVIEW_URL||'http://127.0.0.1:4321';
 page.on('request',r=>{if(!r.url().startsWith(base))outbound.push(r.url());});
 await page.goto('/');
 const links=await page.locator('[data-news-link]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('href')!));
 const current=articles.filter((a:any)=>a.selection_status!=='historical');
 expect(new Set(links).size).toBe(current.length);
 expect(links.length).toBe(current.length);
 expect([...links].sort()).toEqual(current.map((a:any)=>`/news/${a.slug}/`).sort());
 expect(await page.locator('[data-historical-link]').count()).toBe(articles.length-current.length);
 expect(await page.locator('[data-desk]').count()).toBe(3);
 await expect(page.locator('body')).not.toContainText('编辑预览');
 for(const summary of await page.locator('.desk-more>summary').all())await summary.click();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.evaluate(()=>document.documentElement.style.fontSize='32px');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.evaluate(()=>document.documentElement.style.fontSize='');
 if(process.env.CAPTURE_UI==='1')await page.screenshot({path:`../../.cache/v3-home-${testInfo.project.name}.png`,fullPage:true});
 const checkedInternal=new Set<string>();
 for(const article of articles){
  const route=`/news/${article.slug}/`;
  await page.goto(route);await expect(page.locator('h1')).toBeVisible();
  await expect(page.locator('.finding-box')).toBeVisible();
  expect(await page.locator('.paper-paragraph').count()).toBe(3);
  await expect(page.locator('.contribution-focus')).toBeVisible();
  await expect(page.locator('.author-check .data-verdict')).toBeVisible();
  if(process.env.CAPTURE_UI==='1'&&route===links[0])await page.screenshot({path:`../../.cache/v3-article-${testInfo.project.name}.png`});
  expect(await page.locator('.reviewer-check').count()).toBe(article.checks.reviewers.length);
  expect(await page.evaluate(()=>{
   const order=['.article-result','.paper-story','.reviewer-checks','.ac-check','.author-check','.takeaway'];
   return order.slice(1).every((s,i)=>Boolean(document.querySelector(order[i])!.compareDocumentPosition(document.querySelector(s)!)&Node.DOCUMENT_POSITION_FOLLOWING));
  })).toBe(true);
  await page.locator('.full-analysis>summary').click();
  await expect(page.locator('.review-audit')).toBeVisible();
  expect(await page.locator('.audit-row').count()).toBe(5);
  await expect(page.locator('.audit-scope')).not.toBeEmpty();
  expect(await page.locator('.article-section').count()).toBe(article.sections.length);
  await expect(page.locator('.article-sources')).toContainText('来源与核验');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.evaluate(()=>document.documentElement.style.fontSize='32px');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.evaluate(()=>document.documentElement.style.fontSize='');
  const internal=await page.locator('a[href^="/"]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('href')!));
  for(const href of new Set(internal)){if(!checkedInternal.has(href)){expect((await page.request.get(href)).ok(),href).toBe(true);checkedInternal.add(href);}}
 }
 await page.goto('/methodology/');await expect(page.locator('h1')).toContainText('证据');
 await page.goto('/data-status/');await expect(page.locator('body')).toContainText(String(release.public_note_count));
 expect(outbound).toEqual([]);
});
test('public commentary remains readable without JavaScript',async({browser})=>{
 test.skip(process.env.NEWSROOM_PUBLIC!=='1','Public edition build required');
 const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:375,height:812}});
 const page=await context.newPage();const base=process.env.PREVIEW_URL||'http://127.0.0.1:4321';
 await page.goto(base);
 const more=page.locator('.desk-more').first();
 if(await more.count()){await more.locator('summary').click();await more.locator('[data-news-link]').last().click();}
 else await page.locator('[data-news-link]').first().click();
 await expect(page.locator('.paper-story')).toBeVisible();
 await expect(page.locator('.reviewer-check').first()).toBeVisible();
 await page.locator('.full-analysis>summary').click();
 await expect(page.locator('.finding-box')).toBeVisible();await expect(page.locator('.audit-scope')).toBeVisible();
 await context.close();
});
