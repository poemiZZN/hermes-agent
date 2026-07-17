---
name: storyboard-script-upload
description: "Upload a script document through /api/scripts/upload using multipart/form-data, with explicit style, ratio, and workspace selection."
version: 1.1.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [storyboard, upload, script, 剧本上传, docx, pdf, workspace, storyboard-web]
    related_skills: [storyboard-text]
---

# Storyboard Script Upload

Use this skill when the user wants to upload/import a script document into the storyboard platform.

The upload endpoint is:

```http
POST /api/scripts/upload
```

The workspace-list endpoint is:

```http
GET /api/workspaces
```

## Required User Inputs

Before uploading, ensure these five values are explicit:

1. `script_name` - 剧本名
2. `file_path` - 本地剧本文档路径
3. `style` - 风格，must be one of: `真人写实`, `3d国漫`, `2d动漫`
4. `ratio` - 画幅比例，must be one of: `16:9`, `9:16`
5. `workspaceId` - 工作空间 ID selected from the current user's available workspaces

If any value is missing or ambiguous, ask only for the missing value.

Do not invent `style`, `ratio`, or `workspaceId`. The user must choose them from the allowed/current options.

## Authentication First

Use `storyboard_api` for all storyboard platform API calls. Do not ask the user to paste a token.

The model should only pass business parameters. Authentication, token lookup, token isolation, API base URL selection, multipart encoding, and Authorization headers are handled inside `storyboard_api`.

For workspace listing:

```text
storyboard_api(endpoint="/api/workspaces", method="GET")
```

For upload:

```text
storyboard_api(
  endpoint="/api/scripts/upload",
  method="POST",
  multipart=true,
  form={"name":"<script_name>","style":"<style>","ratio":"<ratio>","workspaceId":"<workspaceId>","teamUserIds":"[]"},
  file_field="file",
  file_path="<file_path>"
)
```

If the tool returns `needsLogin: true` with `loginUrl`, this is a normal authorization step, not a task failure. Send that login link to the user and ask them to finish binding, then retry the original request after they confirm. If `storyboard_api` is unavailable, stop and tell the administrator to enable the `storyboard_api` Hermes tool for this entry.

### Hard stop rules

- Do not narrate repeated attempts to "check auth", "try terminal", or "get token again".
- Call `storyboard_api` once for each platform request.
- Do not inspect environment variables, token files, token cache paths, or Authorization headers.
- Do not report internal session variables or agent client credentials as missing before trying `storyboard_api`.
- If `storyboard_api` returns a login link, send it once regardless of the `success` field. If the user says the link expired, call `storyboard_api` again to get a fresh link.

User-facing reply example:

```text
我需要先绑定你的平台账号。请打开这个链接登录并确认授权：<loginUrl>
绑定完成后我会继续上传剧本。
```

## Workspace Selection

Fetch the user's current workspaces before uploading:

```text
storyboard_api(endpoint="/api/workspaces", method="GET")
```

Expected response shape includes:

```json
{
  "success": true,
  "workspaces": [
    { "id": 1, "name": "默认" }
  ]
}
```

Show the available workspaces to the user and ask them to choose one by name or ID. Do not use a workspace that was not returned by `/api/workspaces`.

Example prompt:

```text
请选择上传到哪个工作空间：
1. 默认（ID: 1）
2. 短剧组（ID: 2）
```

If there are no available workspaces, tell the user their account needs to be added to a workspace first.

## Style Selection

Ask the user to choose exactly one style from:

```text
真人写实
3d国漫
2d动漫
```

Do not accept other style values for this skill unless the user explicitly asks to bypass the preset list.

Example prompt:

```text
请选择剧本风格：真人写实 / 3d国漫 / 2d动漫
```

## Ratio Selection

Ask the user to choose exactly one ratio from:

```text
16:9
9:16
```

Example prompt:

```text
请选择画幅比例：16:9 / 9:16
```

## Accepted Files

The platform upload UI accepts `.docx` and `.pdf` documents. Prefer `.docx` when the user has both. If the file extension is not `.docx` or `.pdf`, tell the user the platform only supports `.docx` / `.pdf` and ask for a valid file.

Before uploading, verify that `file_path` exists and is a file. If it does not exist, ask the user for the correct path.

## Upload Request

Send the upload through `storyboard_api` with `multipart=true`.

Required form fields:

| Field | Value |
| --- | --- |
| `name` | `<script_name>` |
| `file` | file contents from `<file_path>` |
| `style` | selected style: `真人写实`, `3d国漫`, or `2d动漫` |
| `ratio` | selected ratio: `16:9` or `9:16` |
| `workspaceId` | selected workspace id from `/api/workspaces` |
| `teamUserIds` | `[]` unless the user explicitly specified visible members |

Do not manually set a `Content-Type` boundary or Authorization header. `storyboard_api` handles multipart encoding and authentication.

Example form payload conceptually:

```text
name=梁山
file=@D:\scripts\梁山.docx
style=真人写实
ratio=16:9
workspaceId=1
teamUserIds=[]
```

## Base URL

Do not choose or print a base URL yourself. `storyboard_api` resolves the platform API base internally.

## Validation

Before calling the upload API:

- Trim surrounding whitespace from `script_name`.
- Reject script names containing path separators such as `/` or `\`.
- Verify `file_path` exists.
- Verify the file extension is `.docx` or `.pdf`.
- Verify `style` is exactly one of `真人写实`, `3d国漫`, `2d动漫`.
- Verify `ratio` is exactly one of `16:9`, `9:16`.
- Verify `workspaceId` exists in the latest `/api/workspaces` response.
- Keep the script name exactly as the user gave it after trimming.

## Success Response

Expected success fields:

- `success: true`
- `name`
- `episodes`
- `path`
- `style`
- `ratio`
- `workspaceId`

After a successful upload, reply with script name, episode count, style, ratio, and workspace id. Keep it concise.

Example reply:

```text
《梁山》已上传并解析完成，共 24 集，风格：真人写实，比例：16:9，工作空间 ID：1。
```

## Pitfalls

- **No direct token handling**: Never read token files, print token cache paths, construct Bearer headers, or use `token_response.json`. Use `storyboard_api` only.
- **Upload uses multipart form**: `/api/scripts/upload` requires multipart fields, but pass them through `storyboard_api` using `multipart=true`, `form`, `file_field`, and `file_path`.
- **Do not waste calls on web_search for auth problems**: Auth issues cannot be solved by web searching. Use `storyboard_api`; if it returns a login link, send that link to the user.

## Failure Handling

If the API returns an error, report the platform error directly and keep it actionable.

Common errors:

- `请输入剧本名称`: ask for the script name.
- `剧本名称不能包含路径符号`: ask for a plain script name without `/` or `\`.
- `请上传 .docx 或 .pdf 文档`: ask for a valid `.docx` or `.pdf` file.
- `当前账号没有可用的工作空间`: tell the user their account needs to be added to a workspace.
- `当前账号没有覆盖该剧本的权限`: tell the user they do not have permission to overwrite this script.
- `目标工作空间中已存在同名剧本目录`: ask the user to choose a different script name or workspace.
- `请先登录` / `登录已过期` / `授权凭证无效或已过期`: create and send a fresh Hermes login link, then retry after binding.



