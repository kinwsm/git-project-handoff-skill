# Git Project Handoff Skill

Codex skill for coordinating ChatGPT discussion and local Codex execution through a per-project GitHub `HANDOFF.md` and an already configured local listener.

## Contents

- `SKILL.md`: when and how Codex should run the handoff workflow.
- `references/protocol.md`: request fields, duplicate protection, recovery, boundaries, and closure evidence.
- `agents/openai.yaml`: Codex UI metadata.

The skill contains no project snapshot, listener database, run logs, credentials, or local configuration. It does not implement or install the listener and cannot grant ChatGPT GitHub access by itself.

## Install

Copy the `git-project-handoff` folder into `~/.codex/skills/` (on Windows, `%USERPROFILE%\.codex\skills\`). Restart Codex so it discovers the new skill. Then invoke it with `$git-project-handoff` or describe a task that matches its purpose.

The GitHub repository stores the distributable skill; local installation is a separate copy. Update both deliberately when changing the skill.
