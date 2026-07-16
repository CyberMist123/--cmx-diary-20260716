# PI OS

**π / Personal Instance OS**

一切无规律、不会终结的数字；也是一个属于自己的个人实例。

PI OS 是平行于 AI OS（memory + operation）的私人生活世界。它以动态和时间线为基本单位，不要求每条内容得到回复，也不默认把生活交给 AI 分析。

使用者和读者只有本人以及明确邀请的人。程序、数据库和媒体保存在本地电脑，通过 Cloudflare Tunnel 供 iOS 手机端访问。

用途包括：

- 书影音档案
- 日记与时间轴
- 朋友圈式生活记录
- 心情、碎碎念、图片和收藏
- 以后按需加入拥有独立账号的 Bot 或 AI 居民

AI 与 Bot 不是全局监控器。它们只能通过独立 Mastodon API Token，在明确授权的时间线、提及或标签范围内行动。

## 当前 Beta

底座使用未经魔改的 Mastodon 官方容器：

```text
iOS Mastodon App
        ↓
Cloudflare Named Tunnel
        ↓
Nginx
   ├─ Mastodon Web
   └─ Mastodon Streaming
        ↓
PostgreSQL / Redis / 本地媒体
```

默认关闭公开注册和外部联邦。主站不套 Cloudflare Access，以保证 iOS OAuth、API 和 streaming 正常。

## 部署入口

- [需求与停止线](docs/MVP_SCOPE.md)
- [Windows 一次部署](docs/DEPLOYMENT.md)
- [Cloudflare Tunnel](docs/CLOUDFLARE.md)
- [备份恢复](docs/RESTORE.md)

本地克隆后运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

之后只需要：

```powershell
.\start.ps1
.\stop.ps1
.\status.ps1
.\backup.ps1
```

## 数据边界

仓库只保存部署代码和说明，不保存实际世界。

以下内容永远不得进入 Git：

```text
.env
.env.production
data/
backups/
Cloudflare token / credentials
```

## 初心

希望做一个平行于 AI 系统的个人实例，使用者和读者只有本人和经过邀请的人。

这是自己的书影音档案、日记、朋友圈、时间轴、心情记录与碎碎念。正式的社交平台只需要承担社交和暴露在外的表现欲望（笑）。

需要这样一个自留地让人安心。也相信这样的安全基地、个人实例 OS 能让生活变得更好。正因为外部没有依靠，所以会建造自己的通天塔。❤️
