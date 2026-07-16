# PI OS 部署

目标：在 Windows 闲置电脑上运行一个私人 Mastodon 实例，通过 Cloudflare Tunnel 供 iOS 客户端访问。

这套仓库不包含 Mastodon 源码，不 fork 上游。运行时直接使用固定版本的官方容器镜像。

## 0. 部署前只确认一次

需要：

- Windows 10/11。
- Docker Desktop，启用 WSL2 backend。
- Git。
- 一个已经托管在 Cloudflare 的最终域名。
- 电脑关闭自动睡眠；Docker Desktop 设置为登录后自动启动。
- 建议至少给 Docker Desktop 4 GB 内存，并预留 20 GB 以上可用磁盘空间。

`LOCAL_DOMAIN` 是账号身份的一部分。真正开始使用后不要更换域名。

## 1. 克隆到目标目录

PowerShell：

```powershell
git clone https://github.com/CyberMist123/PI-Personal-Instance-OS.git "D:\AI\PI-Personal-Instance-OS"
Set-Location "D:\AI\PI-Personal-Instance-OS"
```

路径已使用纯英文、无空格，避免 Docker Desktop、WSL2 和 PowerShell 的路径兼容问题。

## 2. 一次初始化

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

脚本只询问：

1. 最终域名，不带 `https://`。
2. Owner 登录邮箱。
3. Cloudflare Tunnel token；暂时没有可以直接回车跳过。

脚本会：

- 复制本地 `.env` 与 `.env.production`。
- 生成数据库密码、Mastodon secrets、加密密钥和 Web Push VAPID keys。
- 校验 Compose 配置并拉取固定镜像。
- 启动 PostgreSQL 与 Redis。
- 初始化数据库。
- 创建并确认 Owner 账号。
- 关闭公开注册。
- 启动 Mastodon Web、Streaming、Sidekiq、Nginx，以及可选的 `cloudflared`。

Owner 创建成功后，Mastodon CLI 会输出一次性初始密码。立即保存。

## 3. 数据放在哪里

为了避免 PostgreSQL 在 Windows NTFS bind mount 上出现明显性能下降或权限问题：

- PostgreSQL：Docker named volume `pi-os_postgres_data`。
- Redis：Docker named volume `pi-os_redis_data`。
- 上传图片和视频：项目目录 `data\media`。
- 数据库导出、媒体归档和密钥快照：项目目录 `backups`。

named volume 仍然存放在本人电脑的 Docker Desktop / WSL2 数据盘中，不在云端。不要运行：

```powershell
docker compose down -v
```

`-v` 会删除数据库 volume。正常停止只使用 `stop.ps1`。

## 4. 配置 Cloudflare

按 [CLOUDFLARE.md](./CLOUDFLARE.md) 创建 Named Tunnel，并让 public hostname 指向：

```text
http://nginx:80
```

不要指向 `web:3000`，否则实时 streaming 路由会缺失。

主站不要套 Cloudflare Access。Mastodon iOS 客户端需要正常完成 OAuth、API 和 streaming 请求。

## 5. 启停

```powershell
.\start.ps1
.\stop.ps1
```

全部服务使用 `restart: unless-stopped`。Docker Desktop 恢复后，容器会自动恢复。

注意：Docker Desktop 通常需要 Windows 用户登录后才启动；闲置电脑在无人登录的状态下重启，不等于服务已经恢复。

## 6. 唯一一次最终检查

```powershell
.\status.ps1
```

它只做一次 smoke：

- 容器状态。
- Nginx 本地健康。
- Mastodon Web 健康。
- Streaming 健康。
- 已配置 Tunnel 时检查公网入口、Mastodon API discovery 和公网 streaming 路由。
- 检查 Git 是否误追踪 `.env`、数据库、媒体、初始化标记或备份。

脚本通过后，不继续做性能测试或反复审计。

最后在 iOS Mastodon 客户端完成三项人工验收：

1. OAuth 登录。
2. 发布一条文字和一张图片。
3. 刷新时间线并查看通知。

## 7. 邮件边界

第一版 Owner 账号由 CLI 直接确认，因此可以没有 SMTP。

但在以下功能启用前必须配置 SMTP：

- 忘记密码邮件。
- 邮箱确认。
- 通过网页邀请或注册其他真人账号。
- 系统安全通知。

没有 SMTP 时，不要把唯一 Owner 密码弄丢。也可以通过本机 `tootctl accounts modify --reset-password` 恢复，但这要求仍能进入服务器。

## 8. 本地文件边界

永远不要提交：

- `.env`
- `.env.production`
- `.pi-os-initialized`
- `data/`
- `backups/`
- Cloudflare token 或 credentials JSON

部署代码可以公开，实际世界和钥匙只留在本机。

## 9. 停止线

完成手机登录、发图、时间线、通知、重启恢复后立即停止。

当前不做：主题、Bot、AI 接入、Cyberlink、520、全文搜索、S3、公共联邦或前端重写。
