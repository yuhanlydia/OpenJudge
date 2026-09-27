# ReviewCase Quarterly Static Core Implementation Plan (v2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development when available, or superpowers:executing-plans, to implement this plan task-by-task. Track progress with the checkboxes below. The user is requesting a plan; no implementation has been performed in this package.

**Goal:** 交付真实、可追溯、可静态托管的 ICLR 2026 低分录取/高分拒稿网站，具备离线 GPT 报告导入能力。

**Architecture:** Python 获取和规范化公开材料，输出经过校验的固定 JSON 快照；Astro 预渲染页面，浏览器只处理本地筛选。GitHub-hosted CI 只在手动季度任务或批准发布时负责批处理与部署；GPT 分析来自受控导入，MCP/API 不属于核心依赖。

**Tech Stack:** Astro + TypeScript + pnpm；Python + openreview-py + Pydantic + pytest；Playwright；GitHub Actions / Pages。运行时初选 Node 24、Python 3.12；T1/T7 按实际依赖支持核对并写入版本文件与锁文件，不使用未锁定的 latest 部署。

**Spec:** `docs/superpowers/specs/2026-09-27-reviewcase-static-design.md`

## Global Constraints

- ICLR 2026 主会议；仅公开数据；评分反差不是错评判决。
- 默认至少 3 份有效官方评分；首批每类 50 篇深读候选，保留边界并列。
- 同一评分 schema 比较；缺失不补零；Withdrawn/Desk Reject/Unknown/冲突分开处理。
- 个人电脑不必常开；无 GPU、无常驻数据库、无前端模型调用。
- `cadence_mode=quarterly_manual`、`refresh_interval_months=3`；默认仅手动刷新，不设置 schedule/cron、轮询或实时后端。
- 季度普通更新保留历史快照；紧急纠错/下架允许例外补丁，所有公开历史和 JSON 入口同步生效。
- `analysis_mode=import_only`、`api_enabled=false`、`api_budget_usd=0`。
- 公共仓库不得保存未批准的 AI 指控、私人作者材料、登录信息或原始身份字段。
- 标明公开评分快照和 ICLR 2026 回滚背景，不虚构历史版本。
- 未经真实抓取验收，不发布以演示数据组成的榜单。
- 格式校验/引用定位不等于人工专业复核。
- 所有下列 CLI 名称与测试均为待实现合同，不是本包中已有工具。

## Review Focus

1. 子评论更新而投稿 mdate 不变：更新策略应检测候选 forum 变化；测试归 T2/T10。
2. 看似同一 reviewer 的两份不同 notes：不能任意覆盖；测试归 T3。
3. 原稿缺失、只剩 camera-ready：不能给出“原稿已包含”的确定判错；测试归 T5/T6。
4. 公共 PR/日志泄露私有草稿或 API Key：即使不部署页面也已经泄露；测试归 T9/T10。
5. 更新中途失败、页面配置有项目子路径：应保留最后成功快照，来源/详情链接仍有效；测试归 T8/T10。

## 仓库目标结构

```text
reviewcase/
  AGENTS.md
  README.md
  .gitignore
  .node-version
  pnpm-workspace.yaml
  pnpm-lock.yaml
  docs/
    IMPLEMENTATION_STATUS.md
    API_DISCOVERY.md
    DATA_AUDIT.md
    DEPLOYMENT.md
    QUARTERLY_RELEASE.md
    EDITORIAL_POLICY.md
    superpowers/specs/...
    superpowers/plans/...
  config/
    iclr2026.yaml
    schemas/iclr2026-discovered.json
  schemas/
    public-index.schema.json
    analysis-report.schema.json
    evidence-bundle.schema.json
  pipeline/
    pyproject.toml
    requirements.lock
    reviewcase/
      __init__.py
      __main__.py
      models.py
      config.py
      discover.py
      fetch.py
      capture.py
      normalize.py
      score.py
      rank.py
      evidence.py
      report.py
      export.py
      release.py
      validate.py
      publish_guard.py
    tests/
      fixtures/
      test_config.py
      test_discover.py
      test_fetch.py
      test_capture.py
      test_normalize.py
      test_score.py
      test_rank.py
      test_evidence.py
      test_report.py
      test_export.py
      test_release.py
      test_publish_guard.py
      test_end_to_end.py
  data/public/
    manifest.json
    release-manifest.json
    index/iclr2026.json
    papers/<forum_id>.json
    coverage.json
    rankings.json
  data/releases/
    index.json
    <release_id>/...  # 每期已批准静态数据、报告及 manifest；不可用来放私有草稿
  content/reports/
    <forum_id>/<report_id>.json
  apps/web/
    package.json
    astro.config.mjs
    src/
      styles/tokens.css
      layouts/BaseLayout.astro
      components/{CaseRow,ScoreStrip,StatusBadge,EvidenceCard,ProcessNotice}.astro
      lib/{data,filter,basepath,renderSafeText}.ts
      pages/
        index.astro
        iclr-2026/{low-score-accepted,high-score-rejected}.astro
        papers/[forum_id].astro
        {methodology,data-status,contribute}.astro
        versions/{index,[release_id]}.astro
    tests/{filters,basepath}.test.ts
    e2e/{boards,paper,security,accessibility}.spec.ts
  .github/
    ISSUE_TEMPLATE/correction.yml
    workflows/{ci,refresh-data,deploy-pages}.yml
```

