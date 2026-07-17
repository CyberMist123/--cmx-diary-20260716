# PI OS — 当前项目事实

> **这是本仓库最重要的权威文件。**
>
> 所有 AI、Agent 和维护者开始工作前先读本文件。完成已确认的功能或架构修改后，必须原地更新本文件及受影响的详细文档；不得另建重复的状态、交接或架构摘要。
>
> 最后更新：2026-07-17

## 1. 项目是什么

**PI OS（π / Personal Instance OS）** 是部署在个人 Windows 电脑上的私人生活时间线。

当前用途：

- 日记、碎碎念和生活时间轴；
- 书、电影、音乐与收藏；
- 图片、视频和朋友圈式动态；
- 后续由 AI 以正式居民身份发布博客、日记和状态。

PI OS 与 AI OS 平行存在。动态可以无人回复；AI 不默认分析全部生活，也不是全局监控器。

## 2. 当前产品状态

### 已完成的基础网页 MVP

- 手机浏览器通过 HTTPS 访问，不使用 Mastodon App；
- Mastodon v4.6.3 官方容器作为当前网页和后端；
- Owner 可以登录、发布文字、上传图片、浏览时间线并跨设备同步；
- 公开注册关闭，实例不加入公开联邦；
- PostgreSQL、Redis、媒体与密钥保存在本机；
- Cloudflare Named Tunnel 提供公网入口，家庭路由器不开放入站端口；
- 完整备份已成功生成；
- Windows 重启并登录后，Docker Desktop 与 PI OS 自动启动链路已验证，网页与旧内容恢复正常。

### CMX 网页

独立 CMX 前端尚未实现。未来加入时必须：

- 与 Mastodon 同源部署；
- REST 使用 `/api/v1/...` 等相对路径；
- 使用网页登录 Session/CSRF，或页面派发的当前用户 token；
- streaming、媒体和跳转地址从当前 origin 或后端元数据获得；
- 不在源码中写死公网域名；
- 不注册长期绑定某个公网域名的 OAuth application。

已确认的设置页信息架构：

```text
偏好设置
CMX 设置             ← 当前用户的 CMX 主页、时间线和体验设置

……

邀请用户             ← 真人注册链接
AI 居民              ← AI 身份、权限、MCP 连接和活动管理
开发                 ← 传统 OAuth 应用/API
```

“邀请用户”和“AI 居民”必须分开；“AI 居民”放在“邀请用户”与“开发”之间。

### AI / Bot / MCP

这是已确认的后续需求：

- AI 作为独立正式居民，拥有头像、主页和发布历史；
- 每个 AI 使用独立账号、独立 Token 和可单独撤销的 MCP connection；
- 不直连 PostgreSQL，不使用 Owner Token，不开放 `admin:*`；
- 普通居民功能尽量完整；Reader、Resident、Personal 使用不同能力配置；
- MCP 当前只通过本机 STDIO 接入，不新增公网 MCP route；
- MCP 通过 `http://127.0.0.1:8080` 连接本机 Nginx，同时发送当前 `WEB_DOMAIN` 作为 HTTP Host；
- 媒体由 CC/TG 层和 MCP canonical path 白名单双层约束；
- Token 成本是核心验收项：领域工具、compact 返回、默认小分页、不返回原始大 JSON 或媒体 base64；
- AI 可发布仅自己、指定圈子、实例居民或明确公开的内容；具体 CMX 可见性映射仍待审定；
- 当前基础隐私配置没有匿名互联网公开博客出口，未来必须单独设计只读公开页面和显式权限。

设计分支 `design/ai-resident-mcp` 已加入：

- `docs/AI_RESIDENT_MCP_DESIGN.md`：产品、权限、数据、设置页、工具和实施设计；
- `prototypes/cmx-settings-ai-residents.html`：独立静态设置页原型；
- `cmx-mcp/`：官方 MCP Python SDK + STDIO + Mastodon REST 的可审查代码骨架。

以上均为**已实现/未验证的设计分支原型**，尚未接入当前运行实例，也不代表 CMX 前端已完成。

## 3. 域名模型

```env
LOCAL_DOMAIN=pi.invalid
WEB_DOMAIN=pi.ler428.xyz
STREAMING_API_BASE_URL=wss://pi.ler428.xyz
ALTERNATE_DOMAINS=
```

不变量：

- `LOCAL_DOMAIN` 永远固定为 `pi.invalid`；
- `pi.invalid` 不能被当作可访问 URL；
- PostgreSQL、媒体、密码和加密密钥不随公网域名变化；
- 使用可变 `WEB_DOMAIN` 后，实例永久不加入公开联邦；
- 不对 `statuses.uri` 等历史字段执行全库字符串替换。

可变项：

