# ReviewCase Optional MCP and AI Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development when available, or superpowers:executing-plans. This is an optional follow-on plan. Do not execute it merely because the core site has been approved.

**v2 范围提醒：**用户已确定每三个月集中更新的纯静态网站。本文件只作为未来参考，T1—T11 核心实现不得执行 O1—O4；无需自定义 MCP 即可完成季度内容生产和发布。即使未来单独批准 MCP，也不得让公众访问依赖它。

**Goal:** 在已可用的静态网站之上，按独立授权增加 ChatGPT 数据访问接口或自动 GPT 分析，而不让公共网站依赖个人电脑常开。

**Architecture:** 保留静态站和公开快照。先可选地添加只读远程 MCP，让 ChatGPT 读取数据；私有写回和付费 API 生产任务分别独立启用。MCP 不是推理引擎，也不是订阅转 API 的代理。

**Tech Stack:** 核心项目技术栈；可选 TypeScript + Cloudflare Workers + 官方推荐的无状态 MCP handler；可选 Python + OpenAI SDK；写回阶段才增加私有存储。

**Spec:** `docs/superpowers/specs/2026-09-27-reviewcase-static-design.md`

## Global Constraints

- 核心静态网站必须先通过自身验收。
- 自定义 MCP 与付费模型调用均需独立明确授权；预算默认 0。
- 不复制 ChatGPT cookie，不将个人订阅做共享推理后端。
- 只读 MCP 不需要 OpenAI API Key；凭据只在真正需要的服务端使用。
- 草稿写回只能到私有存储；未经批准不 push 到公共仓库或公开 PR。
- 人工批准和证据审查不能由模型伪造。
- 工具返回相同 snapshot 的来源与时间；过期或不可获取时如实说明。

## Review Focus

1. 相对路径、任意 URL 或内网地址：工具只接受已校验 ID 与固定来源域，归 O1。
2. MCP 被误当成模型：只读调用应产生零 OpenAI API 请求，归 O1/O2。
3. 读者权限调用写工具：必须被服务器拒绝，归 O3。
4. 重试、重复任务和并发超过预算：使用预留/结算和幂等任务，归 O4。
5. 工具中的恶意文献指令导致发布或取密钥：读写分离、显式批准、无任意 shell，归 O2/O3/O4。

## 0. 先判断是否真的需要自建 MCP

以下情形不需要：Work 已能通过获准的 GitHub/文件/网页工具读取证据包，并提交符合 schema 的报告。使用现有工具即可，不重新实现仓库访问。

以下情形适合只读 MCP：经常在 ChatGPT 里用自然语言询问跨论文案例，想稳定调用结构化 list/get 工具，而不是每次打开网页或上传包。

以下情形才需要模型 API：希望自己的云任务在无人发起 Work 会话时，定时运行批量分析；或者网站访客提交新材料后即时获得模型分析。MCP 接入本身不满足这个需求。[S07][S08][S09]

## 1. 两种连接方向必须分开

**方向 A：ChatGPT → ReviewCase MCP → 已发布数据。**

ChatGPT 是工具的调用者和推理环境。MCP 返回分数、来源和证据；它不是运行 GPT 的机器。自己在 ChatGPT 中发起的分析按 ChatGPT 账户/工作区可用功能及额度执行。

**方向 B：ReviewCase 生产任务 → OpenAI API → 分析报告。**

自己的代码发起付费推理，取得报告，经过校验和批准后生成静态页面。MCP 可以用来取资料，但不是必需。[S07][S09]

本地 stdio MCP 依赖运行它的机器；远程 HTTPS MCP 可以托管在云端，因此不要求个人电脑开机。云端仍需稳定运行环境，不是完全没有服务端。[S08][S14]

## O1 — 只读 MCP 数据接口

**Files:**
- `services/mcp/package.json`
- `services/mcp/wrangler.jsonc`
- `services/mcp/src/index.ts`
- `services/mcp/src/data.ts`
- `services/mcp/src/tools.ts`
- `services/mcp/tests/{tools,validation,snapshot}.test.ts`
- `docs/MCP_OPERATIONS.md`

**Interfaces:**

