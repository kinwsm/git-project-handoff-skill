# ChatGPT 与 Codex 交接

本文件是项目唯一的执行请求入口。项目其他已分享文档供聊天读取；项目代码和资料由 Codex 按用户授权修改。

填写 `project_id`，使它与本地 `config.json` 中的 `id` 一致。聊天端创建请求前先读完整文件和当前 blob SHA，检查 `request_id` 是否已存在；只追加新请求并用当前 SHA 更新文件。监听器管理状态与回执。

每条请求需要唯一 `request_id`（8–64 位 ASCII 字母、数字、下划线或短横线）、`status: pending`、40 位 `base_commit`、任务正文 `task` 和可验证的 `acceptance`。草案使用 `draft`，不会触发执行。请求一旦提交就不要修改正文或复用 ID。

<!-- CODEX_HANDOFF_START -->
```json
{
  "schema_version": 1,
  "project_id": "demo",
  "requests": []
}
```
<!-- CODEX_HANDOFF_END -->
