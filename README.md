# Git Project Handoff

**ChatGPT 读项目资料、讨论方案；Codex 在本机执行和验证；GitHub 交接文档保存请求与回执。**

V2 将这条链路整理为可复现的工作流：可调用的 Codex skill、可配置的本地监听器、交接文档模板、只读预检和离线验证都在本仓库。V1 的说明型版本保存在 Git 标签 [`v1`](https://github.com/kinwsm/git-project-handoff-skill/tree/v1)。

```text
ChatGPT → 读取已分享的项目文档 → 写 HANDOFF.md 的 pending 请求
                                      ↓
GitHub 共享仓库 ────────────────→ 本地监听器（去重、核验版本）
                                      ↓
Codex 本地执行与验证 ──────────→ 回执写回 HANDOFF.md
                                      ↓
ChatGPT 读取同一条回执并核对结果
```

## 从哪里开始

1. 阅读 [复现工作流](WORKFLOW.md)，确认 Python、GitHub CLI、Codex CLI 与 ChatGPT GitHub 连接已可用。
2. 复制 [`config.example.json`](examples/config.example.json)，登记允许监听的仓库和本地项目目录。
3. 把 [`HANDOFF.example.md`](examples/HANDOFF.example.md) 放进该项目的共享仓库。运行 `python runtime/git_handoff.py --check --config config.json` 做只读预检。
4. 运行 `python runtime/git_handoff.py --run --config config.json`，先用文档中的“不改文件”任务验收一次聊天 → Codex → 聊天往返。

当前公开包已包含运行代码；**GitHub 和 ChatGPT 的账号连接、项目共享范围以及本地 Codex 登录仍由使用者配置**。监听器默认只接受私有项目仓库，公开仓库需要显式开启。监听器只处理登记仓库的专用交接文档，不会上传本地项目资料。需要人工审批的工作应在 Codex 界面中处理。

## 这个工作流解决什么

当项目讨论和本地修改分属两个窗口时，交接文档保存一条任务的依据版本、唯一 ID、目标、验收标准与执行回执。聊天读取的是 GitHub 上已推送的项目快照；Codex 执行前重新核对本地工作树。写入不明时先查远端，避免重复派发。`completed` 表示执行轮次结束，实际验收仍看结果和验证证据。

例如，你可以在 ChatGPT 中先说：“读取我已分享的项目说明，比较两个实现方案。”方案确定后再说：“把选定方案、允许修改的路径和验收条件写进 `HANDOFF.md`，由本地 Codex 执行。”第一个请求留在聊天阶段，第二个才触发本地执行。

## 版本与文件

| 内容 | V1（标签 `v1`） | V2（当前） |
|---|---|---|
| Codex skill 与交接规则 | 有 | 有 |
| 本地监听器与 Codex app-server 执行桥 | 无 | `runtime/` |
| 项目配置与交接模板 | 无 | `examples/` |
| 复现步骤、只读预检、离线验证 | 无 | [`WORKFLOW.md`](WORKFLOW.md)、`tests/` |

[`SKILL.md`](SKILL.md) 是 Codex 入口；[协议参考](references/protocol.md)规定请求格式与恢复语义。本地 `config.json`、状态账本和日志由 `.gitignore` 排除。原私有项目、凭据和运行数据没有进入公开仓库。

## 当前验证范围

V2 运行代码从 Windows 上已完成真实 ChatGPT→GitHub→Codex→GitHub→ChatGPT 往返的本地实现整理而来。公开包会运行离线测试和只读预检；新的项目必须按 [工作流](WORKFLOW.md)自己完成一次真实往返，才能声称它的连接已打通。macOS/Linux 的执行逻辑包含文件锁支持，但尚未做真实往返验收。
