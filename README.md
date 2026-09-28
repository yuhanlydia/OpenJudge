# OpenJudge · ICLR 2026 公开评审观察

网站：[openjudge.longyunbo218.chatgpt.site](https://openjudge.longyunbo218.chatgpt.site)

公开新闻版按三个严格板块组织：严重矛盾和错误、均分≤4的低分录取、均分≥7的高分拒稿。每篇先列评分与结果，再给论文三段式、一个主要贡献、逐位评审、AC及作者回复核查。当前篇数和来源摘要以 `data/newsroom/release.json` 为准，五篇旧版文章单列历史区。

已对2026-05-08公开存档中的19,814篇论文、284,355条记录完成机械扫描。初筛产生329个低分录取候选和1个高分拒稿候选；候选数不等于严重错误数，也不表示通读全部论文。每篇分析披露实际阅读范围、版本与未验证事项。方法见 [PUBLIC_NEWSROOM.md](docs/PUBLIC_NEWSROOM.md)、[REVIEWER_METHODS.md](docs/REVIEWER_METHODS.md)。

站点是 Astro + TypeScript 纯静态页面，以 Sites 公开托管，无付费模型API、数据库或定时抓取。原API全会议榜单管线保留在仓库中，但未完成生产验收，不包含在新闻版部署产物里。早期 `IMPLEMENTATION_STATUS`、`API_DISCOVERY`、`DATA_AUDIT` 记录的是那条管线的历史状态，不代表新闻版没有真实案例或尚未上线。

## 本地预览公开版

```bash
pnpm install --frozen-lockfile
node scripts/build-newsroom.mjs
python -m http.server 8000 --directory dist
```

访问 `http://localhost:8000/`。发布验证记录见 [VERIFICATION.md](docs/VERIFICATION.md)。

## 开发与验证

Node 24.19.0、pnpm 11.25.0、Python 3.12；依赖版本固定在锁文件。

```bash
npm install --global pnpm@11.25.0
pnpm install --frozen-lockfile
python -m pip install -r pipeline/requirements.lock
PYTHONPATH=pipeline python -m pytest pipeline/tests -q
python -m unittest discover -s scripts/tests -q
pnpm --dir apps/web test
pnpm --dir apps/web exec tsc --noEmit
pnpm --dir apps/web build
python scripts/check-dist.py
pnpm --dir apps/web exec playwright install --with-deps chromium
pnpm --dir apps/web exec playwright test site.spec.ts
node scripts/verify-ui-fixtures.mjs
```

`verify-ui-fixtures.mjs` 将虚构测试资料与产物写到 `.cache/`，验证有数据时的排序、分页、详情、转义和历史版本；不会修改 `data/public/`。受限环境可用 `CHROMIUM_PATH` 指定已有 Chromium，不能因为浏览器安装失败而把浏览器测试标为通过。

## 恢复真实数据

先使用允许匿名访问 OpenReview 的环境重新运行官方接口探测。不要绕过 401/403、挑战验证或身份权限。

```bash
PYTHONPATH=pipeline python -m reviewcase discover --venue ICLR.cc/2026/Conference --out .cache/discovery
```

按照 `pipeline/README.md` 核对真实 invitation、rating 枚举、决定标签和来源页面；**未经核实不能把 `verified` 改成 true**。确认配置后执行：

```bash
PYTHONPATH=pipeline python -m reviewcase ingest --config config/iclr2026.yaml --out .cache/capture --resume
PYTHONPATH=pipeline python -m reviewcase normalize --capture .cache/capture --config config/iclr2026.yaml --out .cache/normalized
PYTHONPATH=pipeline python -m reviewcase rank --input .cache/normalized --out .cache/rankings
PYTHONPATH=pipeline python -m reviewcase export --input .cache/normalized --rankings .cache/rankings --out .cache/candidate
PYTHONPATH=pipeline python -m reviewcase validate-public --path .cache/candidate --mode production
```

先生成候选，审计并归档后再更新当前内容。不要用手改覆盖数字的方式通过校验。完整抓取耗时取决于公开记录量和限流；本次未验证全会议运行时长或接口规模表现。

## 分析与发布

报告通过 Work 等离线环境生成，先在私有草稿目录检查证据；在获得外部编辑审批后才导入。具体格式、字段与命令见 `pipeline/README.md`、`schemas/`、`docs/EDITORIAL_POLICY.md`。

公开 GitHub 分支、PR、Issue 和工作流产物都不是私密草稿空间。提交前运行 `python scripts/repository-guard.py`；检查只能发现问题，不能撤销已经发生的公开泄露。

- `docs/DEPLOYMENT.md`：Pages 配置、发布权限和回滚。
- `docs/QUARTERLY_RELEASE.md`：每三个月的手动更新及紧急纠错。
- `docs/REPORT_WORK_TEMPLATE.md`：离线分析清单。
- `docs/SOURCES.md`：官方依据；价格相关内容只是规划历史，本项目未启用任何模型 API。

## 数据与解释边界

评分反差不是错评证明。ICLR 2026 的评分回滚背景在页面固定提示。原稿不可得时不能用后续版本指控早期评审事实错误；没有论文全文及图表核验时不得宣称完成专业审稿。

代码与数据许可分别处理；论文材料链接保留所读取的公开版本，不打包论文 PDF、身份字段或泄露记录。
