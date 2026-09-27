# 本次实际验证记录

日期：2026-09-27。所有测试均在当前云端工作目录执行。真实数据目标没有达成，不由测试替代。

| 命令 / 检查 | 实际结果 |
|---|---|
| `PYTHONPATH=pipeline python -m pytest pipeline/tests -q` | 27 passed，exit 0 |
| `python -m unittest discover -s scripts/tests -q` | 3 passed，exit 0 |
| `pnpm --dir apps/web test` | 8 passed，exit 0 |
| `pnpm --dir apps/web exec tsc --noEmit` | exit 0 |
| `pnpm --dir apps/web build` | 7 个静态页面与两个空索引，exit 0 |
| `pnpm --dir apps/web exec playwright test site.spec.ts` | 10 passed：1440/375px、无第三方请求、键盘、200% 字体、URL 筛选、禁用 JS |
| `node scripts/verify-ui-fixtures.mjs` | 10 passed：34 条虚构记录，双向排序、25 条分页、详情转义、stale 隐藏、历史隔离 |
| `BASE_PATH=/reviewcase/ … node scripts/verify-static.mjs` | 375/1440px 子路径链接及资源检查通过 |
| `python scripts/check-dist.py` | 通过；首屏 JS gzip 约 1.8KB，空索引 gzip 44 字节 |
| `python scripts/repository-guard.py` | 已跟踪内容检查通过；不能撤销已经公开的数据泄露 |
| `reviewcase validate-public --path data/public --mode fixture` | 结构校验通过；不表示数据为 fixture，也不表示生产通过 |
| `reviewcase validate-public --path data/public --mode production` | **预期 exit 1**：完整性、量表、provenance、capture inventory 四项未满足 |

## 浏览器环境

Playwright 自带浏览器下载在此环境取得了损坏下载包，未将该失败视为成功。实际使用从 npm 获取的 `@sparticuz/chromium@153.0.0` 所含 Chromium 153，通过 `CHROMIUM_PATH` 指定，运行同一 Playwright 测试。预览环境补充了官方 Noto CJK 字体以检查中文布局；网站本身使用系统字体，不请求外部字体。

## 有针对性的回归测试

不完整 manifest、错误 quote/source hash、重用错误审批、未核实评分、withdrawal/decision 冲突、刷新失败沿用 complete 标志、子评论变化、非法评分跨论文污染、下架后未来快照重新导出、首页子路径尾斜线、首次翻页与 stale 内容残留等问题均有对应检查或回归测试。

## 未执行

全会议采集、至少 10 篇 API/schema 样本对照、30 篇真实论文审计、原稿/PDF/图表专业核查、真实报告审批、GitHub Actions 实际运行、正式公网发布、未登录线上验收、线上回滚演练。源码级 workflow 与本地构建通过不能代替这些验收。