`list_cases({conference, outcome_group, min_mean?, max_mean?, min_reviews?, cursor?, limit?})`
返回 items、next_cursor、snapshot_id、observed_at、coverage_note。outcome_group 只允许 low_score_accepted/high_score_rejected；limit 默认 20，上限 50。

`get_case({forum_id, snapshot_id?})`
返回公开 PaperRecord、ScoreSummary、报告状态和来源链接，不返回 private draft。

`get_evidence({forum_id, evidence_id, snapshot_id?})`
返回已批准公开的 Evidence、原文/翻译区分、版本、hash 和来源链接。只存在私有 bundle 的证据不能通过此工具读取。

`get_report({forum_id, report_id?})`
仅返回 published/stale 的公开报告及状态；没有报告时明确 not_generated。

- [ ] 写测试：非法 forum_id、未知会议、limit>50、过期 cursor、缺失来源均返回明确错误/结果，而不是空成功。
- [ ] 写 snapshot 一致性测试：客户端指定旧 snapshot 时不偷偷混入新数据；旧版本不可得时返回 snapshot_unavailable。
- [ ] 写访问边界测试：拒绝任意 URL、路径穿越、localhost/IP 输入；不执行论文正文中的命令。
- [ ] 写零模型调用测试：全部只读工具不会调用 OpenAI API，不要求 OPENAI_API_KEY。
- [ ] 运行 `pnpm --dir services/mcp test` 确认失败；实现固定公开快照的数据 adapter 和四个工具。
- [ ] 参考当前 Cloudflare 推荐无状态 MCP handler，而不是直接复制文档中仍可能残留的旧 McpAgent 模板。[S14]
- [ ] 工具标只读，返回可供人打开的来源 URL；日志只含工具名、ID、错误码和耗时。
- [ ] 测试通过后提交。尚未部署时不得给出假定的线上 MCP 地址。

**验收：**客户端可通过 MCP 协议列出/调用工具；访问 `/mcp` 得到普通网页并不是协议验收。

## O2 — 云端部署、连接 ChatGPT 与兼容测试

**Files:** MCP 部署配置、CI、`docs/MCP_OPERATIONS.md`、`services/mcp/tests/integration.test.ts`。

**Interfaces:** 稳定 HTTPS `/mcp` endpoint，支持当前推荐的 Streamable HTTP。固定允许访问的数据源站点；不允许用户把它变成任意代理。

- [ ] 写初始化、list tools、调用、分页和异常协议测试。
- [ ] 写“上游静态站故障”测试：返回明确不可用状态；有缓存时必须显示缓存时间。
- [ ] 实现限速、超时、有限缓存与健康检查，不让一个查询返回整场会议的评审全文。
- [ ] 取得托管/发布授权后部署；使用 MCP Inspector 检查真实端点。
- [ ] 在当前账户允许的 ChatGPT 插件/开发者接入方式中连接。界面名称和权限实施时按官方文档核对。[S08]
- [ ] 实测“列出高分拒稿候选”“打开某篇证据”“没有报告时会怎样”“尝试发布报告应失败”。
- [ ] 关闭本地开发进程后再次从远程客户端调用，验证不是依赖本地 tunnel。
- [ ] 在文档标明：静态网站仍独立可用；MCP 故障不影响普通浏览。

**验收：**云端 endpoint 真实可用，个人电脑与本地代理不构成生产依赖。

## O3 — 私有草稿写回（独立授权后再做）

只在确实需要 ChatGPT 自动写回草稿时执行。只读 MCP 完全可以先长期使用。

**Files:** `services/mcp/src/{auth,drafts,audit}.ts`、对应测试、私有存储配置和数据保留说明。

**Interfaces:**
- `save_report_draft({forum_id, bundle_hash, report, idempotency_key})`：需要 report:draft 权限，保存到私有存储，返回 draft_id。
- `get_draft_status({draft_id})`：只有 owner/editor 可读。
- 不提供匿名 `publish_report`；公开发布仍走管理员授权和核心发布门禁。

- [ ] 写 reader 不能写、不同用户不能读对方 draft、重复 idempotency_key 不创建重复草稿的测试。
- [ ] 写 private draft 不出现在 list_cases/get_case/get_report/公开静态产物/日志的测试。
- [ ] 写无效 OAuth audience/scope/token 被拒绝的测试。
- [ ] 运行失败测试；实现 OAuth 与最小权限、私有存储、审计、删除和保留期。
- [ ] 认证信息通过托管 secret 管理，绝不放前端或工具返回值。
- [ ] 写回是外部动作，依客户端和工作区规则保留确认；保存成功不代表内容获准公开。
- [ ] 人员批准后才由核心流程导出到公开仓库。模型不能自行生成批准记录冒充授权。

