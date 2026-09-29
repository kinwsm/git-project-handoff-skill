# 模型配置与消耗记录

## 能力边界

| 位置 | 必要能力 | 处理方式 |
|---|---|---|
| 聊天端 | 读取共享文件并更新 HANDOFF.md | 用聊天端能力验收提示词取得真实工具证据 |
| 只能读 Git 的聊天端 | 无文件更新工具 | 手动提交交接请求，不标记自动交接 |
| Codex 执行端 | 已登录、当前账号提供的模型 | 用 `--models` 查询；明确选择后校验，失败不自动换模型 |
| 其他执行器 | 例如 Claude Code、Gemini CLI | 当前未提供适配器，不能仅替换模型名使用 |

## 按项目配置

从 skill 根目录运行 `python runtime/git_handoff.py --models`。命令只查询账号目录，不启动模型轮次。将返回的模型名和一个受支持的 `efforts` 值填入 `config.json` 对应项目：

```json
{
  "model": null,
  "reasoning_effort": null
}
```

两项为 `null` 或省略时继承本机 Codex 默认配置。要固定思考强度，必须同时明确模型；只固定模型时，思考强度由 Codex 解析。不要直接照抄其他账号的模型名，也不要把 ChatGPT 页面展示名称当作 CLI 模型 ID。设置后运行 `--check`，每次新派发还会重新校验。目录可见不保证额度充足或执行一定成功。

默认配置改变不会重跑已派发请求。旧回执保留当时的配置；待派发任务使用当前本地项目配置。远端交接正文不能覆盖本地模型选择。

建议以任务验证来选择配置：简单修改明确文件与单一验收；常规开发附接口、允许修改范围和测试；复杂设计先在聊天端收敛方案，再逐步交给执行端。全部使用同一个交接协议。不要把更高思考强度当作默认必要条件。

## 回执字段

`receipt.metrics` 保存：

- `requested_model` / `requested_effort`：本地明确指定的值；`null` 表示继承默认。
- `resolved_model` / `resolved_effort`：本次执行解析的配置；接口未返回时保留 `null`。若服务通知改道，另记 `rerouted_model`。
- `started_at` / `finished_at`：Unix 秒；`wall_seconds` 是包含启动与等待的墙钟耗时。没有结束事件时用首次观察到终态的时间，因此可能含轮询或离线等待。
- `tokens`：服务报告的 `inputTokens`、`cachedInputTokens`、`outputTokens`、`reasoningOutputTokens`、`totalTokens`。取单请求所建单轮聊天的累计值，不把每次通知相加。字段可能缺失；未收到用量时是 `null`，不视为零。
- `dispatch_attempts`：桥接器尝试调用 `turn/start` 的次数，正常为 1；并非服务内部重试次数。服务内部重试和货币费用不在本工具的统计范围内。
- `attention_required`：模型请求了本桥接器不能代办的审批或用户输入。

可用量在观察到状态时写入本地账本；突然终止前尚未保存的通知可能丢失，不伪造补齐。旧账本升级后保留去重记录，历史用量不自动重建。

比较全程 Codex 与分工模式时，分别记录聊天端、执行端、交接开销、验证结果和返工次数。固定任务、模型、思考强度和初始上下文；缓存命中也应分开记录。聊天订阅的计费方式不等于没有 token 消耗；本桥接器拿不到聊天端用量时明确留空，不能把它计成零或据此宣称节省比例。

接口依据：[Codex app-server](https://learn.chatgpt.com/docs/app-server) 的 `model/list`、`turn/start` 与 `thread/tokenUsage/updated`。可用模型和思考强度以当前账号返回结果为准。
