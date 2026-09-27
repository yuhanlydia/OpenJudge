import {test,expect} from '@playwright/test';
test('public edition exposes ten complete attributed articles and working internal navigation',async({page})=>{
 test.skip(process.env.NEWSROOM_PUBLIC!=='1','Public edition build required');
 const outbound:string[]=[];const base=process.env.PREVIEW_URL||'http://127.0.0.1:4321';
 page.on('request',r=>{if(!r.url().startsWith(base))outbound.push(r.url());});
 await page.goto('/');
 const links=await page.locator('[data-news-link]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('href')!));
 expect(new Set(links).size).toBe(10);
 await expect(page.locator('body')).not.toContainText('编辑预览');
 for(const route of links){
  await page.goto(route);await expect(page.locator('h1')).toBeVisible();
  await expect(page.locator('.finding-box')).toBeVisible();
  expect(await page.locator('.article-section').count()).toBe(7);
  await expect(page.locator('.article-sources')).toContainText('来源与核验');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.evaluate(()=>document.documentElement.style.fontSize='32px');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.evaluate(()=>document.documentElement.style.fontSize='');
  const internal=await page.locator('a[href^="/"]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('href')!));
  for(const href of new Set(internal))expect((await page.request.get(href)).ok(),href).toBe(true);
 }
 await page.goto('/methodology/');await expect(page.locator('h1')).toContainText('证据');
 await page.goto('/data-status/');await expect(page.locator('body')).toContainText('176');
 expect(outbound).toEqual([]);
});
test('public commentary remains readable without JavaScript',async({browser})=>{
 test.skip(process.env.NEWSROOM_PUBLIC!=='1','Public edition build required');
 const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:375,height:812}});
 const page=await context.newPage();const base=process.env.PREVIEW_URL||'http://127.0.0.1:4321';
 await page.goto(base);await page.locator('[data-news-link]').first().click();
 await expect(page.locator('.finding-box')).toBeVisible();await expect(page.locator('.section-limits')).toBeVisible();
 expect(await page.locator('.article-section').count()).toBe(7);await context.close();
});
