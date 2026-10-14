---
name: scriptmaker-task-control
description: "Use when the user asks about or controls existing IDEA TO SCRIPT platform tasks — listing projects, switching the active project, checking progress (进度, 到哪了, 卡住了), or pausing, resuming, retrying and terminating a run (暂停, 继续, 重试, 终止)."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [scriptmaker, 剧本平台, 任务进度, 暂停, 继续, 重试, 终止, 项目查询, scriptmaker-web]
    related_skills: [scriptmaker-script-generation, scriptmaker-doctor-and-export]
---

# Scriptmaker Task Control

Use this skill when the user refers to work that already exists on the platform: listing it, selecting it, asking how far along it is, or changing its run state.

| Intent | Tool |
| --- | --- |
| 有哪些项目 / 我的剧本列表 | `list_projects` |
| 切到那个项目 / 用第 2 个 | `select_project` |
| 进度 / 到哪了 / 卡住了吗 | `get_project_status` |
| 暂停 / 先停一下 | `pause_task` |
| 继续 / 接着跑 | `resume_task` |
| 重试 / 再试一次 / 从断点跑 | `retry_task` |
| 终止 / 不做了 / 取消这个任务 | `terminate_task` |

## Resolving which task the user means

None of these tools require the user to know a job id.

- When the user says "这个项目"、"刚才的剧本"、"继续它", use the script-team job id already bound to the current conversation. The platform resolves it from conversation state when `job_id` is omitted — **prefer omitting it** over guessing.
- Pass `job_id` only when the user picked a specific project out of `list_projects` in this conversation.
- If nothing is bound and the user was not specific, call `list_projects` first and let them choose.

Call shapes:

```text
list_projects(limit=10)
select_project(job_id="<job_id>")
get_project_status()
pause_task()
resume_task()
retry_task()
```

## Termination requires explicit confirmation

Query, pause, resume and ordinary retry execute directly — no confirmation needed.

**Termination does not.** `terminate_task` requires *both*:

- `confirmed: true` from you, **and**
- an explicit termination phrase from the user in this same turn — 确认终止 / 立即终止 / 终止任务 / 停止并终止.

The platform independently re-reads the user's raw message. A vague "算了" or "不做了" is **not** sufficient and will return `ok: false`. Ask the user to confirm termination in plain words first:

```text
终止后这个任务的进度会作废，无法从断点恢复。确认要终止吗？请回复“确认终止”。
```

Then, and only then:

```text
terminate_task(confirmed=true)
```

Do not resend `confirmed: true` after a rejection. Ask again instead.

## Resume and retry semantics

- Both refuse while the task is already running — tell the user it is still running and report the current stage rather than forcing it.
- Both restart from the first stage whose artifact is missing, not from the beginning. Say so: the completed nodes are not re-run and not re-billed.

## Reading progress back to the user

`get_project_status` returns a progress card (`ui.kind = "progress"` or `"project"`) with `status`, `current_stage_label`, `pipeline_stage` (1–7) and `progress_percent`.

Report the stage in human terms, not the raw field:

```text
《<title>》正在跑第 3 个节点“人物情感编剧”，整体进度约 29%。
```

The seven nodes are: 总编剧 → 故事架构师 → 人物情感编剧 → 分集连续性编剧 → 正文对白编剧 → 状态记录器 → 终审与钩子编辑。A `framework_only` run stops after 分集连续性编剧 — when such a task shows as finished at node 4, that is complete, not stalled.

## Understanding the user

- Do not require platform vocabulary. Map natural phrasing to the closest tool.
- Distinguish asking from acting: "为什么这么慢" is a question about the current status, not a request to restart anything.
- Never claim a task was paused, resumed or terminated without the tool having returned `ok: true`.

## Authentication

Handled inside the tools. Never ask the user for a token.

### Hard stop rules

- Do not inspect environment variables, token files, token cache paths, or Authorization headers.
- Do not narrate repeated attempts to "check auth" or "get the token again".
- Call each platform tool once per request.
- If a tool returns `status: "platform_turn_context_unavailable"` or `status: "turn_ticket_expired"`, ask the user to resend the message from the platform conversation page. Do not retry in a loop.

## Pitfalls

- **Never fabricate progress.** Every status claim must come from a tool result in this turn.
- **Do not expose tool names, JSON parameters, job ids formatted as internals, API keys, server paths, or stack traces.** Reply in concise Chinese: result first, next step second.
- Do not offer to terminate as a fix for a slow task; suggest checking status first.

## Failure Handling

- `当前会话没有绑定剧本任务`: call `list_projects` and ask the user which one.
- `任务正在运行中`: report the current stage instead of retrying.
- `未获得明确终止确认`: ask the user to reply 确认终止.
- `任务不存在或无权访问`: the job id does not belong to this user — re-list the projects.
- `status: "turn_ticket_expired"`: ask the user to resend the message from the platform conversation page.