`.cache/`、下载的 PDF、模型私有草稿和密钥不纳入版本控制。目录内空位不是要求制造数据；没有实际记录时保持空状态。

## 统一数据合同

所有公共文件带 `schema_version="1.0"`、`snapshot_id`、`generated_at` 和 `is_fixture`。生产发布要求 `is_fixture=false` 且有完整 capture manifest。每个正式版本还带 spec 定义的 ReleaseManifest；历史数据与对应报告在同一 release 内读取。

在 `models.py` 定义并在 JSON Schema 中导出 spec 的 PaperRecord、ReviewRecord、PaperVersion、ScoreSummary、Claim、Evidence、AnalysisReport、ReleaseManifest。额外定义：

- `VenueConfig`：venue_id、submission_invitation、review_invitation_rules、decision_labels、score_schema、public_only、fetch_limits。
- `RawCapture`：capture_id、目录路径、venue_schema_hash、分页清单、成功/失败数、capture_complete。
- `NormalizedCorpus`：papers、reviews、coverage、issues、snapshot_id。
- `RankingResult`：low_score_accepted、high_score_rejected、candidate_ids、ties、eligible_count。
- `EvidenceBundle`：bundle_id、forum_id、versioned_sources、coverage、bundle_hash。
- `ValidationResult`：ok、errors、warnings；每条错误含稳定 code 和记录 ID，不含秘密。

辅助类型也在 T1 的 `models.py` 中声明：`RawNote = dict[str, Any]`；`OpenReviewClient` 是最小只读客户端协议；`DiscoveryResult` 包含 discovered_config、raw_schema_hash、sample_ids 和 validation_errors；`RatingSchema` 包含 scale_id、field_name、allowed_values 与原始标签；`DecisionResolution` 包含 decision、source_kind、source_id、conflicts；`PublicManifest` 包含 schema_version、snapshot_id、file_hashes、coverage；`ApprovedReport` 是带有效人工 approval_record 的 AnalysisReport。前端 `PublicSnapshot`、`CaseIndex`、`CaseFilter`、`SanitizedMarkup` 在 T7/T8 的 `apps/web/src/lib/types.ts` 统一定义，公共字段从 JSON Schema 对齐，不另行猜字段。

`capture_complete` 只表示预定的投稿枚举分页已完整结束；个别论坛不可读取可作为有记录的 coverage 缺失，不得被静默忽略。存在未取得评分的论坛时，`ranking_scope=observed_sample`，页面标题明确“当前已取得材料中的排行”，不能声称全会议最极端案例。枚举本身分页失败则生产发布直接阻止。

报告状态使用 spec 的枚举；别创造另一套近义字段。`model_reported` 无法独立验证时保留 null，并设置 `model_provenance=user_reported/unknown`。

---

## T1 — 项目合同、联网探测和真实 schema 发现

**Files:** 建立 `pipeline/pyproject.toml`、`models.py`、`config.py`、`discover.py`、`__main__.py`、`test_config.py`、`test_discover.py`、`config/iclr2026.yaml`、`docs/API_DISCOVERY.md`、`AGENTS.md`。