- `WEB_DOMAIN` 是当前公网门牌，可通过专用脚本替换；
- `STREAMING_API_BASE_URL` 必须与 `WEB_DOMAIN` 同步；
- `ALTERNATE_DOMAINS` 只用于切换期接受额外 Host，不负责 Cookie、CSP、WebAuthn、OAuth、Service Worker 或主 streaming URL 的迁移。

## 4. 当前部署架构

```text
手机 / PC 浏览器
    │ HTTPS
    ▼
当前 WEB_DOMAIN
    ▼
Cloudflare Named Tunnel
    ▼
cloudflared → nginx:80
                 ├─ Web / Session / REST / Media → web:3000
                 └─ /api/v1/streaming           → streaming:4000

sidekiq     图片处理、通知和异步任务
PostgreSQL  账号、动态、关系、设置和媒体元数据
Redis       缓存、Sidekiq 队列和短期状态
data/media  图片和视频文件
```

Cloudflare Public Hostname 必须指向 `http://nginx:80`，主网页域名不能套 Cloudflare Access。

### AI Resident MCP 提案拓扑

```text
Claude Code / Fable / TG Bot
        │ MCP STDIO
        ▼
本机 cmx-mcp
        │ TCP: http://127.0.0.1:8080
        │ Host: 当前 WEB_DOMAIN
        ▼
Nginx → Mastodon REST
        ▼
该 AI 的独立居民账号
```

此拓扑尚未运行验证。当前不增加 Streamable HTTP 或公网 `/mcp`。

## 5. Windows 启动模型

当前采用双层启动，二者共同使用：

```text
Windows 用户登录
→ Docker Desktop 静默启动，拉起 WSL2 / Docker Linux engine
→ PI-OS-Autostart 计划任务等待 Docker 就绪
→ 调用 start.ps1，明确启动 tunnel profile 与全部 PI OS 服务
→ 检查本机健康接口并写入 logs/autostart.log
```

补充边界：

- Compose 中所有服务都有 `restart: unless-stopped`，作为容器级恢复兜底；
- `start.ps1` 必须保留，它是手动启动、计划任务启动、故障恢复和运维流程的统一入口；
- `install-autostart.ps1`、`autostart-run.ps1`、`test-autostart.ps1` 和相关 bat 均为有效运维文件，不是临时规划稿；
- Docker Desktop 自启不能替代 `start.ps1`，计划任务也不能在 Docker engine 未就绪时直接启动容器。

`cmx-mcp` 尚未加入当前启动链路；设计审查和技术 Spike 通过前不得修改生产自启任务。

## 6. 精确接口与运维入口

### 公网接口

- `https://<WEB_DOMAIN>/_pi/health`：Tunnel 与 Nginx 健康检查；
- `https://<WEB_DOMAIN>/api/v2/instance`：实例元数据，`domain` 应为 `pi.invalid`；
- `https://<WEB_DOMAIN>/api/v1/...`：标准 Mastodon REST API；
- `wss://<WEB_DOMAIN>/api/v1/streaming...`：实时更新。

### 本地接口

- `http://127.0.0.1:8080`：仅本机可访问的 Nginx 入口；
- 本地 MCP 访问 Mastodon 时还必须发送当前 `WEB_DOMAIN` 作为 Host；
- `web:3000`、`streaming:4000`、`db:5432`、`redis:6379`：Docker 内部服务。

### 运维脚本

- `setup.ps1 -AccessDomain <domain>`：首次初始化；
- `start.ps1` / `stop.ps1`：启动和停止，不删除数据；
- `status.ps1`：检查容器、本地/公网链路、身份、streaming 和 Git 安全；
- `backup.ps1`：导出并验证 PostgreSQL 与媒体，并恢复原运行状态；
- `install-autostart.ps1` / `安装开机自启.bat`：安装登录后计划任务；
- `test-autostart.ps1`：带可见进度验收自动启动链路；
- `change-access-domain.ps1`：Prepare / Switch / Release 更换公网门牌。

从任意 PowerShell 目录运行状态检查时，必须使用绝对路径：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File "D:\AI\PI-Personal-Instance-OS\status.ps1"
```

或者先进入项目目录：

```powershell
Set-Location "D:\AI\PI-Personal-Instance-OS"
.\status.ps1
```

## 7. 数据所有权与恢复

```text
Docker named volumes
├─ pi-os_postgres_data
└─ pi-os_redis_data

