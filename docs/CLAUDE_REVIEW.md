# PI OS 独立只读审计

当前项目已经完成两轮源码级审阅，并把确认的 P0/P1 写入代码与文档。继续审计只用于发现明确阻断，不用于制造第三套架构。

## 审计入口

先读：

1. [`../PROJECT.md`](../PROJECT.md) — 当前权威事实、接口和进度；
2. [`MUTABLE_WEB_DOMAIN_RFC.md`](./MUTABLE_WEB_DOMAIN_RFC.md) — 固定内部身份与可替换公网门牌；
3. 与审计问题直接相关的脚本。

仓库：

```text
https://github.com/CyberMist123/PI-Personal-Instance-OS
```

## 提示词

```text
请对这个仓库做一次只读、保守的部署审计，不修改仓库。

真实环境与边界：
- Windows 10/11 + Docker Desktop WSL2
- 本地目录 D:\AI\PI-Personal-Instance-OS
- Mastodon v4.6.3 / PostgreSQL 14 / Redis 7 / Nginx / Cloudflare Named Tunnel
- 单用户、无公开联邦
- 手机浏览器访问网页，不使用 Mastodon App
- 当前 Mastodon Web；CMX 独立前端尚未实现
- LOCAL_DOMAIN 永久固定为 pi.invalid
- WEB_DOMAIN 是可按受控流程替换的公网门牌
- CMX 将使用同源 Session/CSRF，不使用长期绑定域名的 OAuth application

只报告确定的 P0/P1：
1. 首次 setup 是否会失败、丢密钥、创建不可登录 Owner，或写错 LOCAL_DOMAIN/WEB_DOMAIN。
2. change-access-domain.ps1 的 Prepare/Switch/Release 是否可能造成数据损坏、无法回滚、缓存半新半旧、Sidekiq 丢任务或旧 origin 暗依赖。
3. status.ps1 是否能准确验证 instance.domain=pi.invalid 和 streaming URL=当前 WEB_DOMAIN。
4. PostgreSQL、媒体、备份和恢复是否形成闭环。
5. PowerShell 5.1、Docker Compose profile/env interpolation、Mastodon v4.6.3 tootctl/rails/Redis 命令是否准确。
6. 浏览器 Session、CSRF、CSP、Web Push、WebAuthn、Service Worker 和媒体 URL 在换域名时是否存在未登记的阻断。

严格限制：
- 不建议购买长期域名、Tailscale、VPS、S3、Kubernetes、公共联邦或重写架构。
- 不把计划中的 CMX、AI/MCP 当成已实现代码。
- 不报告风格、可选增强或没有实际失败链路的推测。
- 每项必须包含文件/片段、实际失败方式、最小修复和 Mastodon v4.6.3/官方依据。
- 最多 10 项。
- 若无新 P0/P1，明确写：可进入首次真实部署，剩余风险只能通过目标电脑 smoke 验证。
```

## 处理原则

- 只接受有明确失败链路的 P0/P1；
- 不让审核模型自动修改仓库；
- 相同问题不重复修；
- 没有新 P0/P1 时停止文本审计，进入真实部署；
- 任何已接受修改完成后，执行 `skills/project-doc-sync/SKILL.md` 更新 `PROJECT.md`。