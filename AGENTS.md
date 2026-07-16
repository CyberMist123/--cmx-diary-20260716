# PI OS agent guardrails

开始任何编码任务前，先读 `AI_HANDOFF.md`。只在任务需要时再读相关文档；不要重新扫描整个仓库来“重新理解架构”。

## 容易犯错的硬边界

- 不得修改已投入使用的 `LOCAL_DOMAIN`、现有 secrets、Docker named volume 名称或数据路径。
- 不得运行 `docker compose down -v`。
- PostgreSQL / Redis 保持 Docker named volumes；上传媒体保持 `data/media`。
- Cloudflare Public Hostname 保持指向 `http://nginx:80`；主实例域名不套 Cloudflare Access。
- 不把 Bot、主题、AI 系统、监控栈、S3 或其他扩展顺手塞进核心 Compose。
- 不提交 `.env`、`.env.production`、`.pi-os-initialized`、`data/`、`backups/`、`logs/` 或任何 token。
- 代码与 `AI_HANDOFF.md` 冲突时，不要猜；先依据运行证据确认，再同步当前真相。

## 完成任务后的强制收尾

按照 `docs/MAINTENANCE.md` 更新信息。只更新受影响的权威文件，不创建新的 `STATUS.md`、`progress.md`、交接副本或重复总结。

可直接使用 `prompts/finish-task.md` 完成收尾。
