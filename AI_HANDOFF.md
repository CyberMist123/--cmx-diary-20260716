# PI OS — AI 接手说明

这份文件只回答四件事：它是什么、怎么运行、有哪些接口、下一步怎么改。

## 1. 定义

- **PI OS**：私人 Mastodon 实例，不是 AI 聊天系统，也不是公开社交平台。
- **核心目标**：本人手机端稳定登录、发文字和图片、浏览时间线与通知。
- **AI/Bot**：以后只能作为独立账号，通过 Mastodon OAuth/API Token 行动；默认不读全站、不直连数据库。
- **身份锚点**：`.env.production` 中的 `LOCAL_DOMAIN`。实例投入使用后不得更换。
- **真实数据**：PostgreSQL、`data/media`、`.env`、`.env.production`。这些不进入 Git。

## 2. 程序架构

```text
iOS Mastodon App
        │ HTTPS / OAuth / REST / streaming
        ▼
Cloudflare Tunnel
        ▼
cloudflared → nginx:80
                 ├─ 普通请求 → web:3000
                 └─ /api/v1/streaming → streaming:4000

sidekiq     图片处理、通知、异步任务
PostgreSQL  账号、动态、关系、媒体元数据
Redis       缓存、队列和短期状态
data/media  图片和视频文件
```

所有服务由 `compose.yml` 管理。Mastodon 使用固定官方镜像，不 fork 上游源码。

PostgreSQL 容器只接收显式的 `POSTGRES_DB`、`POSTGRES_USER` 和 `POSTGRES_PASSWORD`；Cloudflare Tunnel token 不注入数据库容器。

## 3. 对外与本地接口

### 公网 HTTP

- `https://<domain>/_pi/health`：Nginx/Tunnel 健康检查。
- `https://<domain>/api/v2/instance`：Mastodon 客户端实例发现。
- `https://<domain>/api/v1/streaming/*`：实时通知和时间线。
- 其余 OAuth、REST API 和网页接口均为标准 Mastodon 接口；本项目没有自定义业务 API。

### 本地入口

- `http://127.0.0.1:8080`：仅本机可访问的 Nginx 入口。
- Docker 内部：`web:3000`、`streaming:4000`、`db:5432`、`redis:6379`。
- Cloudflare Public Hostname 必须指向 `http://nginx:80`。

### 运维脚本

- `setup.ps1`：首次初始化；生成密钥、建库、创建已确认且已批准的 Owner、关闭注册并启动；首次冷启动最多等待约 5 分钟。
- `start.ps1`：启动现有实例。
- `stop.ps1`：停止容器，不删除数据。
- `status.ps1`：一次 smoke；检查 Web、Streaming、Sidekiq、公网入口和 Git 安全。
- `backup.ps1`：短暂停应用，导出并验证数据库与媒体归档，再恢复运行状态。Redis 不作为长期快照内容。
- `install-autostart.ps1` / `安装开机自启.bat`：安装登录后自动恢复任务。
- `remove-autostart.ps1` / `卸载开机自启.bat`：移除自动启动，不动容器和数据。

## 4. 当前流程

### 首次部署

```text
clone 到 D:\AI\PI-Personal-Instance-OS
→ setup.ps1
→ 立即保存终端只显示一次的 Owner 密码
→ Cloudflare hostname 指向 nginx:80
→ status.ps1 一次
→ iOS 登录、发文字和图片
→ backup.ps1 一次
→ 双击 安装开机自启.bat
```

如果 Owner 密码丢失但仍能进入本机：

```powershell
docker compose run --rm --no-deps web `
  bin/tootctl accounts modify owner --reset-password --enable --approve
```

### 每次开机

```text
Windows 用户登录
→ 计划任务 PI-OS-Autostart
→ autostart-run.ps1
→ 必要时启动 Docker Desktop
→ 等待 Docker daemon
→ start.ps1
→ 等待本地健康检查
→ 写入 logs/autostart.log
```

这是“开机登录后自动启动”。Docker Desktop 是用户会话程序，不承诺无人登录前运行。

### 发图流程

```text
手机上传
→ Nginx
→ Mastodon Web 写数据库和媒体文件
→ Sidekiq 处理缩略图/异步任务
→ Streaming 推送更新与通知
```

### 备份流程

```text
暂停公网入口、Web、Streaming、Sidekiq
→ PostgreSQL dump 并读回验证
→ 打包媒体并读回验证
→ 保存密钥配置
→ 恢复原运行状态
```

### 恢复流程

```text
恢复 .env / .env.production / PostgreSQL / media
→ FLUSHALL 清空旧 Redis 队列和缓存
→ start.ps1
→ status.ps1
→ 手机确认旧数据和新发图
```

不把 Redis 队列跨快照恢复；同机回滚 PostgreSQL 后必须清空 Redis，避免旧队列和缓存指向不存在的数据。

## 5. 数据位置

```text
Docker named volume
├─ pi-os_postgres_data
└─ pi-os_redis_data

D:\AI\PI-Personal-Instance-OS
├─ data\media
├─ backups
├─ logs
├─ .env
└─ .env.production
```

绝对禁止执行 `docker compose down -v`，它会删除数据库 volume。

## 6. AI 修改规则

接手时先读本文件，再读与任务直接相关的代码和文档。不要为了“全面理解”重新扫描整个项目。

只允许最小改动：

1. 不修改 `LOCAL_DOMAIN`、现有 secrets 或数据目录。
2. 不提交 `.env`、`.env.production`、`data/`、`backups/`、`logs/`。
3. 不把 Bot、主题、AI 系统、监控栈顺手塞进核心 Compose。
4. 修改 Compose 后先跑 `docker compose config --quiet`。
5. 真实部署失败时只修失败点；不要重做架构或重复全量审计。
6. 新增 Bot 时使用标准 Mastodon OAuth/API，独立账号、独立 Token、最小权限，不直连 PostgreSQL。
7. 完成的变更若影响需求、功能、边界、架构、接口名、流程或当前状态，执行 `skills/project-doc-sync/SKILL.md`，原地更新权威文档；不要新增重复交接文件。

## 7. 当前状态与下一步

GitHub 部署包、备份、恢复、一次 smoke、开机登录后自动恢复和项目事实同步 skill 已准备好；Claude 的首次只读审计 P1 已处理：Owner 显式 approve、Redis 回滚策略、数据库容器密钥隔离、首次冷启动等待和密码恢复说明。

尚未在目标电脑完成真实部署。下一步只有：确定最终域名、clone、首次运行、手机验收。通过后停止扩范围。
