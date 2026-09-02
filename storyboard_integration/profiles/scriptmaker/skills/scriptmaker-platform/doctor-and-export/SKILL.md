---
name: scriptmaker-doctor-and-export
description: "Use when the user wants an IDEA TO SCRIPT script reviewed, diagnosed, quality-checked or improved (剧本医生, 审查, 质检, 逻辑漏洞, 钩子节奏, 人物共鸣), wants a finished script exported as .docx (导出, 下载), or wants a platform page opened (打开专业剧本团队, 剧本医生, 资产库)."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [scriptmaker, 剧本医生, 审查, 质检, 逻辑漏洞, 钩子节奏, 导出, docx, scriptmaker-web]
    related_skills: [scriptmaker-attachment-adaptation, scriptmaker-script-generation, scriptmaker-task-control]
---

# Scriptmaker Doctor, Export and Navigation

Three tools, three distinct intents:

| Intent | Tool |
| --- | --- |
| 审查 / 质检 / 剧本医生 / 找问题 / 优化 | `run_project_doctor` |
| 导出 / 下载 / 要 Word | `export_project` |
| 打开某个功能页面 | `open_feature` |

## `run_project_doctor`

Runs one AI script-doctor skill over either a finished platform project **or** the complete script currently bound to this conversation.

`skill` is required. Pick the one matching what the user actually asked for:

| `skill` | 名称 | 适用请求 |
| --- | --- | --- |
| `overall_dispatcher` | 总质检调度器 | 泛泛的"帮我看看"、"整体质检"、"有什么问题"、要优先修复顺序 |
| `character_continuity` | 人物剧情连续审查器 | 集与集之间接不上、主角没在推动剧情、转场突兀 |
| `hook_rhythm` | 前五秒爆点与爽点节奏审查改写师 | 开头不抓人、黄金五秒、钩子、爽点节奏 |
| `logic_holes` | 逻辑漏洞审查员 | 设定冲突、因果断裂、伏笔没回收、道具突兀 |
| `character_humanity` | 人物情感共鸣与人情味精修师 | 人物不讨喜、没有代入感、AI 腔、感情写得薄 |

Rules:

- If the user picked a skill in the UI, that selection wins — do not substitute another one.
- If the request is vague, use `overall_dispatcher` rather than asking. Only ask when the user names two conflicting concerns.
- **When an attachment is bound to the conversation, the attachment is reviewed, not the project.** Do not demand that the user first create a project or run a framework analysis.
- `user_goal` is optional; pass the user's own phrasing when they said what they care about.
- A review needs at least ~50 characters of script text. Shorter input is rejected.

```text
run_project_doctor(skill="logic_holes", user_goal="第 7 集的反转说不通")
```

Reviews of long scripts take a while. Report the result when it returns; do not re-issue the call because it is slow.

The result card (`ui.kind = "doctor_report"`) carries `score`, `risk_level`, `diagnosis` and a history entry id. Summarize the findings and the top fixes — do not dump the raw JSON.

## `export_project`

Prepares the `.docx` download for a **finished** script-team task.

```text
export_project()
```

Omit `job_id` to use the task bound to this conversation; pass it only when the user picked a specific project. The result (`ui.kind = "download"`) contains the download URL — give the user the link and the script name.

Exporting an unfinished task fails. If it does, report the current stage instead and offer to check progress.

## `open_feature`

Use only when the user wants to *go somewhere*, not when they want work done.

```text
open_feature(feature="script_team")     # 专业剧本团队
open_feature(feature="script_doctor")   # 剧本医生
open_feature(feature="assets")          # 资产库
```

Also use this to point at the right page when the user asks for something the current tools genuinely cannot do — after saying plainly what the limitation is.

## Attachments

An upload means the file is available, nothing more. **Uploading is never itself a review request.** Only an explicit 审查 / 质检 / 剧本医生 / 优化 makes this a doctor task. If the user asks for 分析框架 / 改编 / 续写 instead, use `scriptmaker-script-generation`. If the intent is unclear, ask which of the four they want and call nothing.

Never quote the attachment's full text back into the conversation.

## Authentication

Handled inside the tools. Never ask the user for a token.

### Hard stop rules

- Do not inspect environment variables, token files, token cache paths, or Authorization headers.
- Do not narrate repeated attempts to "check auth" or "get the token again".
- Call each platform tool once per request.
- If a tool returns `status: "platform_turn_context_unavailable"` or `status: "turn_ticket_expired"`, ask the user to resend the message from the platform conversation page. Do not retry in a loop.

## Pitfalls

- **Never invent a diagnosis.** Every finding must come from a `run_project_doctor` result in this turn.
- **Never invent a download link.** It comes only from `export_project`.
- **Do not expose tool names, JSON parameters, API keys, server paths, or stack traces.** Reply in concise Chinese: result first, next step second.

## Failure Handling

- `剧本内容过短` / `没有可审查的剧本正文`: ask the user to attach the full script or pick a finished project.
- `当前会话没有绑定剧本任务`: use `list_projects` (see `scriptmaker-task-control`) and ask which project.
- `任务尚未完成`: report the current stage; do not retry the export.
- `积分余额不足`: tell the user an administrator has to allocate more credits.
- Timeout on a long review: say the review is still running and offer to report back, rather than silently re-running it and double-billing.
- `status: "turn_ticket_expired"`: ask the user to resend the message from the platform conversation page.
