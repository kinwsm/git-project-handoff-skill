# Git Project Handoff

**让 ChatGPT 读项目、讨论方案；任务确定后交给本地 Codex 执行，结果再回到 GitHub 供聊天复核。**

当一次项目工作既需要充分讨论，又需要在本机修改文件时，这个 Codex skill 规定如何通过项目仓库中的 `HANDOFF.md` 交接任务：记录依据版本、避免重复派发、保留执行回执，并用实际证据判断是否完成。

> **当前可用程度：协作 skill 已可安装；完整链路尚不能只靠下载本仓库启动。** 你还需要 ChatGPT 的 GitHub 连接，以及单独配置的本地监听器和 Codex 执行桥。本仓库暂未发布监听器程序。

```text
ChatGPT 读取已分享的项目文档 → 讨论并写入 HANDOFF.md
                                      ↓
                              本地监听器发现新请求
                                      ↓
                    Codex 核对本地项目、执行并验证
                                      ↓
                     结果写回 Git → ChatGPT 读回
```

## 你可以怎样使用

假设项目的 GitHub 仓库已经授权给聊天端，且本地监听器已登记该项目：

> “先读项目说明，帮我比较两种文档检查方案。决定采用哪一种后，把目标、允许修改的文件和验收条件写入交接文档，请 Codex 在本地实现并验证。”

聊天端按项目版本整理出一条请求。Codex 收到后重新检查本地文件与权限，执行任务，并回写同一请求的结果。聊天端再从 GitHub 读取回执。你可以继续在聊天里讨论方案，同时保留本地执行的任务 ID 和验证证据。

**对已配置好的项目**，这套流程减少了在两个窗口间手动复制任务和结果的步骤。聊天只能看到已推送的项目快照；本地未推送改动仍由 Codex 在执行时核对。

## 安装 skill

本仓库根目录就是 skill 目录。将它克隆到 Codex 的个人 skills 目录：

**Windows PowerShell**

```powershell
git clone https://github.com/kinwsm/git-project-handoff-skill.git "$env:USERPROFILE\.codex\skills\git-project-handoff"
```

**macOS / Linux**

```bash
git clone https://github.com/kinwsm/git-project-handoff-skill.git ~/.codex/skills/git-project-handoff
```

如果已有同名安装，请先处理现有目录。重启 Codex 后，用 `$git-project-handoff` 调用，或直接描述“让 ChatGPT 讨论并通过 Git 交接给 Codex 执行”。入口是 [`SKILL.md`](SKILL.md)。

## 从零搭建还缺什么

| 部分 | 本仓库提供 | 需要另外准备 |
|---|---|---|
| 交接规则与异常处理 | ✅ `SKILL.md` 和协议参考 | — |
| 项目文档与专用 `HANDOFF.md` | — | 建立授权的 GitHub 项目仓库 |
| 聊天端读取及提交请求 | — | 在 ChatGPT 连接 GitHub，并确认目标仓库可访问 |
| 自动唤醒本地 Codex | — | 配置并运行本地监听器与 Codex 执行桥 |
| 本地文件修改和测试 | — | 安装 Codex，按项目规则授权执行 |

**所以，新用户现在可以立即安装和阅读 skill，但不能仅凭这个下载包完成端到端交接。** 未来若发布可复用的监听器、配置向导和独立项目验收，再把本项目称为开箱即用才准确。

## 交接的关键规则

- 新请求使用唯一 ID。写入前读取完整 `HANDOFF.md` 与最新 blob SHA，保留其他请求和回执。
- 写入结果不确定时先核对远端，不换 ID 重发。
- 接收或执行轮次结束都不等于验收通过；检查真实任务、结果和验证证据。
- Codex 以本地工作树和项目授权为准；GitHub 文件是共享快照和交接通道。
- 请求与回执不包含凭据、私人资料或未经批准分享的内容。

详细字段和恢复办法见 [`references/protocol.md`](references/protocol.md)。skill 不能赋予聊天端文件访问权，也不能限制 GitHub App 的 OAuth 权限；项目文件只读是这套协作的使用约定。

## 仓库文件

| 文件 | 作用 |
|---|---|
| [`SKILL.md`](SKILL.md) | Codex 使用 skill 的时机和工作步骤 |
| [`references/protocol.md`](references/protocol.md) | 请求字段、去重、恢复与验收条件 |
| [`agents/openai.yaml`](agents/openai.yaml) | Codex 中显示的名称与简述 |

当前 skill 已通过 Codex 结构校验，协作约定来自一个私有项目的完整往返验收。其他项目需要各自配置和验证。