**Interfaces:**
- `load_config(path: Path) -> VenueConfig`
- `discover_venue(venue_id: str, client: OpenReviewClient) -> DiscoveryResult`
- CLI：`python -m reviewcase discover --venue ICLR.cc/2026/Conference --out .cache/discovery`
- 产出：经来源核对的 `config/schemas/iclr2026-discovered.json` 与最小权限说明。

- [ ] 写 `test_config_public_only_and_no_paid_api`：public_only 必须为 true；api_enabled=false；预算为 0。
- [ ] 写 `test_discover_uses_submission_name`：构造 venue group 中非默认投稿名称，断言 invitation 来自该字段而非硬编码 Submission。
- [ ] 运行 `pytest pipeline/tests/test_config.py pipeline/tests/test_discover.py -q`，确认尚未实现时失败。
- [ ] 实现配置、模型和 discover；将网络 I/O 通过可替换客户端注入，不在单元测试访问真实服务。
- [ ] 安装本地包后运行 discovery。读取公开 venue 配置与少量公开 notes，记录实际字段、量表合法值、invitation、状态和时间语义。
- [ ] 对照官方页面人工抽查至少 10 个可读 forum。目标包含 Accept/Reject；不足时如实记录，不伪造满足配额。
- [ ] 接口不可达时记录环境网络限制并继续离线开发；真实验收保持未通过。只有成功发现 schema 后，才能把配置标记 `verified=true`。
- [ ] 重跑测试与类型检查，通过后提交本任务。不得提交原始身份字段或未经清理响应。

**验收：**有实际 schema 核查结果，或者明确的未通过状态；后续代码不会把未核实映射当真值。

## T2 — 分页抓取、限速、断点恢复

**Files:** `fetch.py`、`capture.py`、`test_fetch.py`、`test_capture.py`；扩展 `__main__.py`。

**Interfaces:**
- `capture_corpus(config: VenueConfig, workdir: Path, resume: bool) -> RawCapture`
- `fetch_forum(forum_id: str, client: OpenReviewClient) -> list[RawNote]`
- CLI：`python -m reviewcase ingest --config config/iclr2026.yaml --out .cache/capture --resume`

- [ ] 写 `test_pagination_failure_is_not_empty_page`：第二页超时不能把 capture_complete 标成 true。
- [ ] 写 `test_retry_after_and_attempt_cap`：429 尊重 Retry-After；最多 5 次；401/403 不重试绕过。
- [ ] 写 `test_resume_deduplicates_ids`：断点前后重复 ID 只落一次，页清单可对账。
- [ ] 写 `test_nested_reply_and_child_update`：能保留二级 replyto；父 note mdate 未变时，候选 forum 刷新仍检测子评论变化。
- [ ] 运行 `pytest pipeline/tests/test_fetch.py pipeline/tests/test_capture.py -q` 确认失败。
- [ ] 实现速率限制、超时、分页清单与原子落盘，初始并发 2、1 请求/秒。
- [ ] 用小样本 capture 验证后，再抓公开投稿和评分/决定，不先下载全部 PDF。
- [ ] 运行同样测试确认通过；日志只输出 ID、计数与错误码。提交本任务。

**验收：**重复运行不产生重复评分，失败不能伪装全量完成；采集过程可恢复。

## T3 — 规范化评分、版本与最终决定

**Files:** `normalize.py`、`score.py`、`test_normalize.py`、`test_score.py`。

**Interfaces:**
- `normalize_capture(capture: RawCapture, config: VenueConfig) -> NormalizedCorpus`
- `parse_rating(raw: object, schema: RatingSchema) -> Decimal | None`
- `resolve_decision(notes: list[RawNote], config: VenueConfig) -> DecisionResolution`
- CLI：`python -m reviewcase normalize --capture .cache/capture --config config/iclr2026.yaml --out .cache/normalized`

