# RFC：固定内部身份 + 可替换 CMX 访问域名

> 状态：**仅供审核，尚未实施。** 当前仓库仍是单域名部署模型，在本 RFC 审核、落地前不要运行 `setup.ps1`。

## 1. 背景与真实需求

PI OS 是个人使用的 CMX 网页系统，不使用 Mastodon App，不接入公开联邦宇宙，也不要求外部实例识别本地账号。

实际需要长期保存的是：

- PostgreSQL 中的账号、动态、关系和设置；
- `data/media` 中的图片与视频；
- `.env.production` 中的加密密钥；
- CMX 的网页功能和本地 API 行为。

公网域名只承担“手机浏览器当前从哪里进入”的作用。用户可能每年更换低价域名，因此不希望公网访问域名成为不可替换的数据身份。

## 2. 目标

将 Mastodon 的两个域名角色拆开：

```env
# 永久固定，只作为 Mastodon 内部账号/实例身份锚点
LOCAL_DOMAIN=pi.invalid

# 当前手机浏览器访问 CMX/Mastodon 的公网门牌，可以更换
WEB_DOMAIN=pi.ler428.xyz

# 显式绑定实时连接到当前公网门牌
STREAMING_API_BASE_URL=wss://pi.ler428.xyz

# 域名切换时短期放旧门牌；正常运行时尽量为空
ALTERNATE_DOMAINS=
```

`pi.invalid` 使用保留的 `.invalid` 后缀，不需要 DNS，不会被其他人注册。它不会作为手机访问地址。

公网链路：

```text
手机浏览器
   │ HTTPS
   ▼
当前 WEB_DOMAIN
   ▼
Cloudflare Named Tunnel
   ▼
cloudflared → nginx:80
                  ├─ CMX 网页
                  ├─ Mastodon Web / OAuth / REST API
                  └─ /api/v1/streaming → Mastodon Streaming
```

## 3. 为什么理论上可行

Mastodon 原生区分：

- `LOCAL_DOMAIN`：本地账号与实例在联邦语义中的身份域名；
- `WEB_DOMAIN`：真正承载网页、登录、邮件链接和 streaming 的域名；
- `ALTERNATE_DOMAINS`：允许额外 Host 被识别为本机域名。

Mastodon 初始化器将 `LOCAL_DOMAIN` 和 `WEB_DOMAIN` 分别写入 `config.x.local_domain` 与 `config.x.web_domain`，并默认从 `WEB_DOMAIN` 生成 HTTPS 页面和 streaming 地址。

官方警告不要更换 `WEB_DOMAIN`，主要针对远程联邦服务器已经记住旧 ActivityPub URL/账号映射的场景。本项目明确不联邦、不向外迁移账号、不依赖外部 WebFinger，因此提出将公网门牌作为可替换层。

这仍然是偏离官方支持路径的私有部署策略，必须在首次正式写入数据前审核和 smoke。

## 4. CMX 前端约束

CMX 必须按照“同源、无硬编码域名”实现：

- REST 请求使用相对地址，例如 `/api/v1/timelines/home`；
- 图片、头像和附件优先使用后端返回值，不自行拼接旧域名；
- streaming 地址从当前页面 origin 或后端实例元数据取得，不写死域名；
- OAuth redirect URI、登出回跳、CSRF trusted origin 不得硬编码旧域名；
- 本地配置中唯一允许变化的公网门牌是 `WEB_DOMAIN`；
- 不把 `LOCAL_DOMAIN=pi.invalid` 当成可访问 URL。

如果 CMX 使用 Mastodon OAuth 而非同源网页登录，域名切换时需要重新注册/更新 OAuth redirect URI。应优先设计为可根据当前 origin 自动注册或更新，而不是把旧域名写入源码。

## 5. 首次部署（拟议流程）

审核通过后修改部署包：

1. `setup.ps1` 参数从单一 `-Domain` 改为：

   ```powershell
   .\setup.ps1 -AccessDomain "pi.ler428.xyz"
   ```

2. 脚本固定写入：

   ```env
   LOCAL_DOMAIN=pi.invalid
   WEB_DOMAIN=pi.ler428.xyz
   STREAMING_API_BASE_URL=wss://pi.ler428.xyz
   ALTERNATE_DOMAINS=
   ```

3. Cloudflare Tunnel 的 Public Hostname：

   ```text
   pi.ler428.xyz → http://nginx:80
   ```

4. 初始化 PostgreSQL、Redis、Owner、密钥和媒体目录；关闭注册与联邦。
5. 启动 Web、Streaming、Sidekiq、Nginx、cloudflared。
6. 手机浏览器访问 CMX 网页并验证：
   - 登录；
   - 发文字；
   - 发图片并生成缩略图；
   - 刷新时间线；
   - streaming/通知；
   - 重启后恢复。

## 6. 日常运行

正常情况下：

