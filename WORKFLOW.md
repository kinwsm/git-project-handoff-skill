# 复现工作流（V2）

V1 保留在 Git 标签 [`v1`](https://github.com/kinwsm/git-project-handoff-skill/tree/v1)，只提供协作 skill。V2 增加可运行的本地监听器、配置样例、交接模板与离线验证。以下步骤以 Windows PowerShell 为例；运行代码也提供 Unix 文件锁，但 macOS/Linux 的真实 Codex 往返尚未验收。

## 1. 准备条件

- Python 3.11 或更新版本，Git、GitHub CLI (`gh`) 和已登录的 Codex CLI (`codex`) 已在 PATH 中。
- `gh` 可以读取和更新你授权的项目仓库；只有可信协作者可以修改交接文件。可先在终端检查 `gh auth status` 与 `codex --version`。
- ChatGPT 中的 GitHub 连接能对同一个项目仓库执行文件读取和更新。具体可用工具与权限取决于账号连接；若聊天端没有写入该文件的能力，Git 交接不能从聊天端主动触发。
- 选择一个用于共享的项目仓库（建议私有）。只推送允许聊天和该仓库读者查看的工程资料。聊天读到的是已推送快照，不是本地未提交文件。

如果还没有共享仓库，可先用 `gh repo create YOUR_NAME/YOUR_SHARE --private --clone` 建立一个空的私有仓库。只把获准让聊天端读取的文档放进去；`HANDOFF.md` 模板将在下一步复制。已有合适仓库时直接使用原仓库即可。

## 2. 下载并配置本地监听器

```powershell
$skillPath = Join-Path $env:USERPROFILE '.codex\skills\git-project-handoff'
git clone https://github.com/kinwsm/git-project-handoff-skill.git $skillPath
Set-Location $skillPath
Copy-Item examples/config.example.json config.json
```

上述安装跟随 `main` 分支。要精确复现本次维护版，可在克隆时加上 `--branch v2.0.1`；这会停在固定标签，后续需主动选择新标签，不能使用 `git pull` 更新。

已有同名 skill 时，先确认旧目录是否为 Git 克隆；可更新的克隆使用 `git pull --ff-only`，其他安装先保留旧目录再安装。重启 Codex 后，新 skill 才会被发现。

此包的 Python 运行代码只依赖标准库。当前 Windows 实测 Codex CLI 版本为 `0.158.0-alpha.2.1`。其他版本先做下面的可选执行测试。安装后可以在 Codex 中用 `$git-project-handoff` 调用 skill；ChatGPT 端则复制并填写 [`CHATGPT_INSTRUCTIONS.md`](examples/CHATGPT_INSTRUCTIONS.md)，让新的聊天也知道交接规则。两端账号和连接分别配置，安装 skill 不会自动给 ChatGPT 增加 GitHub 工具。

编辑 `config.json` 中的 `id`、`name`、`repository`、`branch` 和 `local_root`。`local_root` 是本机真实项目的绝对路径；`repository` 只接受 `owner/name`。默认只监听仓库根目录的 `HANDOFF.md`，并拒绝公开仓库；确需公开交接时，在逐项检查请求和回执暴露范围后显式设置 `allow_public_repository: true`。`config.json` 已被 Git 忽略，不要提交包含本地路径的配置。

将 [`examples/HANDOFF.example.md`](examples/HANDOFF.example.md) 复制为**项目共享仓库**根目录的 `HANDOFF.md`，把其中 `project_id` 改成配置里的 `id`，再由项目所有者在共享仓库执行 `git add HANDOFF.md`、`git commit -m "Add handoff entry"` 与 `git push -u origin HEAD`。模板中 `requests` 为空，不会唤醒 Codex。其他项目资料也需先按各自授权推送；此工具不会自动上传本地目录。

## 3. 只读预检

```powershell
python runtime/git_handoff.py --check --config config.json
```

预检读取配置与 GitHub 交接文档，确认本地目录、Codex 命令、文档格式，并输出当前 `pending_request_ids`；它不创建 Codex 任务。首次运行前检查这个列表，确认没有历史待执行请求。配置或账号访问错误必须先解决。

如果还要确认 Codex 登录和当前接口可执行，可选择运行：

```powershell
python runtime/verify_codex.py
```

此项会创建一个临时项目和一条 Codex 验证聊天，**消耗一次模型调用**。输出 `execution: completed`、`marker_present: true`、`project_unchanged: true` 才算通过；测试目录会清理，聊天记录会保留。最长等待 3 分钟，超时后停止测试所启动的服务。它只验证本地执行桥，不替代第 5 步的聊天端往返验收。

## 4. 启动执行通路

```powershell
python runtime/git_handoff.py --run --config config.json
```

保持终端运行。监听器默认每 30 秒检查一次已登记的项目，只接受 `HANDOFF.md` 中的 `pending` 请求；它会为新请求创建 Codex 任务，在本地 SQLite 账本中去重，并把任务与回执写回同一文件。状态与账本保存在 `.handoff-state/`，此目录已被 Git 忽略。不要运行第二个实例，也不要删除账本来消除 `unknown` 状态。

终端安静时可用 `Get-Content .handoff-state/status.json` 查看每个项目最近检查时间、`ok` 和错误信息。复制安装目录不会共享去重锁；同一个项目只能由一个安装副本监听。升级前先确认任务结束并停止旧监听器，保留 `config.json` 和 `.handoff-state/`，然后更新文件再启动。项目 ID 不得复用于另一个仓库或本地目录。

监听器以当前机器上登录的 `gh` 与 `codex` 身份运行。它不会自行提升权限；如果 Codex 请求交互审批，桥接器不会代替用户同意。需要人工处理的任务应在 Codex 界面中直接进行。

## 5. 验收一次完整往返

先用不会修改项目文件的任务验证连接。在 ChatGPT 中要求它直接通过**自己的 GitHub 工具**重新读取项目仓库的 `HANDOFF.md`，查重后用当前 blob SHA 追加唯一请求：

```json
{
  "request_id": "handoff_check_20260929_a1",
  "status": "pending",
  "base_commit": "请填写当前共享项目提交的完整 40 位 SHA",
  "task": "这是交接验收。不要修改项目文件，只回复 HANDOFF_CHECK_OK_a1。",
  "acceptance": "Codex 最终答复包含 HANDOFF_CHECK_OK_a1，且项目文件无修改。"
}
```

示例 ID 只能用一次；实际运行请换成新的 ID。`base_commit` 必须指向该项目仓库已存在的提交。聊天更新交接文件时应保留其他条目，并提交完整文件与刚读取的 blob SHA。若更新工具报错，先重新读取远端确认是否已经写入，不能直接换 ID 重发。

等待监听器处理后，让 ChatGPT 再次直接读取 `HANDOFF.md`，核对同一 `request_id` 的 `receipt.thread_id`、`receipt.turn_id`、最终答复与预期标记。`completed` 仅代表 Codex 轮次结束，还需检查验收条件。成功后再提交真正的工程任务。

## 停止、恢复和边界

确认没有运行中任务后，在前台按 Ctrl+C 停止。也可以在 `.handoff-state/` 下创建 `STOP` 文件，监听器会在本轮结束后退出；再次启动前需移除该文件。停止可能中断它托管的 Codex 进程，因此先核对任务状态。

如果派发结果为 `unknown`，检查既有 Codex 任务和本地账本，不自动重发。回写失败时保留本地执行结果，网络恢复后重试回写。仓库中的请求或回执不得包含凭据、私人资料或未经批准共享的内容。

尚未派发的排队请求可以改成 `cancelled`；监听器观察到撤回后不再执行。已派发任务不能靠修改 Git 状态中断，需在 Codex 中处理；轮询无法保证撤回与派发同时发生时一定拦截。已完成、失败、阻塞或已取消的条目可在回执留档后移出请求数组，避免达到 100 条上限；本地账本继续保留，原 ID 不得复用。运行中和 `unknown` 条目需先核实，不得直接移除。

此工作流仅在已登记项目内工作。ChatGPT 的 GitHub 权限可能大于本协议约定的“仅改交接文件”；这是协作规则，不是 OAuth 层文件权限隔离。每新增项目都需要单独配置、检查共享范围并验收。

## 离线验证

```powershell
python -m unittest discover -s tests -v
```

测试使用模拟 GitHub 与 Codex 服务，不消耗模型调用，也不访问真实项目。它验证请求去重、并发回写、派发不确定时不重发、回执失败后的恢复等行为。真正的聊天到本机闭环，必须按第 5 步在自己的仓库实测。

Codex 本地任务由官方 [Codex app-server](https://learn.chatgpt.com/docs/app-server) 接口创建，复用本机 Codex 的登录方式。本项目按 [MIT](LICENSE) 开源。