- [ ] 写 `test_rating_is_not_confidence`：缺 rating、有 confidence=4 的 note，rating_value 必须为 null。
- [ ] 写 `test_missing_rating_not_zero`：虚构量表下 [4,6,null] 得 mean=5、n=2，不得 mean=3.33。
- [ ] 写 `test_rating_outside_schema_is_invalid`：合法枚举之外的数字不参与均分。
- [ ] 写 `test_review_edits_count_once` 与 `test_duplicate_alias_notes_quarantined`，分别覆盖 edits 去重与身份冲突。
- [ ] 写 `test_comment_word_reject_not_decision`、`test_withdrawn_not_rejected`、`test_decision_conflict_excluded`、`test_status_only_explicit`。
- [ ] 运行两组测试确认失败；实现基于 discovery 的字段/标签映射与 source_kind。
- [ ] 为 every note 保留来源 ID/hash；ICLR2026 的 score_stage 默认 observed_public_snapshot，而不是 final_after_rebuttal。
- [ ] 重跑测试通过；输出实际归一化计数、未知标签清单，提交本任务。

**验收：**算术和状态完全可追溯；遇到未知/冲突进入隔离清单，而不是猜测。

## T4 — 可重现的两个榜单与统计

**Files:** `rank.py`、`test_rank.py`；扩展 CLI。

**Interfaces:**
- `build_rankings(corpus: NormalizedCorpus, min_reviews: int = 3, candidate_n: int = 50) -> RankingResult`
- `score_percentile(mean: Decimal, cohort: list[Decimal]) -> Decimal`
- CLI：`python -m reviewcase rank --input .cache/normalized --min-reviews 3 --candidate-n 50 --out .cache/rankings`

- [ ] 写 `test_accepted_ascending_rejected_descending`，用明确标记的虚构记录验证方向。
- [ ] 写 `test_mean_keeps_score_distribution`：[2,2,8,8] 与 [4,4,6,6] 均分同为 5，但 std_population 分别为 3 和 1。
- [ ] 写 `test_min_reviews_and_invalid_excluded` 与 `test_desk_reject_outside_main_board`。
- [ ] 写 `test_boundary_ties_retained`：第 50 位并列者全部进入候选清单，不任意截断。
- [ ] 写 `test_midrank_percentile`：全员同分时，每篇分位 0.5。
- [ ] 写 `test_no_ranking_before_rounding`：接近均分按精确值排，不按显示字符串排序。
- [ ] 运行 `pytest pipeline/tests/test_rank.py -q` 确认失败；实现排序、分位和描述统计。
- [ ] 验证同一 snapshot 重跑得到同样排序；通过后提交。

**验收：**每个榜单可以由公开评分复算；没有“错评概率”或未经支持的因果打分。

## T5 — 证据包、季度快照与覆盖报告

**Files:** `evidence.py`、`export.py`、`validate.py`、`test_evidence.py`、`test_export.py`、三个 JSON Schema。

**Interfaces:**
- `build_evidence_bundle(forum_id: str, corpus: NormalizedCorpus, source_dir: Path) -> EvidenceBundle`
- `export_public(corpus: NormalizedCorpus, rankings: RankingResult, output: Path) -> PublicManifest`
- `validate_public(output: Path, mode: Literal['fixture','production']) -> ValidationResult`
- CLI：`python -m reviewcase bundle --forum FORUM_ID --input .cache/normalized --out .cache/bundles`
- CLI：`python -m reviewcase export --input .cache/normalized --rankings .cache/rankings --out data/public`
- CLI：`python -m reviewcase validate-public --path data/public --mode production`

- [ ] 写 `test_original_missing_not_camera_ready_substitute`：仅 camera-ready 时 coverage.original_available=false。
- [ ] 写 `test_quote_span_matches_exact_source`：偏移与 hash 不一致即失败。
- [ ] 写 `test_public_export_allowlist`：原始 email、authors verification、private draft 不进入任何公开文件。
- [ ] 写 `test_production_rejects_fixture_and_incomplete_capture`。
- [ ] 写 `test_manifest_counts_balance`：发现数等于成功处理与明确未处理之和；每个过滤原因可追溯。
- [ ] 运行测试确认失败；实现逐来源 hash、版本、摘录和 coverage，不给缺失部分填 AI 文本。
- [ ] 仅为待分析候选获取需要的公开论文材料。图表核验需要页面图像时由后续内容生产环境完成；提取失败必须记录。
- [ ] 写 `test_release_metadata_separates_observed_generated_published_dates`：采集结束晚于开始、报告时间独立、未正式发布时 published_at 必须 null；不能用默认值捏造时间。
- [ ] 写 `test_new_release_preserves_old_snapshot`：发布 R2 后 R1 文件哈希不变；R1 的榜单只能引用 R1 中的报告和证据。
- [ ] 实现完整快照先写临时目录、验证后归档到 `data/releases/<release_id>/` 并更新当前 `data/public/`；拒绝普通更新覆盖已经发布的 release_id。公开导出只采用字段允许清单。
- [ ] 导出 ReleaseManifest 与 `data/releases/index.json`，标明数据收集窗口、来源阶段、变更摘要与检查周期。空历史/首次发布是合法状态；所有未取得的历史阶段标 unknown/unavailable。
- [ ] 重跑测试通过；检查生产导出不包含 .cache、原始 PDF 或私有材料，提交。

