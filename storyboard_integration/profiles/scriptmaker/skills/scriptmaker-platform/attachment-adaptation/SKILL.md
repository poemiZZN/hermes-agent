---
name: scriptmaker-attachment-adaptation
description: "Use when the user wants the current Hermes model to read, summarize, answer questions about, rewrite, continue, or directly adapt a document bound to an IDEA TO SCRIPT conversation without starting the seven-node professional team (直接改编, 当前模型, 不要启动节点, 对话里处理, 阅读附件)."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [scriptmaker, 附件, 阅读文档, 直接改编, 当前模型, 不启动节点, read_attachment, write_attachment_draft]
    related_skills: [scriptmaker-script-generation, scriptmaker-doctor-and-export]
---

# Scriptmaker Direct Attachment Handling

Use this skill when the user wants **this model** to work with the document inside the conversation. This path never starts the professional screenwriting team and never requires episode count or character count.

## Intent boundary

- Upload alone only makes the file available. If the user gave no purpose, ask one short question about what they want.
- Reading, summarizing, extracting facts, Q&A, local rewriting, continuation, and direct adaptation use this skill.
- If the user explicitly requests 专业剧本团队 / 七节点 / 启动节点, use `scriptmaker-script-generation` instead.
- If the user explicitly requests 剧本医生 / 审查 / 质检 / 诊断, use `scriptmaker-doctor-and-export` instead.
- If the user says 当前模型 / 直接在对话里 / 不要启动节点 / 不用团队, that choice is decisive: do not call `prepare_script_generation` or `confirm_script_generation`.

## Reading the attachment

The prompt contains only the filename, type, and character count. It does not contain the document body. Call `read_attachment` before making any claim about the content.

- `operation="metadata"`: inspect the bound file and its size.
- `operation="search"`: locate a name, scene, line, or fact without reading unrelated text.
- `operation="read"`: read a bounded character range using `offset` and `limit`.

For a request that depends on the whole document, start at `offset=0` and continue with each returned `next_offset` until `has_more=false`. Never claim to have read the whole file while `has_more=true`.

The attachment remains bound across later turns in the same conversation. Do not ask the user to upload it again merely because the current message has no new attachment chip.

## Returning an adaptation

- Small rewrites and short adapted passages: answer directly in the conversation.
- Long or full-document adaptations: save the result with `write_attachment_draft` so the platform can present a Word download.

Long draft sequence:

```text
write_attachment_draft(action="start", title="<改编稿标题>", content="<第一段>")
write_attachment_draft(action="append", draft_id="<returned id>", content="<后续段>")
write_attachment_draft(action="finish", draft_id="<returned id>", content="<最后一段或空字符串>")
```

Each write is bounded. Keep appending until all requested output is saved, then call `finish` exactly once. Only `finish` returns the download card. Do not invent a download URL.

## Safety and accuracy

- Never expose tool names, attachment ids, tickets, tokens, server paths, or raw JSON in the user-facing reply.
- Do not quote the full source document back unless the user explicitly requested a verbatim transformation and the output itself requires it.
- Preserve the source's important facts unless the requested adaptation deliberately changes them. State any major assumptions briefly.
- If the tool reports no bound attachment, ask the user to upload the document in this conversation.
- If the turn ticket expired, ask the user to resend the instruction from the platform conversation page; do not retry in a loop.

## Success response

For a short result, lead with the adapted text or answer. For a completed long draft, say it has been saved and tell the user to use the Word download card shown in the conversation.
