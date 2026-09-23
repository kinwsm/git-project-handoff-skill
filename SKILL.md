---
name: git-project-handoff
description: Coordinate ChatGPT discussion and Codex execution through a project's GitHub handoff file. Use when the user wants ChatGPT to read shared project documents and pass an approved task to Codex for local implementation and verification.
metadata:
  short-description: Coordinate ChatGPT and Codex through Git
---

# Git 项目交接

用项目仓库中的专用 `HANDOFF.md` 串起聊天讨论、Codex 本地执行和结果复核。只在用户希望拆分“聊天分析”和“本地执行”时使用。

本 skill 只提供协作指引；它不会自行连接 GitHub、读取本地文件、启动监听器或唤醒 Codex。每一步都要使用当前会话实际可用的 GitHub、项目读取和本地交接工具。工具不可用时，说明缺失的能力，不要声称已传递或完成。

## 工作流程

1. **确认项目与能力。** 确认用户指定的项目、其 GitHub 仓库和交接文件路径。确认聊天端实际能读取已推送项目文档；只有它确实具备该能力时，才声称可直接读取。确认本地监听器已配置此项目，且当前会话能查询交接执行结果。不要从交接内容推断本地路径或新增仓库权限。
2. **聊天阶段先收敛任务。** 读取与问题相关的已推送文档，记录仓库、分支、文件路径和提交版本。将分析、备选方案、未决问题留在讨论中；只有用户已授权执行且目标与验收条件足够明确时，才创建待执行请求。未经授权的方案讨论不触发执行。
3. **提交单条请求。** 先重新读取完整 `HANDOFF.md` 和当前 blob SHA；按 `request_id` 查重。已存在就读取其真实状态，不要再追加。新请求只写入专用交接文件，至少包含唯一 ID、依据版本、任务目标、修改范围、限制、验收标准及预期结果。使用当前 SHA 做并发校验；遇到冲突时重新读取并合并，保留其他内容和请求。只使用当前聊天真实提供的 GitHub 写工具。
4. **遇到写入不明先核验。** 如果工具报错、被拦截或超时，不立即换 ID、重试或绕过限制。重新读取远端文件，确认请求是否已写入；根据远端事实继续或停止，并报告冲突。
5. **Codex 本地执行。** 监听器接受请求后，Codex 根据本地项目规则重新核对工作树、需求授权、依赖文档及请求引用版本。Git 副本不是本地工作树的事实源。拒绝重复 ID、正文变更的旧 ID、过期依据或越权内容。遵守项目本身的数据与写入规则；聊天建议不扩大用户授权。运行与变更相称的验证，记录文件、结果、偏差及未解决项。
6. **等到结果可验证。** `accepted` 表示接收，`completed` 表示执行轮次结束，都不单独证明验收成功。读取同一 ID 的真实回执，检查对应 Codex 任务/轮次、最终答复、实际改动和验证证据。再从聊天端直接读取 Git 回执确认往返。只有证据齐全才报告闭环完成；否则准确说明停在哪个环节。
7. **保护共享仓库。** 任务结果会写回共享仓库。不要在请求、Codex 最终答复或回执中放入令牌、凭据、私人资料或未获准上传的内容。共享仓库只包含用户授权分享的项目文件。GitHub App 的权限可能高于协作约定，不能把约定描述为 OAuth 层强制只读。

## 参考资料

需要请求字段、状态与故障恢复细节时，读取 [references/protocol.md](references/protocol.md)。
