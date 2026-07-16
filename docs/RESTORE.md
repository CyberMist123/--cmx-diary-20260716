# PI OS 恢复

恢复依赖同一组：数据库、上传媒体、`.env`、`.env.production`。

不要在恢复时更换 `LOCAL_DOMAIN`，也不要重新生成 secrets。

下面假设快照位于：

```text
backups\pi-os-YYYYMMDD-HHMMSS
```

## 1. 停止应用

```powershell
.\stop.ps1
```

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

快照使用 `-SkipMedia` 创建时，这一步不可用。

## 4. 恢复 PostgreSQL

只启动数据库：

```powershell
docker compose up -d db redis
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
  "/backups/pi-os-YYYYMMDD-HHMMSS/database.dump"
```

`pg_restore` 可能对已存在的扩展或权限打印非致命警告；真正失败时会返回非零状态。

## 5. 启动并检查一次

```powershell
.\start.ps1
.\status.ps1
```

随后从手机确认旧动态与图片可见。

## 安全提醒

`backup.ps1` 创建的是本地明文快照，其中包含账号密钥、数据库和私人媒体。至少保留一份放在加密磁盘或加密归档中的离线副本。
