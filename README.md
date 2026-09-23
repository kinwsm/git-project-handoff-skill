# Git Project Handoff

让 ChatGPT 读取 GitHub 上的项目文档并整理任务，由本地 Codex 执行、验证，再把结果送回同一个交接文件。

> **适用范围**：这是一个 Codex skill，提供协作步骤和判断规则。它需要你已经为项目配置好 GitHub 连接和本地监听器；安装 skill 本身不会创建连接或启动监听器。

```text
ChatGPT 讨论与读取项目快照
          ↓ 仅将明确的任务写入 HANDOFF.md
GitHub 项目仓库
          ↓ 已登记的本地监听器
Codex 核对本地项目、执行与验证
          ↓ 回写同一请求的结果
ChatGPT 直接读取回执并复核
```

## 一次交接会怎样进行

1. 聊天读取仓库中已推送的项目文档，确定目标与验收条件。
2. 聊天检查 `HANDOFF.md` 的当前版本和请求 ID，追加一条 `pending` 请求。
3. 本地监听器识别新请求，唤醒 Codex。Codex 重新核对本地工作树和项目权限，完成获准工作。
4. 监听器回写任务 ID、状态和执行结果。聊天读回同一条请求，依据实际结果判断是否验收通过。

例如，你可以先在聊天中说：“阅读已分享的项目说明，讨论文档检查工具的需求；方案确定后，将实现和测试要求交给 Codex。” 任务正文应写清要改什么、允许改哪些文件、怎样验证，以及引用的项目提交。讨论尚未形成执行指令时，保持在聊天阶段即可。

## 安装与调用

将此仓库克隆到 Codex 的个人 skill 目录（该目录如果已有同名 skill，请先处理现有安装）：

**Windows PowerShell**

```powershell
git clone https://github.com/kinwsm/git-project-handoff-skill.git "$env:USERPROFILE\.codex\skills\git-project-handoff"
```

**macOS / Linux**

```bash
git clone https://github.com/kinwsm/git-project-handoff-skill.git ~/.codex/skills/git-project-handoff
```

重启 Codex，让它发现新 skill。之后可以在任务中写 `$git-project-handoff`，或描述“让 ChatGPT 讨论并通过 Git 交接给 Codex 执行”。本仓库根目录就是 skill 目录，入口是 [`SKILL.md`](SKILL.md)。

## 使用前需要具备

- 聊天端具有实际可用的 GitHub 项目读取能力，并按项目约定只在专用交接文件中提交请求。
- 项目仓库只分享获准公开给该仓库读者的文件；聊天看到的是**已推送版本**。
- 本机已经登记该项目仓库、交接文件与工作目录，并运行可信的监听器和 Codex 执行桥。
- 项目自身的授权、数据范围和测试规则仍然生效。交接文档不能扩大这些权限。

此仓库只发布 skill 指引，不包含监听器程序、账号连接配置或任何项目数据。若缺少上述连接，skill 会指出缺口，不会宣称任务已派发。GitHub App 可能拥有比协作约定更宽的权限；“项目文件只读”是工作规则，不能当作 OAuth 强制限制。

## 关键规则

- 用唯一请求 ID 去重；更新前读取完整 `HANDOFF.md` 和当前 blob SHA，防止并发覆盖。
- 写入结果不明时先核对远端状态，不换 ID 重发。
- `accepted` 只是接收，`completed` 只是执行轮次结束；最终验收需要实际结果和验证证据。
- Codex 根据本地文件与项目规则执行；不把 Git 快照当作未推送工作树的现状。
- 交接和回执中不放凭据、私人资料或未经批准共享的内容。

具体字段和恢复规则见 [`references/protocol.md`](references/protocol.md)。

## 项目文件

| 文件 | 作用 |
|---|---|
| [`SKILL.md`](SKILL.md) | Codex 何时使用 skill、怎样完成交接 |
| [`references/protocol.md`](references/protocol.md) | 请求字段、去重、故障恢复与验收证据 |
| [`agents/openai.yaml`](agents/openai.yaml) | Codex 中的显示名称与简述 |

当前版本已通过 Codex skill 结构校验，并依据一次私有项目的完整往返验收整理。其他项目需要各自配置和验证。
