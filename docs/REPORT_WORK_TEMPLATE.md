# Work 离线报告生产模板

此模板是操作清单，不是已生成、已批准的分析。

## 输入

- 一篇论文的固定 EvidenceBundle；确认 forum_id、snapshot_id、bundle_hash、rubric_version。
- 公开可核验的论文版本与必要图表；无法取得原稿时明确标记。
- 报告草稿写在 `.cache/` 或私有存储，不能写进公共分支、PR 或 Issue。

## 三阶段分析

A. 先读论文与评审实质内容，尽量屏蔽决定、分数、机构。逐条抽取可以核验的主张，同时核对肯定与否定判断。

B. 加入评分、作者回复和讨论。每条争议列支持证据、反证、最强合理替代解释及限制。不能以关键词搜索不到为“原稿不存在”的充分证明。

C. 加入 meta-review 和决定。只说明公开材料能解释什么；不推测私下讨论、人格、动机，不生成个人羞辱榜或“错评概率”。

## 写作与结构

按 `schemas/analysis-report.schema.json` 创建结构化记录，再写叙述。每个 claim 的证据 ID、精确 quote、source hash、字符范围、论文版本和可见页码来自 bundle；不能编造引用。

写作诊断区分：原稿已清楚 / 信息存在但组织不清 / 确实缺少材料 / 无法核验。改写不增加实验、结果或技术主张；事实引用必须来自已有 fact_ids。

Work 的模型名称无法独立确认时，model_reported=null、model_provenance=unknown；操作者提供名称时标 user_reported。不能把文件名当作 API 验证。

## 校验与审核

运行 `check-report` 只表示格式与引用定位可检查。外部编辑必须看过真实报告，明确批准其精确内容摘要、bundle_hash 和 rubric_version；代理不能自行生成真实批准记录。强矛盾结论另行人工核对原稿、附录与图表。

批准后通过 `publish-report` 输出允许公开的字段，再在 `export --reports content/reports` 中导入对应快照。任何证据改变则待复核；拒绝用改日期的方式继续沿用旧结论。
