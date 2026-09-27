# GitHub Pages 发布与回滚

## 本次未部署

已选定 `https://github.com/yuhanlydia/OpenJudge`，用户授权在该仓库接入工程；网站的公开部署尚未执行。当前公开数据为 0 条、真实数据门禁失败；这些是剩余条件，不是可以忽略的报错。`apps/web/dist/` 是可预览的工程产物，不等于已上线榜单。

## 准备

1. 使用已选定的 `yuhanlydia/OpenJudge` 仓库；实际网站发布需明确授权。仓库是否公开、Actions/Pages 可用额度由账号实际设置决定。
2. 上传已检查的代码、锁文件及经过审计的公开数据。不得上传 `.cache/`、PDF、草稿、身份材料或密钥。
3. GitHub Settings → Pages → Source 选择 GitHub Actions；建议为 `github-pages` environment 配置所需审核人。
4. 按 `QUARTERLY_RELEASE.md` 准备完整且经审核的候选版本。当前 `verified=false` 的配置必须经真实接口与样本核实后更新。
5. 设置可选的公开纠错入口 `PUBLIC_CORRECTION_URL`（构建环境变量，合法 GitHub Issue URL）；未配置时页面明确显示没有提交入口。

## 手动发布

`deploy-pages.yml` 只有 `workflow_dispatch`。输入 `authorize_public_release=true` 表示本次操作者明确授权公开该已审核 commit。`base_path` 填项目路径（本仓库为 `/OpenJudge/`）；根域名网站才使用 `/`。

工作流顺序：生产数据校验 → Python / 前端测试 → 浏览器检查 → 按选定子路径构建 → 对该子路径检查 → 产物扫描 → 上传 Pages artifact → GitHub Pages 部署。任何前置步骤失败均不执行部署；新数据刷新本身也不会自动部署。

第三方 Actions 均已从官方仓库 `git ls-remote` 核对 tag 并锁定 commit SHA。CI 对 PR 只有 contents:read，不使用 pull_request_target，也不向 fork 提供凭据。页面没有运行时模型或 OpenReview 请求。

## 发布后核验

必须确认 GitHub deployment 成功，再从未登录浏览器核对：首页、两个榜单、至少两条详情、方法、覆盖、历史、纠错，以及 375px / 1440px 页面。核对页面网络请求仅来自静态站自身；外部来源只在读者点击时打开。

实际发布时间只能在成功部署后记录，不使用构建时间代替。将确认后的日期写入该 release 的发布记录，首期以站长选定时区建立季度检查基准。详见 pipeline release helper 的 `mark_published`。这一步未在本次任务执行。

## 回滚

保留上一次经审计的源码 commit 和对应 release 目录。新版本失败时继续托管上一版。若已部署后发现问题，由站长在旧的已验证 commit 上手动运行同一 deploy workflow，确认成功后记录回滚原因与实际时间；不要删除原始历史来源。

涉及已确认敏感资料的下架不能通过回滚重新暴露：先将当前 denylist 应用于待回滚版本的公开材料，再构建并核验全部入口。正式上线后还应验证 CDN/历史部署的访问行为；当前未执行线上回滚演练。
