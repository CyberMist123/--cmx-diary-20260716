# Claude 独立审计说明

这份审计只用于发现首次部署阻断、数据丢失风险和手机端兼容问题，不用于重构或扩展功能。

## 最简单的使用方法

把公开仓库地址和下面这段提示词发给 Claude：

```text
https://github.com/CyberMist123/PI-Personal-Instance-OS
```

如果 Claude 当前环境不能直接读取 GitHub，则下载仓库 ZIP 后上传，或在本地 clone 后从仓库目录启动 Claude Code。

## 审计提示词

```text
请对这个仓库做一次只读、保守的部署审计。

目标环境：Windows 10/11 + Docker Desktop WSL2；项目目录 D:\AI\PI-Personal-Instance-OS；Mastodon v4.6.3；PostgreSQL 14；Redis 7；Nginx；Cloudflare dashboard-managed Named Tunnel；主要客户端为 iOS Mastodon App；实例关闭注册并启用 limited federation。

严格边界：
1. 不修改任何文件，不提交代码，不创建分支或 PR。
2. 不建议新功能、主题、Bot、AI 集成、监控栈、Kubernetes、S3、Elasticsearch 或迁移到 Linux/VPS。
3. 不重写现有方案。只找会导致首次部署失败、数据损坏、密钥丢失、OAuth/媒体上传/streaming 异常、Windows Docker 持久化问题的缺陷。
4. 以 Mastodon v4.6.3 官方文档/源码、Docker Compose 行为和 Cloudflare Tunnel 官方文档为准，不凭旧版本记忆推断。
5. 重点检查：compose.yml、setup.ps1、start.ps1、stop.ps1、status.ps1、backup.ps1、nginx/default.conf、.env.production.example、docs/RESTORE.md。
6. 特别验证 PowerShell 5.1 语法、Compose profile 与 env interpolation、tootctl 命令、VAPID/加密密钥生成、named volumes、Nginx HTTPS/真实 IP/WebSocket 头、Cloudflare origin 路由、备份和恢复命令。
7. 最多输出 10 项，按 P0/P1/P2 排序。每项必须包含：文件和行/片段、实际失败方式、最小修改方案、依据。
8. 纯风格问题和“可以更完善”的建议不要报告。
9. 如果没有 P0/P1，请明确写：可进入首次真实部署；剩余风险只能通过一次运行 smoke 验证。

最后单独回答：
- 是否存在会让 iOS Mastodon App 无法完成实例发现或 OAuth 的配置？
- 是否存在会让图片上传后丢失或处理失败的配置？
- 是否存在一次重启后数据库/媒体丢失的风险？
- backup.ps1 + RESTORE.md 是否形成可恢复闭环？
```

## 如何处理审计结果

只接受两类修改：

- P0：会丢数据、泄露密钥、破坏身份或导致明显安全事故。
- P1：会直接阻断首次部署、iOS 登录、发图或 streaming。

P2 先记录，不在第一次部署前继续加复杂度。

Claude 的输出应贴回当前对话，由现有方案负责人逐条核对；不要让 Claude 自动修改仓库。

## 为什么只做一次

仓库已经有静态审计和一次 smoke 脚本。第二模型的价值是独立发现盲点，而不是制造另一套架构。审计完成后直接进入真实部署；真实容器输出比继续进行第三轮文本审查更有价值。
