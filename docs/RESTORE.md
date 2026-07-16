# PI OS 恢复

恢复依赖同一组：数据库、上传媒体、`.env`、`.env.production`，以及与快照兼容的 Mastodon 镜像版本。

不要在恢复时更换 `LOCAL_DOMAIN`，也不要重新生成 secrets。

下面假设快照位于：

```text
backups\pi-os-YYYYMMDD-HHMMSS
```

## 0. 确认版本

先查看：

```text
backups\pi-os-YYYYMMDD-HHMMSS\mastodon-version.txt
```

恢复时优先使用快照中的 `compose.yml` 或仓库中对应版本的提交。先恢复原版本，确认可用后再按官方 release notes 单独升级；不要在一次操作中同时恢复和跨版本升级。

## 1. 停止应用

```powershell
.\stop.ps1
```

正常的 `down` 不会删除 PostgreSQL / Redis named volumes。不要加 `-v`。

## 2. 恢复配置密钥

从快照复制回仓库根目录：

```powershell
Copy-Item ".\backups\pi-os-YYYYMMDD-HHMMSS\.env" ".\.env" -Force
Copy-Item ".\backups\pi-os-YYYYMMDD-HHMMSS\.env.production" ".\.env.production" -Force
```

确认 `.env.production` 中的 `LOCAL_DOMAIN` 与原实例完全一致。

## 3. 恢复媒体

先清空目标媒体目录，再展开快照：

```powershell
Remove-Item ".\data\media" -Recurse -Force -ErrorAction SilentlyContinue
New-Item ".\data\media" -ItemType Directory -Force | Out-Null
tar.exe -xzf ".\backups\pi-os-YYYYMMDD-HHMMSS\media.tar.gz" -C ".\data\media"
```

快照使用 `-SkipMedia` 创建时，这一步不可用；旧图片和视频不能只靠数据库恢复。

## 4. 恢复 PostgreSQL

只启动数据库：

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

`--exit-on-error` 可以避免恢复一半仍继续运行。若命令失败，先保留现场并查看第一条错误，不要直接启动应用。

## 5. 启动并检查一次

```powershell
.\start.ps1
.\status.ps1
```

随后从手机确认：

- 原账号可以登录。
- 旧动态存在。
- 图片和视频可见。
- 新发一条测试动态后 Sidekiq 与 streaming 正常。

## 6. 新电脑或 Docker 数据盘损坏时

Docker named volume 本身不需要从文件系统复制；只要 `.env`、`.env.production`、数据库 dump 和媒体归档还在，就可以在空 volume 中按上面的流程重建。

`.pi-os-initialized` 只是防误操作标记，不是恢复所需的核心数据。恢复成功后可重新运行一次：

```powershell
@(
  "restored_at=$([DateTime]::UtcNow.ToString('o'))",
  "domain=$((Get-Content .env.production | Where-Object { $_ -match '^LOCAL_DOMAIN=' }) -replace '^LOCAL_DOMAIN=', '')"
) | Set-Content .pi-os-initialized
```

## 安全提醒

`backup.ps1` 会短暂停止 Web、Streaming、Sidekiq 和公网入口，以得到数据库与媒体处于同一时间点的快照；完成后会恢复此前运行状态。

快照仍是本地明文，其中包含账号密钥、数据库和私人媒体。至少保留一份放在加密磁盘或加密归档中的离线副本。
