---
name: scriptmaker-script-generation
description: "Use when the user explicitly wants the IDEA TO SCRIPT seven-node professional screenwriting team to create, generate, adapt, or plan a script (专业剧本团队, 七节点, 启动节点, 生成完整项目). Do not use for current-model-only attachment reading or adaptation."
version: 1.1.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [scriptmaker, 剧本平台, 剧本生成, 短剧, 专业剧本团队, 框架分析, ask_choice, scriptmaker-web]
    related_skills: [scriptmaker-attachment-adaptation, scriptmaker-task-control, scriptmaker-doctor-and-export]
---

# Scriptmaker Script Generation

Use this skill only when the user wants a **new professional-team task** produced or planned on the platform: a fresh idea, a team adaptation of an uploaded document, a story framework, or a continuation through the seven-node workflow.

If the user says 当前模型 / 直接在对话里 / 不要启动节点 / 不用专业团队, or simply asks to read, summarize, answer questions about, locally rewrite, or directly adapt the attachment without requesting a team workflow, use `scriptmaker-attachment-adaptation` instead. Never call `prepare_script_generation` or `confirm_script_generation` for that direct mode.

It covers three tools, always used in this order:

```text
ask_choice  ->  prepare_script_generation  ->  confirm_script_generation
```

## The three-step contract

**This ordering is enforced by the platform, not by you.** Skipping a step returns `ok: false`; it does not start anything.

1. `prepare_script_generation` — validates the collected fields, stores a pending action, and returns a plan card with a cost estimate. **It never starts a task and never spends credits.**
2. `confirm_script_generation` — starts the paid seven-node run. It is accepted only when *both* are true:
   - you pass `confirmed: true`, **and**
   - the user's message *in this same turn* is an explicit go-ahead.

   The platform re-reads the user's raw message itself. Passing `confirmed: true` on a turn where the user did not actually agree returns `ok: false` — so do not try it, and do not retry it. Ask the user to confirm instead.
3. Only after `ok: true` from `confirm_script_generation` is a task actually running.

## Required User Inputs

Before calling `prepare_script_generation`, these three must be explicit:

1. `user_expectation` — 创作要求 (at least 10 characters; the genre, premise, audience, tone)
2. `total_episodes` — 总集数
3. `character_count` — 主要角色数量

Inferred and optional:

- `title` — infer it from the premise; do not ask.
- `episode_word_count` — defaults to 600. Ask only if the user raises it.
- `execution_scope` — `framework_only` (stop after 分集连续性编剧) or `framework_and_script` (all seven nodes). When an attachment is present the platform defaults to `framework_only`.

Ask for **only the missing values**, at most three in one turn, and never re-ask for something the user already said in different words.

## Asking with `ask_choice`

When a required field is missing or genuinely ambiguous, call `ask_choice` to render a selection card:

```text
ask_choice(
  field="total_episodes",
  question="这部剧计划做多少集？",
  options=[
    {"label":"20 集","prompt":"总集数：20 集","description":"常见短剧长度"},
    {"label":"30 集","prompt":"总集数：30 集","description":"更完整的情节容量"}
  ]
)
```

Rules:

- **`ask_choice` must be the only tool call in its turn.** Never pair it with an operation tool. The card stops the turn and waits for the user; anything called alongside it is discarded.
- Two to five options. Fewer than two is rejected — use a short plain-language question instead.
- One question per card, the single most decision-changing one.
- The user may always answer freely instead of picking an option.

After the tool returns `awaiting_user_input: true`, present the question and stop. Do not guess the answer and continue.

## Understanding the user

- Judge the intended outcome first, then decide whether a tool is needed. Do not require platform vocabulary or fixed keywords.
- Spoken, elliptical, misspelled or anaphoric phrasing is normal — "把刚才那个接着做", "照这个来", "先把故事骨架弄好" all resolve against the recent conversation and the current task state.
- Distinguish **discussion** from **execution**. Answer questions about approach or capability directly; call tools only when the user wants the platform to act.
- When the user corrects one condition, change only that condition and keep every previously settled field.

## Attachments

An uploaded file is bound to the current conversation until another attachment replaces it. **Uploading is never itself a request to analyze, review, adapt, restructure, or generate.**

- Only when the user explicitly asks the professional team / seven nodes to perform 分析框架 / 拆解重构 / 改编生成 / 续写 does this skill apply — and 总集数 plus 主要角色数量 are still required first.
- Direct current-model reading, Q&A, rewriting or adaptation belongs to `scriptmaker-attachment-adaptation` and does not require team fields.
- Only when the user explicitly asks for 审查 / 质检 / 剧本医生 / 优化 does this become a doctor request — use `scriptmaker-doctor-and-export` instead.
- If the intent is unclear, ask whether they want the current model to handle it directly or start the professional team. Do not start a team tool.
- **Never quote the attachment's full text back into the conversation.** The platform reads it server-side after confirmation; repeating it re-bills the whole script every turn.

## Distillation skills

If the user has locked a 爆款蒸馏 Skill in the UI, it is a structural constraint on this script. Preserve its exact name and published version through `prepare_script_generation`; never substitute, downgrade, or drop it. The skill transfers narrative function, beat relationships, and description method only — it must not carry the sample's characters, relationship tropes, occupations, scenes, props, evidence devices, illnesses, or specific events into the new story.

## The generation pipeline

Generation always runs the professional screenwriting team, in this order:

总编剧 → 故事架构师 → 人物情感编剧 → 分集连续性编剧 → 正文对白编剧 → 状态记录器 → 终审与钩子编辑

`framework_only` stops after 分集连续性编剧. `framework_and_script` runs all seven nodes.

## Authentication

Authentication is handled inside the tools. Never ask the user for a token, and never mention tickets, tokens, or session variables.

### Hard stop rules

- Do not inspect environment variables, token files, token cache paths, or Authorization headers.
- Do not narrate repeated attempts to "check auth", "try terminal", or "get the token again".
- Call each platform tool once per request.
- Do not report internal session variables as missing before actually calling a tool.
- If a tool returns `status: "platform_turn_context_unavailable"` or `status: "turn_ticket_expired"`, this is a session problem, not a task failure: ask the user to resend the message from the platform's conversation page. Do not retry in a loop.

## Success Response

`prepare_script_generation` returns `prepared: true`, `confirmation_required: true`, a `summary` payload, and `ui.kind = "confirmation"`. Present the plan — 题材、集数、角色数、执行范围、预计消耗 — and ask for confirmation.

`confirm_script_generation` returns `ui.kind = "task_started"` with the job id. Reply with the task and where to watch it.

Example reply:

```text
已启动《<title>》的专业剧本团队任务，共 <total_episodes> 集。
你可以随时问我进度，或者说“暂停”“继续”。
```

## Pitfalls

- **Never claim work happened without a tool call.** Anything touching projects, tasks, exports, reviews, or status must go through a tool.
- **Never call `confirm_script_generation` speculatively.** It spends the user's credits.
- **Do not expose tool names, JSON parameters, API keys, server paths, or stack traces** in the reply. Answer in concise Chinese: result first, next step second.

## Failure Handling

- `创作要求过短` / `missing_fields` present: ask for exactly the listed missing fields.
- `请先确认执行方案` — `confirm_script_generation` was called before `prepare_script_generation`. Call prepare first.
- `未获得明确确认`: the user's message was not an explicit go-ahead. Ask them to confirm in plain words; do not re-send `confirmed: true`.
- `积分余额不足`: tell the user their credit balance is insufficient and that an administrator has to allocate more.
- `status: "turn_ticket_expired"`: ask the user to resend the message from the platform conversation page.
