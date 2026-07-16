# PI OS 部署

目标：在 Windows 闲置电脑上运行私人 Mastodon 后端，通过 Cloudflare Tunnel 供手机浏览器访问。当前网页由 Mastodon Web 提供；独立 CMX 前端尚未加入。

仓库不包含 Mastodon 源码，不 fork 上游。运行时使用固定版本的官方容器镜像。

## 0. 部署前只确认一次

需要：

- Windows 10/11；
- Docker Desktop，启用 WSL2 backend；
- Git；
- 一个当前可用、已托管在 Cloudflare 的公网域名；
- 电脑关闭自动睡眠；
- 建议给 Docker Desktop 至少 4 GB 内存，并预留 20 GB 以上磁盘。

本项目不把公网门牌当永久身份：

```env
LOCAL_DOMAIN=pi.invalid
WEB_DOMAIN=<当前公网域名>
```

`LOCAL_DOMAIN` 永远不改。以后更换公网门牌必须使用 `change-access-domain.ps1`。

## 1. 克隆到目标目录

```powershell
git clone https://github.com/CyberMist123/PI-Personal-Instance-OS.git "D:\AI\PI-Personal-Instance-OS"
Set-Location "D:\AI\PI-Personal-Instance-OS"
```

路径使用纯英文、无空格，减少 Docker Desktop、WSL2 和 PowerShell 路径兼容问题。

## 2. 先配置 Cloudflare route

按 [CLOUDFLARE.md](./CLOUDFLARE.md) 创建 Named Tunnel，并添加当前网页域名：

```text
pi.ler428.xyz → http://nginx:80
```

主网页域名不要套 Cloudflare Access、Challenge 或 Cache Everything。

## 3. 一次初始化

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1 `
  -AccessDomain "pi.ler428.xyz"
```

脚本只询问：

1. Owner 登录邮箱；
2. Cloudflare Tunnel token；暂时没有可以回车跳过。

脚本会：

- 复制 `.env` 与 `.env.production`；
- 固定写入 `LOCAL_DOMAIN=pi.invalid`；
- 写入当前 `WEB_DOMAIN`、对应的 `STREAMING_API_BASE_URL` 和空的 `ALTERNATE_DOMAINS`；
- 生成数据库密码、Mastodon secrets、加密密钥和 VAPID keys；
- 校验 Compose 并拉取固定镜像；
- 启动 PostgreSQL 与 Redis并初始化数据库；
- 创建、确认、批准并赋予 Owner 角色；
- 关闭公开注册；
- 启动 Web、Streaming、Sidekiq、Nginx 与可选 cloudflared。

Owner 创建成功后，CLI 会输出随机初始密码。**密码只显示一次，也不会写入文件。看到 `New password:` 后立刻保存到密码管理器。**

首次冷启动可能需要几分钟。脚本最多等待约 5 分钟；超时后保留容器和 volume，运行 `status.ps1`，不要删数据重跑。

忘记初始密码且仍能进入本机时：

```powershell
docker compose run --rm --no-deps web `
  bin/tootctl accounts modify owner --reset-password --enable --approve
```

把 `owner` 替换为实际用户名。

## 4. 数据位置

- PostgreSQL：Docker named volume `pi-os_postgres_data`；
- Redis：Docker named volume `pi-os_redis_data`；
- 图片和视频：`data\media`；
- 数据库导出、媒体归档和密钥快照：`backups`；
- 自动启动日志：`logs`。

不要运行：

```powershell
docker compose down -v
```

`-v` 会删除数据库 volume。正常停止只使用 `stop.ps1`。

## 5. 启停

```powershell
.\start.ps1
.\stop.ps1
```

全部服务使用 `restart: unless-stopped`。Docker Desktop 恢复后，容器会自动恢复。

## 6. 唯一一次基础检查

```powershell
.\status.ps1
```

它检查：

- `LOCAL_DOMAIN` 是否仍为 `pi.invalid`；
- `WEB_DOMAIN` 与 streaming URL 是否一致；
- 容器、Nginx、Web、Streaming、Sidekiq；
- 当前公网门牌与 Tunnel；
- `/api/v2/instance` 是否报告 `domain=pi.invalid`；
- 公网 streaming 路由；
- Git 是否误追踪运行数据与密钥。

脚本通过后，在手机浏览器打开：

```text
https://pi.ler428.xyz
```

人工验收：

1. 使用密码/TOTP登录；
2. 发布文字；
3. 发布一张图片并等待缩略图；
4. 刷新时间线并确认实时更新；
5. 重启服务后重新登录并读取旧内容。

当前不使用 Mastodon App，也不需要第三方 App OAuth。

## 7. 首次备份和自动启动

手机验收通过后：

```powershell
.\backup.ps1
```

把至少一份快照移到加密离线位置。

然后双击：

```text
安装开机自启.bat
```

或运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\install-autostart.ps1
```

计划任务 `PI-OS-Autostart` 会在当前 Windows 用户登录后：

1. 必要时启动 Docker Desktop；
2. 最多等待 Docker 5 分钟；
3. 运行 `start.ps1`；
4. 等待本地健康检查；
5. 写日志到 `logs\autostart.log`。

这是“用户登录后自动启动”，不承诺无人登录前 Docker Desktop 已运行。

移除自动启动只删除计划任务：

```text
卸载开机自启.bat
```

## 8. 更换公网域名

先在 Cloudflare 为新域名添加同一个 Tunnel route，然后按顺序运行：

```powershell
.\change-access-domain.ps1 -Phase Prepare -NewDomain "pi.new-domain.xyz"
.\change-access-domain.ps1 -Phase Switch  -NewDomain "pi.new-domain.xyz"
```

Prepare 只证明新 Host/TLS/基础 GET 可用。Switch 才会正式改 `WEB_DOMAIN`、同步 streaming、清 Redis 并重建 `web`、`streaming`、`sidekiq`。

Switch 后在新 origin 完整重新登录、读旧内容、发文、发图、检查 streaming，并临时阻断旧域名，确认新页面没有暗中依赖旧 origin。

过渡期结束：

```powershell
.\change-access-domain.ps1 -Phase Release
```

再删除旧 Cloudflare route。详细边界见 [MUTABLE_WEB_DOMAIN_RFC.md](./MUTABLE_WEB_DOMAIN_RFC.md)。

## 9. 邮件边界

Owner 由 CLI 直接确认和批准，因此第一版可以没有 SMTP。

在以下功能启用前必须配置 SMTP：

- 忘记密码邮件；
- 邮箱确认；
- 网页邀请或注册其他真人；
- 系统安全通知。

发件地址必须使用真实域名，不能从 `pi.invalid` 推导。

## 10. 本地文件边界

永远不要提交：

- `.env`；
- `.env.production`；
- `.pi-os-initialized`；
- `data/`；
- `backups/`；
- `logs/`；
- Cloudflare token 或 credentials JSON。

## 11. 给下一位 AI

先读根目录 [PROJECT.md](../PROJECT.md)，再读 [AGENTS.md](../AGENTS.md)。不要重新扫描整个项目，也不要在没有运行输出时声称部署成功。

## 12. 停止线

基础验收完成后停止扩范围。当前不开发独立 CMX、AI/MCP、主题、全文搜索、S3、公共联邦或其他基础设施。