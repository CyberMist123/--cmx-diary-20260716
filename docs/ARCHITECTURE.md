# PI OS 架构说明

## 一句话

PI OS 不是重新开发社交平台，而是把原版 Mastodon 当作稳定的“朋友圈内核”，再用 Docker 管理依赖、Nginx 统一入口、Cloudflare Tunnel 让手机从外网安全访问。

## 请求如何流动

```text
iOS Mastodon App
        │ HTTPS / OAuth / API / WebSocket
        ▼
Cloudflare Edge
        │ 已加密 Tunnel，不开放家庭路由器端口
        ▼
cloudflared 容器
        │ HTTP: nginx:80
        ▼
Nginx 容器
   ├─ 普通网页、OAuth、REST API ──→ Mastodon Web :3000
   └─ /api/v1/streaming ─────────→ Mastodon Streaming :4000
```

Nginx 必须存在，因为 Mastodon 的普通网页/API 与实时 streaming 是两个独立进程。Cloudflare 只连接 Nginx，Nginx 再按路径分流。

## 各容器做什么

### `web`

Mastodon 的 Rails Web 服务：

- 登录与 OAuth。
- 时间线和动态 API。
- 账号、设置、后台管理。
- 页面和静态资源。
- 图片上传请求的接收。

### `streaming`

Mastodon 的 Node.js streaming 服务：

- 实时时间线更新。
- 通知和 WebSocket/SSE 类长连接。
- 避免手机每次都靠轮询刷新。

### `sidekiq`

后台任务执行器：

- 图片处理与缩略图。
- 通知、邮件和异步任务。
- 未来 Bot 或联邦任务也会经过后台队列。

没有 Sidekiq 时，网页可能能开，但发图、通知等功能会出现延迟或卡死。

### `db`

PostgreSQL，保存真正的结构化世界：

- 账号。
- 动态正文。
- 点赞、评论、关系和设置。
- 媒体元数据。

数据库使用 Docker named volume，避免 PostgreSQL 直接跑在 Windows NTFS bind mount 上带来的性能和权限问题。

### `redis`

保存缓存、队列状态和实时服务需要的短期数据。它不是主要历史档案，真正需要长期恢复的核心仍是 PostgreSQL、媒体和密钥。

### `nginx`

唯一的内部 Web 入口：

- 把普通请求转给 `web:3000`。
- 把 streaming 路径转给 `streaming:4000`。
- 保留公网 HTTPS、真实客户端 IP 和 WebSocket 所需的请求头。
- 将本机调试入口限制在 `127.0.0.1:8080`。

### `cloudflared`

从家中电脑主动连接 Cloudflare：

- 家庭路由器不需要端口映射。
- 家庭公网 IP 不直接暴露。
- 公网 HTTPS 由 Cloudflare 处理。
- Tunnel token 只保存在本机 `.env`。

## 数据分层

```text
Docker named volume
├─ pi-os_postgres_data   数据库
└─ pi-os_redis_data      Redis 持久化

项目目录 D:\AI\PI-Personal-Instance-OS
├─ data\media            上传的图片和视频
├─ backups               数据库导出、媒体归档和密钥快照
├─ .env                  Docker / Tunnel 密钥
└─ .env.production       Mastodon 身份与加密密钥
```

GitHub 只保存“如何建造世界”，不保存这个世界的真实内容。

## 为什么不 fork Mastodon

当前需求是稳定使用，不是开发新的社交网络内核。直接使用官方容器意味着：

- 不需要维护 Ruby、Node 和前端源码构建链。
- 安全更新可以通过更换镜像版本完成。
- 自己的 Bot 和未来主题可以放在外层，不污染核心。
- 部署失败时，问题范围只剩配置、网络和存储。

## 私密边界

Mastodon 配置为：

- 关闭公开注册。
- `LIMITED_FEDERATION_MODE=true`，只允许明确批准的外部实例。
- `DISALLOW_UNAUTHENTICATED_API_ACCESS=true`，未登录者不能通过普通 API 查看动态。
- AI/Bot 将来只使用独立账号和 API Token，不直接读取 PostgreSQL。

这提高了控制权，但不是端到端加密。Cloudflare、服务器系统和拥有管理员权限的人仍处在信任边界内。

## 故障影响

- 家中断网：手机暂时无法访问，数据仍在本机。
- Cloudflare Tunnel 断开：公网入口失效，本机数据不受影响。
- Web 容器挂掉：登录和 API 不可用。
- Streaming 挂掉：网页可能能用，但实时更新异常。
- Sidekiq 挂掉：图片处理和异步通知积压。
- PostgreSQL 丢失：动态和账号主体丢失，必须从备份恢复。
- `.env.production` 加密密钥丢失：部分加密数据可能无法恢复，因此它与数据库同等重要。

## 当前停止线

Beta 只验证：启动、手机 OAuth、文字/图片发布、时间线、通知、重启恢复和一次备份。

Bot、AI 接入、主题、独立朋友圈前端和更复杂权限都属于后续独立增量。