```powershell
.\start.ps1
.\stop.ps1
.\status.ps1
.\backup.ps1
```

`LOCAL_DOMAIN`、数据库、媒体目录和所有加密密钥永不变。

CMX 日常只通过当前 `WEB_DOMAIN` 访问；不需要 Tailscale，也不依赖手机 VPN 状态。

## 7. 每年更换公网域名（拟议两阶段切换）

计划新增：

```powershell
.\change-access-domain.ps1 -NewDomain "pi.new-domain.xyz"
```

脚本不能直接粗暴替换，应执行两阶段切换。

### 阶段 A：让新旧域名同时可用

1. 运行完整备份。
2. 用户先在 Cloudflare Tunnel 添加：

   ```text
   pi.new-domain.xyz → http://nginx:80
   ```

3. 将新域名暂时加入 `ALTERNATE_DOMAINS`。
4. recreate Web/Streaming/Sidekiq，使新 Host 被 Rails 接受。
5. 从新域名验证健康页、登录页、API、媒体和 streaming。

### 阶段 B：正式切换

验证新域名成功后：

```env
LOCAL_DOMAIN=pi.invalid
WEB_DOMAIN=pi.new-domain.xyz
STREAMING_API_BASE_URL=wss://pi.new-domain.xyz
ALTERNATE_DOMAINS=pi.old-domain.xyz
```

然后 recreate Web/Streaming/Sidekiq，并从新域名重新登录。

旧域名只保留短期过渡。旧域名到期或删除 Cloudflare route 前，应从 `ALTERNATE_DOMAINS` 移除，避免长期接受废弃 Host。

## 8. 换域名时预期会失效的内容

允许失效：

- 旧域名书签和手工复制的绝对链接；
- 旧域名浏览器 Cookie/登录会话；
- 旧 origin 的 Web Push 授权与订阅；
- 绑定旧 origin 的 WebAuthn/passkey；
- 写死旧 redirect URI 的 OAuth application；
- CMX 的旧缓存或 Service Worker。

必须保持：

- PostgreSQL 主体数据；
- 媒体文件；
- Owner 密码与 TOTP；
- `LOCAL_DOMAIN=pi.invalid`；
- `SECRET_KEY_BASE`、`OTP_SECRET`、`ACTIVE_RECORD_ENCRYPTION_*`、VAPID key；
- 动态正文、时间线关系和本地账号主键。

因此首版不建议启用 WebAuthn/passkey；换域名后需要清理 CMX Service Worker、重新登录并重新允许网页通知。

## 9. 需要审核的高风险问题

请审核者重点回答：

1. Mastodon v4.6.3 是否允许不可解析的 `LOCAL_DOMAIN=pi.invalid` 与真实 `WEB_DOMAIN` 组合完成建库、创建账号、网页登录、REST、媒体和 streaming？
2. 哪些数据库字段会持久化包含 `WEB_DOMAIN` 的绝对 URL，而不是每次动态生成？换域名后是否需要最小 SQL/rails runner 修复？
3. 本地 status/account/media 的 `uri`、`url`、OAuth application、Web Push、WebAuthn、Active Storage/Paperclip 路径中，哪些会残留旧域名？
4. `ALTERNATE_DOMAINS` 是否足够支持切换前新旧 Host 并行，还是还需要 Nginx/CORS/CSP/CSRF 配置？
5. CMX 若同源调用 Mastodon API，推荐使用网页 Session 还是 OAuth PKCE？哪一种在每年更换 `WEB_DOMAIN` 时修改量最小？
6. `STREAMING_API_BASE_URL` 是否应显式设置并随 `WEB_DOMAIN` 更新？
7. 切换 `WEB_DOMAIN` 后是否必须 recreate `web`、`streaming`、`sidekiq`，还需要处理哪些进程？
8. 不接联邦的前提下，官方所说“WEB_DOMAIN 不可安全更改”的剩余本地风险有哪些？
9. 是否存在域名切换导致旧媒体不可访问或新上传文件写入不同路径的风险？
10. 如何设计最小 smoke，证明换域名后数据未迁移、网页功能仍完整？

## 10. 审核边界

- 只评估本 RFC 的可行性和 P0/P1 风险；
- 不建议购买长期域名、Tailscale、VPS、Kubernetes、S3 或公共联邦；
- 不修改仓库；
- 不扩展 Bot、AI、主题或 CMX 功能；
- 明确区分“官方不支持”与“在无联邦、单用户场景会实际失败”；
- 每项问题给出源码/官方文档依据和最小修正。

## 11. 当前停止线

本 RFC 审核通过前：

- 不运行当前 `setup.ps1`；
- 不用 `pi.ler428.xyz` 初始化现有单域名版本；
- 不修改数据库；
- 不让 Codex 或 Claude 自动改代码。

通过后再一次性修改：env 模板、setup、status、Cloudflare 文档、恢复文档、AI_HANDOFF，并新增 `change-access-domain.ps1`。