**验收：**未经批准的模型判断不会通过 PR、Issue、日志或部署产物间接公开。

## O4 — 付费 API 批量分析（与 MCP 独立）

这个模块可以完全不使用 MCP：直接读取核心 evidence bundle 即可。

**Files:**
- `pipeline/reviewcase/analysis/{provider,budget,runner,prompts,ledger}.py`
- `pipeline/tests/analysis/{test_budget,test_runner,test_provider}.py`
- `config/analysis.yaml`
- `docs/ANALYSIS_BUDGET.md`

**Interfaces:**
- `analyze_bundle(bundle: EvidenceBundle, settings: AnalysisSettings) -> DraftAnalysisReport`
- `reserve_budget(job_id: str, upper_bound_usd: Decimal) -> Reservation`
- `settle_budget(reservation: Reservation, usage: UsageRecord) -> None`
- `AnalysisSettings`：enabled=false、model 可配置、max_cases_per_run、max_billed_output_tokens、budget_limit、price_version、reasoning 设置、retry_limit、approval_required=true。

`provider.py` 定义 `AnalysisSettings` 与 `DraftAnalysisReport`（核心 AnalysisReport 的 draft_private 状态）；`ledger.py` 定义 `Reservation`（job_id、reserved_usd、status）及 `UsageRecord`（请求 ID、实际模型、各类计费 token、工具费用、price_version、总额）。`budget.py` 只能通过 ledger 的原子事务预留/结算，不能把进程内变量当并发预算账本。

可配置的已核对模型 ID 为 `gpt-6-astra`，但实现时要核对账号权限和最新价格；不能静默改成别的模型仍在网页标为 GPT-6。[S12]

- [ ] 写 enabled=false 或 budget=0 时一条网络推理请求也不能发出的测试。
- [ ] 写两个并发任务预留预算不能双重花费的测试；预算不够则 pending_budget。
- [ ] 写同一 bundle_hash/model/prompt_version 的任务幂等测试；失败/重试记录可追踪。
- [ ] 写结构化输出无效、引用不存在、原稿缺失、source 中含恶意指令时的失败/abstain 测试。
- [ ] 测试中 mock 网络，先确认失败，再实现三阶段分析和私有账本。
- [ ] 真实启用前给站长展示当前价格、总 token 假设、最大调用数和预留预算，取得付费授权。
- [ ] 第一批仅 2 篇真实案例冒烟测试，记录所有调用的账单用量和准确性问题；不直接跑 100 篇。
- [ ] 按实际成本和证据质量决定扩大规模；达到预算上限停止。API 输出只写私有草稿，由核心门禁发布。
- [ ] 运行环境用受控云任务/私有 CI，不在公开 CI 日志或产物里保存未核实的指控性文本。

**预算说明：**

简单的 Standard 文本估价为：全部调用的 input_tokens/1e6 × input_price + 全部计费 output_tokens/1e6 × output_price。计费输出包括适用的推理 token；另外核对缓存写入、长上下文、工具、重试、服务档位和税费。不能仅按页面最终显示的字数估价。

仅作算术示例：按核对时 input=$10/百万、output=$50/百万，若一批所有调用合计 400 万 input 与 60 万计费 output，则基础文本费用为 $70；假设每次请求未触发长输入加价、没有额外工具/缓存写费。**这不是 100 篇论文必然只需 $70 的承诺。**[S12]

## 为什么不先做访客实时聊天

访客实时提交论文并要求分析会增加持久化队列、鉴权、限流、防滥用、费用控制、私有材料处理与删除机制。它不是给静态页面加一个按钮就完工。当前用户主要需要固定会议的反差案例，因此预生成报告优先。

## 退出条件

O1/O2 成功即可停在只读 MCP。O3/O4 没有授权或价值不足时不实施，不影响核心网站交付。最终逐项报告真正完成的服务、URL、权限、测试和费用，不把可选计划写成已经运行的系统。
