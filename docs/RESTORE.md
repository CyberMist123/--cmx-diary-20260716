# PI OS 恢复

恢复依赖同一组长期事实：PostgreSQL、上传媒体、`.env`、`.env.production`，以及与快照兼容的 Mastodon 镜像版本。

域名规则：

- `LOCAL_DOMAIN` 必须始终恢复为 `pi.invalid`；
- secrets 和 VAPID keys 必须从快照恢复，不得重新生成；
- 首次恢复优先使用快照中的 `WEB_DOMAIN`；确认实例可用后，再通过 `change-access-domain.ps1` 切换公网门牌；
- 不在恢复过程中同时做跨版本升级或全库 URL 替换。

下面假设快照位于：

```text
backups\pi-os-YYYYMMDD-HHMMSS
```

## 0. 确认版本与配置

查看：

```text
backups\pi-os-YYYYMMDD-HHMMSS\mastodon-version.txt
backups\pi-os-YYYYMMDD-HHMMSS\compose.yml
backups\pi-os-YYYYMMDD-HHMMSS\.env.production
```

确认快照中的：

```env
LOCAL_DOMAIN=pi.invalid
```

恢复时优先使用快照对应版本。先恢复原版本，确认可用后再单独升级。

## 1. 停止应用

```powershell
.\stop.ps1
```

正常 `down` 不会删除 PostgreSQL / Redis named volumes。不要加 `-v`。

## 2. 恢复配置与密钥

```powershell
Copy-Item ".\backups\pi-os-YYYYMMDD-HHMMSS\.env" ".\.env" -Force
Copy-Item ".\backups\pi-os-YYYYMMDD-HHMMSS\.env.production" ".\.env.production" -Force
```

检查：

```powershell
Get-Content .\.env.production | Select-String '^(LOCAL_DOMAIN|WEB_DOMAIN|STREAMING_API_BASE_URL|ALTERNATE_DOMAINS)='
```

必须满足：

```text
LOCAL_DOMAIN=pi.invalid
STREAMING_API_BASE_URL=wss://<WEB_DOMAIN>
```

恢复完成前不要修改 `WEB_DOMAIN`。若旧域名仍可配置，先在 Cloudflare 临时恢复该 route；实例恢复并验收后再走受控切换流程。

## 3. 恢复媒体

```powershell
Remove-Item ".\data\media" -Recurse -Force -ErrorAction SilentlyContinue
New-Item ".\data\media" -ItemType Directory -Force | Out-Null
tar.exe -xzf ".\backups\pi-os-YYYYMMDD-HHMMSS\media.tar.gz" -C ".\data\media"
```

快照使用 `-SkipMedia` 创建时，旧图片和视频不能只靠数据库恢复。

## 4. 恢复 PostgreSQL

只启动数据库和 Redis：

```powershell
docker compose up -d db redis
```

等待数据库健康：

```powershell
docker compose exec -T db pg_isready -U mastodon -d mastodon_production
```

删除并重建空数据库：

```powershell
docker compose exec -T db dropdb -U mastodon --if-exists mastodon_production
docker compose exec -T db createdb -U mastodon mastodon_production
```

从快照恢复：

```powershell
docker compose exec -T db pg_restore `
  -U mastodon `
  -d mastodon_production `
  --no-owner `
  --exit-on-error `
  "/backups/pi-os-YYYYMMDD-HHMMSS/database.dump"
```

失败时保留现场并查看第一条错误，不要直接启动应用。

## 5. 清空旧 Redis 队列与缓存

Redis 不作为跨快照长期事实恢复。同机回滚旧 PostgreSQL 时，原 Redis volume 可能仍含指向新数据或旧 origin 的队列和缓存：

```powershell
docker compose exec -T redis redis-cli FLUSHALL
```

这会丢弃尚未执行的后台任务和缓存，但不会删除 PostgreSQL 中的账号、动态、关系或媒体记录。

## 6. 启动并检查

```powershell
.\start.ps1
.\status.ps1
```

随后从手机浏览器确认：

- 使用密码/TOTP登录；
- 旧账号和动态存在；
- 图片和视频可见；
- 新发文字和图片后 Sidekiq 与 streaming 正常；
- `/api/v2/instance` 的 `domain` 仍为 `pi.invalid`；
- streaming URL 与当前 `WEB_DOMAIN` 一致。

旧 origin 的 Cookie、Service Worker、Web Push 与 WebAuthn 不属于恢复集，需要在当前网页域名重新建立。

## 7. 恢复后更换公网门牌

数据库、媒体和密钥恢复并验收后，才执行：

```powershell
.\change-access-domain.ps1 -Phase Prepare -NewDomain "pi.new-domain.xyz"
.\change-access-domain.ps1 -Phase Switch  -NewDomain "pi.new-domain.xyz"
```

不要修改历史 `statuses.uri`，不要修改 `LOCAL_DOMAIN`。

## 8. 新电脑或 Docker 数据盘损坏

只要 `.env`、`.env.production`、数据库 dump 和媒体归档存在，就能在空 named volume 中重建。

`.pi-os-initialized` 只是防误操作标记。恢复成功后可重建：

```powershell
$identity = ((Get-Content .env.production | Where-Object { $_ -match '^LOCAL_DOMAIN=' }) -replace '^LOCAL_DOMAIN=', '')
$access = ((Get-Content .env.production | Where-Object { $_ -match '^WEB_DOMAIN=' }) -replace '^WEB_DOMAIN=', '')
@(
  "restored_at=$([DateTime]::UtcNow.ToString('o'))",
  "identity_domain=$identity",
  "access_domain=$access"
) | Set-Content .pi-os-initialized
```

## 安全提醒

`backup.ps1` 会短暂停止 Web、Streaming、Sidekiq 和公网入口，以得到数据库与媒体同一时间点的快照；完成后恢复此前运行状态。

快照是本地明文，包含账号数据库、私人媒体、Cloudflare Tunnel token、`SECRET_KEY_BASE`、`OTP_SECRET`、`ACTIVE_RECORD_ENCRYPTION_*` 和 VAPID keys。至少保留一份加密离线副本。