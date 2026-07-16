# PI OS 部署

目标：在 Windows 闲置电脑上运行一个私人 Mastodon 实例，通过 Cloudflare Tunnel 供 iOS 客户端访问。

这套仓库不包含 Mastodon 源码，不 fork 上游。运行时直接使用固定版本的官方容器镜像。

## 0. 部署前只确认一次

需要：

- Windows 10/11。
- Docker Desktop，启用 WSL2 backend。
- Git。
- 一个已经托管在 Cloudflare 的最终域名。
- 电脑关闭自动睡眠；Docker Desktop设置为登录后自动启动。

`LOCAL_DOMAIN` 是账号身份的一部分。真正开始使用后不要更换域名。

## 1. 克隆到目标目录

PowerShell：

```powershell
git clone https://github.com/CyberMist123/pi-os.git "D:\AI\个人实例（长毛象+朋友圈 beta）"
Set-Location "D:\AI\个人实例（长毛象+朋友圈 beta）"
```

仓库尚未重命名时，临时使用旧 URL 克隆；仓库改名后 GitHub 通常会继续重定向旧地址。

如果中文、空格或括号导致 Docker 挂载报错，再迁移到 `D:\AI\pi-os`。不提前迁移。

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
- 拉取固定镜像。
- 初始化 PostgreSQL。
- 创建并确认 Owner 账号。
- 关闭公开注册。
- 启动 Mastodon Web、Streaming、Sidekiq、PostgreSQL、Redis 和 Nginx。
- 有 Tunnel token 时同时启动 `cloudflared`。

Owner 创建成功后，Mastodon CLI 会输出一次性初始密码。立即保存。

## 3. 配置 Cloudflare

按 [CLOUDFLARE.md](./CLOUDFLARE.md) 创建 Named Tunnel，并让 public hostname 指向：

```text
http://nginx:80
```

不要指向 `web:3000`，否则实时 streaming 路由会缺失。

主站不要套 Cloudflare Access。Mastodon iOS 客户端需要正常完成 OAuth、API 和 streaming 请求。

## 4. 启停

```powershell
.\start.ps1
.\stop.ps1
```

全部服务使用 `restart: unless-stopped`。Docker Desktop恢复后，容器会自动恢复。

## 5. 唯一一次最终检查

```powershell
.\status.ps1
```

它只做一次 smoke：

- 容器状态。
- Nginx 本地健康。
- Mastodon Web 健康。
- Streaming 健康。
- 已配置 Tunnel 时检查公网域名。
- 检查 Git 是否误追踪 `.env`、数据库、媒体或备份。

脚本通过后，不继续做性能测试或反复审计。

最后在 iOS Mastodon 客户端完成三项人工验收：

1. OAuth 登录。
2. 发布一条文字和一张图片。
3. 刷新时间线并查看通知。

## 6. 本地文件边界

永远不要提交：

- `.env`
- `.env.production`
- `data/`
- `backups/`
- Cloudflare token 或 credentials JSON

部署代码可以公开，实际世界和钥匙只留在本机。

## 7. 今天停止线

完成手机登录、发图、时间线、通知、重启恢复后立即停止。

今天不做：主题、Bot、AI 接入、Cyberlink、520、全文搜索、S3、公共联邦或前端重写。
