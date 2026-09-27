import {test,expect} from '@playwright/test';

test('news home retains the masthead, both archive entrances and a plain-language evidence warning',async({page})=>{
  await page.goto('/');
  await expect(page.getByRole('link',{name:'OpenJudge 首页',exact:true})).toBeVisible();
  await expect(page.getByRole('link',{name:'新闻首页',exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'低分录取',exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'高分拒稿',exact:true})).toBeVisible();
  await expect(page.locator('body')).toContainText('评分反差本身不构成错评证据');
});

test('preview article is static, attributed, readable at 200 percent and makes no third-party requests',async({browser})=>{
  test.skip(process.env.NEWSROOM_PREVIEW!=='1','Editorial articles are opt-in private preview content');
  const context=await browser.newContext({javaScriptEnabled:false,viewport:{width:375,height:812}});
  const page=await context.newPage();
  const outbound:string[]=[];
  const base=process.env.PREVIEW_URL||'http://127.0.0.1:4321';
  page.on('request',request=>{if(!request.url().startsWith(base))outbound.push(request.url());});
  await page.goto(base+'/');
  await expect(page.getByText('编辑预览 · AI 分析待复核',{exact:true})).toBeVisible();
  const href=await page.locator('[data-news-link]').first().getAttribute('href');
  expect(href).toBeTruthy();
  await page.goto(base+href);
  await expect(page.locator('h1')).toBeVisible();
  await expect(page.locator('[data-score-chart]')).toBeVisible();
  await expect(page.getByRole('heading',{name:'来源与核验',exact:true})).toBeVisible();
  await expect(page.locator('.article-body p').first()).toBeVisible();
  expect(await page.locator('a[href^="javascript:"]').count()).toBe(0);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.evaluate(()=>document.documentElement.style.fontSize='32px');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  expect(outbound).toEqual([]);
  await context.close();
});
