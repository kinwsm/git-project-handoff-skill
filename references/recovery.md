# 失败定位与恢复

先看终端 JSON 或 `.handoff-state/status.json` 的 `error_code`，再看远端同一 request_id 的回执。不得通过删除账本、更换 ID 或启动第二个副本绕过不确定状态。

| 信号 | 含义 | 操作 |
|---|---|---|
| `codex_login` | Codex 尚未登录 | 运行 `codex login`，再做 `--check` |
| `github_login` | GitHub 凭据无效 | 用 `gh auth status` 检查并重新登录 |
| `github_permission` | 当前操作被拒绝 | 检查账号、仓库授权和限流；不扩大到无关仓库 |
| `github_not_found` | 文件/仓库/分支错误，或私有资源不可见 | 核对配置、HANDOFF.md 是否已推送、账号授权 |
| `github_conflict` | 文件版本发生并发变化 | 自动有限次重读后再写；仍失败则等待下一轮，不重派任务 |
| `github_rate_limit` / `github_api_error` | 限流或网络/API 故障 | 检查连接并等待恢复；本地结果保留，后续只补写回执 |
| `model_required` | 配置了思考强度但没有模型 | 同时填写模型，或把两项都设为 null |
| `model_unavailable` / `effort_unsupported` | 本账号目录不支持该选择 | 运行 `--models` 并修正配置；此阶段未创建任务 |
| `approval_required` / `user_input_required` | 模型需要审批/用户输入 | 按回执任务 ID 在 Codex 中核对和处理。桥接器不自动同意；不会自动续跑 |
| `execution_failed` / `execution_interrupted` | Codex 轮次失败或中断 | 查看同一任务的实际错误与文件状态，确认是否已有部分结果 |
| `unknown` | 派发结果不确定 | 按本地账本中的 thread_id / turn_id 核对既有任务；没有记录也不能断言未执行 |
| `RuntimeError` / `ValueError` 等 | 协议、文件或接口异常 | 查看本地错误，保持原账本；需要适配时先用隔离验收项目验证 |

初次读取遇到 Codex 会话尚未写入磁盘时，桥接器保持原请求并等待再次读取，不再调用 `turn/start`。`unknown` 会阻挡该项目后续排队请求，以便人工核对。

升级前确认没有活跃任务，停止监听器，备份 `config.json` 与 `.handoff-state/`，再更新源码。新版本会向 SQLite 添加指标列并保留原记录；不要用空账本启动同一个仓库。回滚程序前先保留新账本，已执行的外部动作不能通过还原旧账本撤销。

审批或执行失败不代表模型一定不兼容。所有 `completed` 仍须核对实际文件和测试结果。真实编程验收输出目录包含 HANDOFF.md、evidence.json 和独立测试输出，排错时优先用这些最小证据；分享前删除私人路径和账号信息。
