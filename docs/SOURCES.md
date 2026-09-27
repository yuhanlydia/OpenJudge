# 官方资料与设计依据

**v2 修订说明：**本次依据用户的新要求改为纯静态、每三个月手动集中更新；未重新进行外部资料核验。以下链接及接口/价格记录沿用上一版，执行前重新核实，不能把本次文档修订当成实时价格或 API 可用性证明。

核对日期：2026-09-27。产品、API、许可证和平台限制可能变化，实施前重新核对涉及的接口与价格。以下是文档核查，不代表已对用户账户功能、会议实际字段或抓取结果完成实测。

## S01 — OpenReview：获取所有投稿及回复
`https://docs.openreview.net/how-to-guides/data-retrieval-and-modification/how-to-get-all-notes-for-submissions-reviews-rebuttals-etc`

依据：通过 venue group 发现投稿 invitation；`get_all_notes` 支持 invitation/forum 等过滤；`details='replies'` 可协助获取回复；相同 venueid 的录用稿查询不等价于所有状态投稿；API v2 content 通常包装在 value 字段中。实际会议仍需探测 schema。

## S02 — OpenReview Terms of Use
`https://openreview.net/legal/terms`

依据：Comment 与 Configuration Record 的许可、元数据许可、Article 自身许可证与访问控制相互独立。公开可访问不等于任意个人数据都应再次传播。计划不作跨司法辖区的法律保证。

## S03 — ICLR 2026 Response to Security Incident
`https://blog.iclr.cc/2025/12/03/iclr-2026-response-to-security-incident/`

依据：2025 年 11 月冻结讨论、回滚评审文字与分数、重新分配 AC；AC 综合原始评审、回复和自身判断，分数不是唯一依据。网站须展示流程背景，但不能未经版本核验就宣称抓到的每一条分数精确属于某个历史阶段。

## S04 — GitHub Pages
`https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages`

依据：托管静态 HTML/CSS/JavaScript；免费账户的公开仓库可使用 Pages；公开/私有仓库支持取决于套餐。静态托管本身不是任意后端代码的执行环境。

## S05 — GitHub Actions 触发方式
`https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows`

依据：支持 schedule、workflow_dispatch 等事件；定时任务可能延迟/丢弃；公开仓库长时间无活动可能自动禁用 schedule；这不是有实时 SLA 的调度器。本版选择仅手动触发，不设置 schedule；保留刷新时间和失败保留机制。

## S06 — Astro 静态与按需渲染
`https://docs.astro.build/en/guides/on-demand-rendering/`

依据：默认预渲染静态页面；将来可按路由扩展按需渲染。交互式筛选和图表不要求每次在服务端生成页面。

## S07 — ChatGPT 与 API 分开计费
`https://help.openai.com/en/articles/9039756-managing-billing-for-chatgpt-and-the-api-platform`

依据：ChatGPT 订阅与 API 独立计费；MCP 连接不把个人订阅转换成网站可用的 API 额度。

## S08 — OpenAI：构建 MCP server
`https://developers.openai.com/plugins/build/mcp-server`

依据：MCP server 提供工具/资源，生产接入需要稳定可达的端点和正确的权限；可部署于 serverless、edge、container 或传统服务。公网插件使用稳定 HTTPS 与 Streamable HTTP。MCP 的传输服务不是一个静态 JSON 文件。

## S09 — OpenAI Responses API 的远程 MCP
`https://developers.openai.com/api/docs/guides/tools-connectors-mcp`

依据：模型通过 MCP 使用工具；Responses API 对远程 MCP 的支持不改变模型推理的 API 计费属性。工具输入输出必须防范不可信内容。

## S10 — ChatGPT Work：本地与云端
`https://learn.chatgpt.com/docs/get-started-with-work`

依据：当账户/界面提供 Cloud 选项时，云端工作不依赖个人电脑持续开机；本地工作适用于个人电脑上的资源。不要据此保证所有账户、工作区与工具都有相同权限。

## S11 — Codex cloud 环境
`https://learn.chatgpt.com/docs/environments/cloud-environment`

依据：云端可检出仓库并执行命令、测试；代理阶段联网受环境设置影响。网络错误应先核对允许访问的域名和代理，不应误报为 OpenReview 故障。

## S12 — GPT-6 Astra 模型
`https://developers.openai.com/api/docs/models/gpt-6-astra`

核对到模型 ID `gpt-6-astra`。核对时 Standard 文本价格为 input $10/百万 token、output $50/百万 token；缓存、长输入、不同服务档位有额外规则。价格仅用于解释预算公式，不是本计划的费用承诺。实际使用时重新核对价格与账号可用性。

## S13 — ChatGPT Sites
`https://learn.chatgpt.com/docs/sites`

依据：可在账户和工作区允许的情况下构建、预览和发布 Sites。此计划把可导出的静态代码与数据放在核心位置，Sites 可作为预览/备选发布，不假定当前对话拥有发布能力。

## S14 — Cloudflare：远程 MCP
`https://developers.cloudflare.com/agents/model-context-protocol/guides/remote-mcp-server/`

依据：可用 Workers 部署 Streamable HTTP MCP；当前文档推荐新的无状态 handler 路径，并提醒部分旧 quick-start 模板仍走弃用实现。实现时跟随当前推荐路径，不机械复制过时模板。

## S15 — GitHub Actions 计费
`https://docs.github.com/en/billing/concepts/product-billing/github-actions`

依据：公开仓库使用标准 GitHub-hosted runner 的计算使用免费；私有仓库的计算和存储涉及套餐额度。不同 runner、存储及附加服务可能另有规则，不能把它概括为一切永久免费。