**验收：**可公开、可追溯、可对账；版本缺失明确限制模型判断。

## T6 — Work 报告导入与发布门禁（无 API）

**Files:** `report.py`、`publish_guard.py`、`test_report.py`、`test_publish_guard.py`、`docs/EDITORIAL_POLICY.md`。

**Interfaces:**
- `validate_report(report: AnalysisReport, bundle: EvidenceBundle) -> ValidationResult`
- `approve_report(report: AnalysisReport, actor: str, approval_record: str) -> ApprovedReport`
- `mark_stale(report: AnalysisReport, current_bundle_hash: str) -> AnalysisReport`
- CLI：`python -m reviewcase check-report --report .cache/draft.json --bundle .cache/bundles/BUNDLE_ID.json`
- CLI：`python -m reviewcase publish-report --report .cache/draft.json --bundle .cache/bundles/BUNDLE_ID.json --approval-record .cache/approval.json --out content/reports`

- [ ] 写 `test_report_rejects_missing_evidence_id`、`test_quote_not_found_blocks_claim`、`test_bundle_mismatch_marks_stale`。
- [ ] 写 `test_unchanged_bundle_and_rubric_reuses_approved_report`：证据内容、分析规则及批准状态未变时复用，不因抓取日期更新而调用模型。
- [ ] 写 `test_historical_report_is_not_attached_to_new_evidence`：R1 报告不能绑定 R2 已变化证据；旧期仅作为注明日期的历史分析保留。
- [ ] 写 `test_missing_original_blocks_original_contradiction`。
- [ ] 写 `test_user_reported_model_not_api_verified`。
- [ ] 写 `test_unapproved_report_not_public` 和 `test_approval_requires_explicit_record`；审批是站长/授权人员行为，不能由模型自己伪造文件来满足。
- [ ] 写 `test_rewrite_cannot_add_new_facts` 的结构约束：改写中的事实引用必须来自报告已列事实；技术含义的最终核查在人工审核清单。
- [ ] 运行测试确认失败；实现导入、校验、stale 与审批记录校验。
- [ ] 提供 Work 使用的报告模板：三个分析阶段、正反证据、写作诊断、公开决定解释与限制。
- [ ] 明确公共 PR 不是私人草稿；先将 draft 私下返回站长，不自动 push。
- [ ] 用虚构报告验证系统，不将其发布；真实报告按授权样本验证后提交代码。

**验收：**没有 API Key 也能导入真实报告；引用校验和人工复核状态不混淆。

## T7 — 静态页面、双榜与筛选

**Files:** Astro/pnpm 配置、`lib/types.ts`、BaseLayout、tokens.css、榜单组件、首页、两张榜单页、`lib/data.ts`、`lib/filter.ts`、`filters.test.ts`、`e2e/boards.spec.ts`。

**Interfaces:**
- `loadPublicSnapshot(): PublicSnapshot`，构建时从本地 data/public 读取，禁止联网。
- `filterCases(cases: CaseIndex[], filter: CaseFilter): CaseIndex[]`，纯函数。
- `CaseFilter`：q、minMean、maxMean、minReviews、reportState、page；pageSize 固定 25。
- 命令：`pnpm --dir apps/web test`、`pnpm --dir apps/web build`。

- [ ] 写筛选测试：中文/英文关键词、数字排序、空结果、页码越界、缺失字段。
- [ ] 写 Playwright 用例：两个榜单的方向不同、原始分数可见、没有报告时显示尚未分析。
- [ ] 先运行失败测试；再按 spec 视觉 token 和尺寸实现页面。
- [ ] 保留预渲染的前 25 行，JS 失败时仍可浏览；完整索引按需加载。
- [ ] query 参数可保存筛选状态；图表启用时只能读取同一 snapshot 的统计。
- [ ] 构建不依赖 .env 或数据库；no-results 不显示虚构卡片。
- [ ] 测试通过后提交页面任务。

