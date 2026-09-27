# OpenJudge / ReviewCase · ICLR 2026

## 公开新闻版

网站： https://openjudge.longyunbo218.chatgpt.site

10 篇 ICLR 2026 评审案例已改为证据分级的批判性评论。每篇提供具体争议、原始来源、反证和判断边界；不冒充人工技术鉴定。公开版构建：`node scripts/build-newsroom.mjs`。发布范围和材料口径见 [PUBLIC_NEWSROOM.md](docs/PUBLIC_NEWSROOM.md)。


纯静态的公开评审资料浏览网站：低分录取、高分拒稿、论文详情、证据分析、版本记录和纠错说明。Astro + TypeScript 前端，Python 匿名只读数据管线，GitHub Pages 部署配置。按三个日历月手动更新；没有定时抓取、数据库、账号、MCP 或付费模型调用。

## 当前交付状态

这是可运行、可测试的工程第一版，**还不是已验收的真实论文榜单**。

- 2026-09-27 实测：OpenReview 会议 group 接口 HTTP 200；投稿 / 评审 notes 接口 HTTP 403 `ChallengeRequiredError`。
- 当前实际论文 **0**，实际评审 **0**，真实样本审计 **0/30**，已批准分析报告 **0**。
- 正式发布日期、会议总数和历史评分阶段均未推测填入。网站显示明确空状态。
- 目标仓库：[yuhanlydia/OpenJudge](https://github.com/yuhanlydia/OpenJudge)。尚未部署网站，也未创建定时抓取任务。发布门禁会阻止当前数据部署为正式榜单。

查看 `docs/IMPLEMENTATION_STATUS.md`、`docs/API_DISCOVERY.md` 与 `docs/DATA_AUDIT.md`。测试夹具仅用于工程验证，不是 ICLR 论文；它们不会进入交付的静态榜单。

## 新闻专题预览（2026-09-27）

网站新增新闻首页和逐篇深读页面：本期选取 10 个 ICLR 2026 案例，分别呈现研究内容、评审分歧、作者回应、公开决定、AI 分析、写作建议与限制。公开材料来自 2026-05-08 的第三方 OpenReview 公开存档，并非实时抓取或全会议排名。

10 篇完整分析目前在站长持有的私有预览文件中，尚未获得人工编辑批准，因此不进入公共仓库、默认构建或现有发布工作流。页面模板已可用，原有全会议数据门禁保持不变。预览与来源核验说明见 [NEWSROOM_PREVIEW.md](docs/NEWSROOM_PREVIEW.md)。

## 先看页面

从本仓库获取源码后，先执行下方的安装与 `pnpm --dir apps/web build`。先前交付的 ZIP 已包含 `apps/web/dist/`，可以直接预览：

```bash
python -m http.server 8000 --directory apps/web/dist
```

浏览器打开 `http://localhost:8000/`。电脑只在本地预览时需要运行该命令；正式托管后访客不依赖你的电脑。

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

代码与数据许可分别处理；本次仅链接 OpenReview 和 ICLR 的官方来源，不打包论文 PDF、身份字段或泄露记录。
