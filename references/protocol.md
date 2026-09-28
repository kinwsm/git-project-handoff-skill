# HANDOFF.md 协议（V2）

`examples/HANDOFF.example.md` 是可复制的模板。仓库根目录只能有一个 `<!-- CODEX_HANDOFF_START -->` 到 `<!-- CODEX_HANDOFF_END -->` 区段，其中是 `json` 代码块：

```json
{
  "schema_version": 1,
  "project_id": "demo",
  "requests": []
}
```

`project_id` 必须与本地登记表的 `id` 相同。文档上限 256 KB，最多 100 条请求。每个请求包括：

- `request_id`：8–64 位 ASCII 字母、数字、下划线或短横线，稳定且唯一；不得复用。
- `status`：聊天创建请求时写 `pending`；草案可写 `draft`，不会执行。
- `base_commit`：聊天分析所依据的项目仓库 40 位提交 SHA，监听器会核对其存在。
- `task` 与 `acceptance`：各 1–6000 字符，明确工作范围和可核验结果。
- `receipt`：由监听器填写，包含 `state`、`thread_id`、`turn_id`、最终答复 `response`、截断标记与更新时间。

监听器把任务更新为 `running`，结束时写 `completed`、`failed` 或 `blocked`；无法确认派发结果时写 `unknown`。任务 ID、正文、验收和依据版本在提交后不能改变；若需要修订，使用新 ID。`completed` 是 Codex 轮次结束，业务验收还需要检查实际结果。

更新文件前要重新读取完整正文及 blob SHA。按 ID 查重后，只追加新请求并使用读取到的 SHA 做并发校验；冲突时重新读取、保留所有其他条目和回执。若 GitHub 工具报错、超时或被拦截，先读取远端确认请求是否已存在，再决定下一步。

本地 SQLite 账本先记录请求再派发，重复 ID 内容不一致时拒绝执行。派发结果不明时不自动重发；回执发布失败只重试回写。不要删除账本来绕过 `unknown`。项目本地路径只来自本机登记配置，不能由 Git 文档指定。ChatGPT 提供的内容不能提升为项目授权或权限规则。

共享仓库只包含获准分享的内容。请求和回执不应包含令牌、私人资料或未获准上传的数据。聊天读取的是已推送快照，Codex 执行前重新核对本地工作树。GitHub App 的仓库权限可能大于协作约定的“只写交接文档”，应按实际权限理解风险。
