---
name: storyboard-text
description: "Create text storyboard tasks through /api/storyboard/text with only script name, start episode, and end episode required."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [storyboard, text-storyboard, 分镜, 文本分镜, 剧本, episodes, storyboard-web]
    related_skills: []
---

# Storyboard Text Task

Use this skill when the user wants to create/generate a text storyboard task for the storyboard platform.

The backing endpoint is:

```http
POST /api/storyboard/text
```

## Required User Inputs

Before calling the API, ensure these three values are explicit:

1. `script_name` - 剧本名
2. `start_episode` - 开始集数
3. `end_episode` - 结束集数

If any of the three values are missing or ambiguous, ask the user for only the missing values. Do not ask for style, ratio, scene mode, prompt, model, or any other optional parameter.

## Request Body

Send only these fields:

```json
{
  "jj": "<script_name>",
  "start_index": <start_episode>,
  "loop_num": <end_episode>
}
```

`jj` is the API's script name field. `loop_num` is the API's ending episode field, not a count.

Do not include optional fields such as `style`, `ratio`, `is_scene`, or `system_prompt`. The server will use its defaults:

- `style`: script profile style, otherwise `真人写实`
- `ratio`: script profile ratio, otherwise `16:9`
- `is_scene`: `false`
- `system_prompt`: empty string

## Validation

Before calling the API:

- **Combined Input Parsing**: If the user provides a combined input like `剧本名 1-1` or `剧本名 1-5`, automatically extract the script name (e.g., `剧本名`), starting episode (e.g., `1`), and ending episode (e.g., `1` or `5`). Do not treat the numbers as part of the script name or ask the user to specify them again.
- Convert `start_episode` and `end_episode` to positive integers.
- If `end_episode < start_episode`, tell the user the ending episode cannot be smaller than the starting episode and ask for corrected values.
- Keep the script name exactly as parsed, except trimming surrounding whitespace.

## Authentication

Use `storyboard_api` for all storyboard platform API calls. Do not ask the user to paste a token.

The model should only pass business parameters. Authentication, token lookup, token isolation, API base URL selection, and Authorization headers are handled inside `storyboard_api`.

Call shape:

```text
storyboard_api(
  endpoint="/api/storyboard/text",
  method="POST",
  body={"jj":"<script_name>","start_index":<start_episode>,"loop_num":<end_episode>}
)
```

If the tool returns `needsLogin: true` with `loginUrl`, this is a normal authorization step, not a task failure. Send that login link to the user and ask them to finish binding, then retry the original request after they confirm. If `storyboard_api` is unavailable, stop and tell the administrator to enable the `storyboard_api` Hermes tool for this entry.

### Hard stop rules

- Do not narrate repeated attempts to "check auth", "try terminal", or "get token again".
- Call `storyboard_api` once for the platform request.
- Do not inspect environment variables, token files, token cache paths, or Authorization headers.
- Do not report internal session variables or agent client credentials as missing before trying `storyboard_api`.
- If `storyboard_api` returns a login link, send it once regardless of the `success` field. If the user says the link expired, call `storyboard_api` again to get a fresh link.

### User-facing reply example

```text
我需要先绑定你的平台账号。请打开这个链接登录并确认授权：<loginUrl>
绑定完成后请立刻告诉我，我会马上继续创建文本分镜任务。
```

## Base URL

Do not choose or print a base URL yourself. `storyboard_api` resolves the platform API base internally.

## Example

User: `给《梁山》第 3 到 5 集生成文本分镜`

Request:

```json
{
  "jj": "梁山",
  "start_index": 3,
  "loop_num": 5
}
```

Expected success response fields:

- `success: true`
- `task_id`
- `message`
- `episodes`
- `summary`

After a successful call, reply with the task id and episode range. Keep the response concise.

Example reply:

```text
已创建《梁山》第 3-5 集文本分镜任务，task_id: <task_id>。
```

## Pitfalls

- **No direct token handling**: Never read token files, print token cache paths, construct Bearer headers, or use `token_response.json`. Use `storyboard_api` only.
- **Do not waste calls on web_search for auth problems**: Auth issues cannot be solved by web searching. Use `storyboard_api`; if it returns a login link, send that link to the user.

## Failure Handling

If the API returns an error, report the platform error directly and keep it actionable.

Common errors:

- `缺少剧本名称参数 jj`: ask for the script name.
- `结束集数不能小于起始集数`: ask for corrected episode numbers.
- `找不到剧本目录`: the user's script name may differ from what's stored in the platform (e.g., "剧本测试2" vs "测试2"). Before telling the user, call `storyboard_api(endpoint="/api/scripts", method="GET")` to list all available scripts. Search the response for the closest name match and retry with the correct platform name automatically.
- `请先登录` / `登录已过期` / `授权凭证无效或已过期`: if `storyboard_api` returns `needsLogin` with `loginUrl`, send the link, then retry after binding.
- Permission/model access errors: tell the user their account does not currently have access to this script or text-storyboard model.




