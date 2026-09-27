# OpenJudge 新闻专题预览

## 目的

把评分与决定之间的反差写成读者能读懂的报道：一页新闻首页，十个独立案例页面。每篇区分公开事实、评审意见、作者主张、决定与 AI 分析，并在段落所属章节列出精确 note 链接。

## 资料口径

- 来源：[ICLR OpenReview reviews archive v1.0](https://github.com/qhjqhj00/iclr-openreview-reviews/releases/tag/v1.0)，维护者标注采集于 2026-05-08。
- 本次下载 SHA-256：`350071daf25ebf1aef854ee1d5dc3a81834e1c468917c82a4f78af5548de34fc`。
- 仅处理 `readers=["everyone"]` 的公开条目；未使用身份泄露数据、私人评论或访问凭据。
- 十例是选题样本，不是全会议覆盖、全局前五名或全体评审质量的统计估计。
- 将正式决定与投稿 venueid 交叉检查；Withdrawn/Reject 冲突的候选不列入本期十例。
- 0 是本届可见的合法评分。仅在正文为占位且 AC 明确排除时删除该条评分，不普遍删除零分。
- [ICLR 官方过程回顾](https://blog.iclr.cc/2026/03/31/a-retrospective-on-the-iclr-2026-review-process/)解释评分回退和讨论冻结背景。AC 对潜在改分的判断不等于已发生改分。
- 原稿 PDF 请求仍遇到 HTTP 403；未把评论中的技术主张伪装成独立全文核验、代码检查或实验复现。

## 预览

私有 JSON 是一个文章数组，结构见 `apps/web/src/lib/newsroom.ts`。由站长提供完整路径：

```bash
NEWSROOM_PREVIEW=1 NEWSROOM_FILE=/absolute/path/articles.json pnpm --dir apps/web build
python -m http.server 8000 --directory apps/web/dist
```

可以使用 `OUT_DIR` 把预览构建写到独立目录。无需付费模型 API，也不在浏览器访问 OpenReview。

## 发布边界

未设置 `NEWSROOM_PREVIEW=1` 时，加载器在任何文件读取之前返回空数组，默认构建不导入私有稿件。新闻草稿明确标为 `draft_private` 和“编辑预览 · AI 分析待复核”。来源定位和页面测试不是人工专业审核；不要创建虚假的审批记录，也不要把预览输出上传到公开 Pages。

网站所有者审核十篇实际内容后，才能按原有编辑政策确认公开版本并准备相应发布。当前 `deploy-pages.yml` 的生产数据门禁没有改动，新闻预览不会使空的全会议榜单通过发布验收。