**验收：**静态服务器即可浏览、搜索和排序；UI 不请求 OpenAI 或 OpenReview。

## T8 — 论文详情、报告、来源、方法与纠错

**Files:** `papers/[forum_id].astro`、EvidenceCard、ProcessNotice、`renderSafeText.ts`、`basepath.ts`、方法/数据状态/投稿页、相关 e2e 与 basepath 测试。

**Interfaces:**
- `sitePath(path: string, base: string): string`
- `renderSafeText(text: string): SanitizedMarkup`
- paper route 来自公开索引；正文与报告引用来自固定数据，不接受任意用户传入 HTML。

- [ ] 写 `test_project_basepath_links`：根域和 `/reviewcase/` 子路径均能访问资源和详情。
- [ ] 写页面测试：显示完整分数、决定来源、快照时间、ICLR2026 提示、版本缺失、尚未分析、stale 报告。
- [ ] 写静态 `/versions/` 与 `/versions/<release_id>/` 测试：首期无历史时正常；历史页显示明确日期和“历史快照，不代表当前状态”；全部引用来自同一 release。
- [ ] 历史页面在构建时本地读取并预渲染，不新增 SSR/API 路由或客户端后台轮询。
- [ ] 写 XSS 测试：review 含 script、javascript URL、MDX 表达式时不执行。
- [ ] 写纠错用例：说明 GitHub Issue 是公开的；没有配置私密联系入口时不编造邮箱。
- [ ] 运行失败测试；实现桌面对照/手机堆叠、证据跳转与页签。
- [ ] 方法页解释均分、排除项、并列和非因果性质；数据页显示失败来源和统计分母。
- [ ] 通过全部测试，提交。

**验收：**任何确定性结论都能展开来源；不同来源身份与不同审核状态不会混淆。

## T9 — 全链路质量、安全与真实样本审计

**Files:** `test_end_to_end.py`、`e2e/security.spec.ts`、`e2e/accessibility.spec.ts`、`docs/DATA_AUDIT.md`、CI 工作流。

**Interfaces:**
- CLI：`python -m reviewcase validate-public --path data/public --mode production`
- `pnpm --dir apps/web exec playwright test`
- 静态 dist 的 secrets/private-files 检查在 publish_guard.py 实现。

- [ ] 写从虚构 capture → normalize → rank → export 的金标准测试；构造数据永久标 fixture。
- [ ] 写“页面网络请求中无 OpenAI、无 OpenReview、无未知第三方”的浏览器测试。
- [ ] 写发布产物检查：阻止密钥格式、私有目录、未经批准 report、is_fixture=true、报告对应不到来源。
- [ ] 写 375px 与 1440px 布局/键盘测试，检查状态不是仅颜色区分。
- [ ] 运行失败测试；实现修复直到全部通过。
- [ ] 真实审计目标至少 30 篇，覆盖低分 Accept、高分 Reject、普通 Accept、普通 Reject、排除/边界情况；这是最低开发审计目标，不是质量统计样本设计。记录实际达到数量。
- [ ] 每篇人工对照评分列表、均分、决定、源 URL 与版本；错误归因到解析模块并增加回归测试。
- [ ] 缺失/错误未解决时不宣称全量完成。提交审计文档和修复。

**验收：**本地测试、浏览器测试与真实样本核对均有证据，不只截图好看。

## T10 — GitHub Pages、每三个月手动发布与失败恢复

**Files:** `.github/workflows/ci.yml`、`refresh-data.yml`、`deploy-pages.yml`、`pipeline/reviewcase/release.py`、`pipeline/tests/test_release.py`、`docs/DEPLOYMENT.md`、`docs/QUARTERLY_RELEASE.md`、更新/回滚相关测试。

**Interfaces:**
- `refresh-data`：只有 workflow_dispatch（手动触发）；每三个月按发布清单集中更新元数据和公开证据，不启用 schedule、不产生模型结论。
- `release.py`：`next_review_date(anchor: datetime.date, months: int = 3) -> datetime.date`，按日历月推进并对月底截断；`anchor` 使用首期成功发布日期或站长明确调整后的基准，不因普通纠错补丁改变。
- `deploy-pages`：从已经过审核的数据 commit 构建并部署；仅必要权限。
- `ci`：所有 PR 跑无密钥测试；不执行来自 fork 的不可信代码并同时赋予 secrets。