D:\AI\PI-Personal-Instance-OS
├─ data\media
├─ backups
├─ logs
├─ .env
└─ .env.production
```

核心恢复集：PostgreSQL dump、媒体归档、`.env`、`.env.production` 和兼容版本的 `compose.yml`。

Redis 不是长期事实来源。恢复旧 PostgreSQL 快照后必须清 Redis。

绝对禁止 `docker compose down -v`。不得提交密钥、运行数据、日志或备份。

未来 CMX Bot 元数据由 CMX 自有存储管理；它只保存居民绑定、connection、能力、媒体目录和审计元数据，不直接读取 Mastodon PostgreSQL。具体使用 SQLite 或未来 CMX 后端主存储仍待审定。

## 8. 已验证运行事实

2026-07-17，用户明确确认：

- 首次初始化成功；
- 手机和 PC 均可通过当前公网门牌访问并登录；
- 文字发布正常；
- 图片上传、处理和显示正常；
- 手机与 PC 时间线/内容同步正常；
- 无痕窗口确认公开注册关闭；
- `status.ps1` 曾完整通过：身份域名、当前门牌、streaming、容器、本地/公网 health、Sidekiq、Nginx 和 Git safety 均为 OK；
- `backup.ps1` 最终显示 `Backup completed`，首次完整备份成功；
- Windows 重启后网页恢复，旧内容存在，Docker Desktop 静默自启与 PI OS 自定义启动链路可用。

重启后在 `C:\Windows\system32` 使用相对路径 `-File .\status.ps1` 失败，只说明调用目录错误，不代表 PI OS 失败。文档已统一要求绝对路径或先进入项目目录。

AI Resident MCP、CMX 设置页和静态原型均没有目标电脑运行证据，必须保持“已实现/未验证”或“计划中”。

## 9. 功能与进度表

| 项目 | 状态 | 验收证据 |
|---|---|---|
| Docker/Mastodon 核心内容栈 | 已验证 | 实例运行，登录、REST、媒体和跨设备同步正常 |
| 首次本地初始化 | 已验证 | 目标 Windows 电脑真实运行 |
| `status.ps1` 全链路检查 | 已验证 | 身份、门牌、streaming、容器、本地/公网 health 与 Git safety 通过 |
| 手机与 PC 公网网页链路 | 已验证 | 两端均可访问和登录 |
| 文字、图片与时间线同步 | 已验证 | 用户真实发布与跨设备确认 |
| 关闭公开注册 | 已验证 | 无痕窗口确认 |
| 首次完整备份 | 已验证 | 脚本输出 `Backup completed` |
| Windows 重启恢复 | 已验证 | 重启登录后网页和旧内容恢复 |
| Docker Desktop + PI-OS-Autostart | 已验证 | 双层启动后实例恢复可用 |
| 恢复流程 | 已实现/未验证 | 真实 restore 演练以后独立执行 |
| 可替换 `WEB_DOMAIN` | 已实现/未验证 | 脚本和边界已完成，真实年度切换以后演练 |
| 手机 Mastodon 网页日常 MVP | 已验证 | 基础部署阶段完成 |
| CMX 设置导航设计 | 已实现/未验证 | 设计文档和静态 HTML 原型位于 `design/ai-resident-mcp` |
| AI Resident MCP 架构 | 已实现/未验证 | 设计文档已写入分支，待其他 AI 审核 |
| `cmx-mcp` STDIO 原型 | 已实现/未验证 | 9 个领域工具骨架、REST client、compact 输出和媒体守卫已写入；未安装/未运行 |
| CMX Owner Bot API / enrollment | 计划中 | 只有接口和数据模型草案 |
| 独立 CMX 前端 | 计划中 | 当前仍是 Mastodon Web |
| 匿名公开博客出口 | 计划中 | 需独立只读页面和显式许可 |
| 公共联邦 | 永不实施 | 与可变门牌和私人实例边界冲突 |

## 10. 当前下一步

基础部署阶段已经收官。当前产品工作流：

1. 由其他 AI 只读审核 `design/ai-resident-mcp` 分支；
2. 重点验证 Mastodon v4.6.3 endpoint、工具粒度、最小 token scope、可见性映射、账号 provisioning、媒体路径守卫和 enrollment；
3. 根据审查结论原地修订设计和原型；
4. 审查收敛后再决定是否进入 Phase 1 技术 Spike；
5. 未通过审查前不合并到 `main`，不修改当前 Compose、自启或线上页面。

不阻塞当前产品阶段的独立运维演练：

- 真实 restore；
- 年度更换 `WEB_DOMAIN`。

## 11. Agent 更新契约

事实优先级：

1. 用户已确认的需求和边界；
2. 实际代码、配置和运行验证；
3. 本文件；
4. 详细文档；
5. Issue 与历史讨论。

任何任务只要改变需求、边界、架构、接口、数据所有权、运行流程或进度，就必须执行 `skills/project-doc-sync/SKILL.md`：

- 先更新本文件；
- 再更新受影响的详细文档和当前 Issue；
- 删除或替换陈旧描述，不并存两套架构；
- 明确区分“计划中”“已实现/未验证”“已验证”；
- 没有真实输出时不得声称验证成功。