- [ ] 写“抓取第二页失败时不覆盖最后成功快照”的测试。
- [ ] 写“当前新版证据 hash 变化时标待复核，不改写旧期报告”的测试。
- [ ] 写“单条 denylist 能不依赖抓取直接下架”的测试；当前页、历史页、静态 JSON 与旧报告入口都必须生效，不能只隐藏列表卡片。
- [ ] 写 `test_refresh_workflow_has_manual_trigger_and_no_schedule`：更新 workflow 有 workflow_dispatch，没有 schedule/cron、定期心跳或驻留抓取步骤。
- [ ] 写 `test_quarterly_due_date_uses_calendar_months`：以发布时选定时区的日期计算，如测试夹具 2027-01-31 → 2027-04-30；此日期仅表示计划检查时间，不创建任何外部任务。
- [ ] 写 `test_correction_release_does_not_require_network_or_model`：经批准的单条纠错能基于本地已发布数据生成补丁；普通补丁不移动原季度检查基准。
- [ ] 验证 workflow 无前端密钥、无 pull_request_target 执行不可信代码、无公开草稿日志。
- [ ] 实现 GitHub-hosted runner；第三方 Action 核对官方仓库后 pin commit SHA。
- [ ] 手动季度任务产生候选 snapshot/release；数据校验、页面测试和发布审批通过后才部署。报告未通过复核时不自动更新结论，可明确显示待分析/待复核。自动模型调用不在此路径。
- [ ] 编写季度清单：手动发起 → 抓取/对账 → 检查变更 → 复用或重核报告 → 审批 → 静态构建/测试 → 发布 → 记录下次建议检查日。明确没有已创建的定时任务；状态显示真实上次成功时间。
- [ ] 输出 dist 并验证本地静态托管。拿到发布授权后部署；没权限则交付 dist 和准确的剩余授权清单。
- [ ] 真正部署后以未登录身份检查根页/子路径/详情/来源链接；执行一次回滚演练后恢复最新版本。

**验收：**关闭站长电脑仍可访问；一次季度刷新失败不让网站变空；可证明没有运行时模型调用、自动定时抓取或常驻业务后端；历史期可查，纠错可独立发布。

## T11 — 文档、使用说明与最终交付

**Files:** README、AGENTS、IMPLEMENTATION_STATUS、DEPLOYMENT、EDITORIAL_POLICY、数据说明。

- [ ] 写明每三个月怎样手动更新元数据、对齐材料阶段、复用报告、导出证据包、导入报告、批准公开、查历史版本、标记错误/下架及回滚。
- [ ] 写明网站托管、内容生产、MCP 和模型费用是不同层；零 API 的运行路径可实际走通。
- [ ] 记录真实数据数量、失败/未知字段、未完成审计和报告覆盖，不使用设计目标替代结果。
- [ ] 写出所有实际执行的测试命令与退出结果；只有真实部署后给出线上地址。
- [ ] 输出源码包和静态产物；有授权仓库则提交已完成工作，没有则不声称 push 成功。
- [ ] 最终核查没有自行执行可选 MCP/API 计划，没有擅自开通付费服务。

## 执行依赖与阶段交付

T1→T2→T3→T4→T5 构成数据主线。T7 在数据合同固定后可使用明确夹具并行开发，但真实发布必须等待 T5/T9。T6 与 T8 完成报告导入和展示。T9→T10→T11 才能认定核心可交付。

第一次可发布版本可以没有任何 GPT 报告；它必须具有真实榜单、详情、来源、方法和覆盖说明。不要为了等模型预算而搁置这部分。

## 建议最终核验命令

下面命令在实现相应 CLI/脚本后执行；此规划包本身不能运行这些命令完成建站。

```bash
python -m pip install -e ./pipeline
pytest pipeline/tests -q
python -m reviewcase validate-public --path data/public --mode production
pnpm install --frozen-lockfile
pnpm --dir apps/web test
pnpm --dir apps/web build
pnpm --dir apps/web exec playwright test
```

全部通过只说明工程核验通过；专业审稿结论仍依赖证据与人工复核。
