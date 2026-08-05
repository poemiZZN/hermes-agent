---
name: character-three-view
description: "Use when the user asks to turn one full-body character image into a character reference sheet, character three-view, 三视图, 人设三视图, 半身特写加全身三视图, or wants the ready-to-use three-image character-sheet workflow on the Storyboard platform."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [storyboard, character-sheet, character-design, three-view, 人设三视图, 生图]
    related_skills: [art-asset-production, character-design-prompt]
---

# 人设三视图生成

将一张人物全身图生成三份可交付图片，顺序固定为：

1. 完整人设图：半身特写在左、全身三视图在右。
2. 半身特写图。
3. 全身三视图。

仅在用户明确要生成三视图、人设图或角色设定图时使用。这个 Skill 会实际提交图片任务；不要只写提示词冒充已经生成。

## 使用的工具

只使用平台已注册的工具：

- `storyboard_api`：准备固定参考图、校验输入图、提交带自定义尺寸的生图任务、查询任务结果及拼接最终图片。
- `canvas_image_generate`：当平台版本不需要自定义 `size` 时可作为后备；本流程优先使用 `storyboard_api`，以保证三视图的固定尺寸。

认证、平台地址和密钥由工具处理。不要读取环境变量、Token 文件或直接构造 Authorization 请求头。

## 必要输入

- 一张可访问的**人物全身图** URL 或平台图片资产。
- 当前剧本名。嵌入平台会话优先使用当前上下文中的剧本名。
- 分辨率：`1K` 或 `2K`。

用户未指定分辨率时，只询问一次：`请选择 1K 或 2K。`

输入图必须是单一、清晰可辨的人物全身图。用户只提供文字、头像、半身图、多人图或无法访问的图片时，不要开始生图，先索取一张合格全身图。

## 固定规格

使用逻辑模型 `gpt-image-2-c2`，质量 `high`，输出格式 `png`，每个阶段只生成一张图片。

| 选项 | 半身特写 Size | 全身三视图 Size | 最终拼图 Size |
| --- | --- | --- | --- |
| `1K` | `688x1088` | `1216x1088` | `1920x1080` |
| `2K` | `928x1440` | `1600x1440` | `2560x1440` |

这些 Size 都必须保持：最长边不超过 `3840`、两个边都为 `16` 的倍数、长短边比不超过 `3:1`。不要自行替换为未校验的尺寸。

固定提示词，不增删、不改写：

```text
半身特写：给图片1生成一张人物设定大头照，大头照的构图参考图片2，保持人物一致性
全身三视图：给图片1生成一张人物设定全身三视图，三视图的站姿和构图参考图片3，保持人物一致性
```

## 执行流程

### 1. 先验证输入图片

在任何生图请求前调用：

```text
storyboard_api(
  endpoint="/api/canvas/character-sheet/validate-source",
  method="POST",
  body={"scriptName":"<script_name>","image_url":"<source_image_url>"}
)
```

- 仅当返回 `success: true` 且 `is_full_body: true` 时继续。
- `is_full_body: false` 时立即停止，回复用户：`请换一张人物全身图后再生成三视图。`
- 校验接口失败时直接报告可操作的错误，不要跳过校验或用模型自行猜测。

### 2. 获取两张固定构图参考图

调用：

```text
storyboard_api(
  endpoint="/api/canvas/character-sheet/references",
  method="GET",
  query={"scriptName":"<script_name>"}
)
```

响应中的 `ref1.url` 是全身三视图构图参考，`ref2.url` 是半身特写构图参考。缺少任一 URL 时停止并报告固定参考图准备失败。

### 3. 生成半身特写图

提交：

```text
storyboard_api(
  endpoint="/api/canvas/generate",
  method="POST",
  body={
    "scriptName":"<script_name>",
    "prompt":"给图片1生成一张人物设定大头照，大头照的构图参考图片2，保持人物一致性",
    "model":"gpt-image-2-c2",
    "size":"<portrait_size>",
    "resolution":"<1K_or_2K>",
    "quality":"high",
    "output_format":"png",
    "n":1,
    "reference_images":[
      {"url":"<source_image_url>","name":"人物全身图.png"},
      {"url":"<ref2_url>","name":"半身特写构图参考.png"}
    ]
  }
)
```

`<portrait_size>` 按上表选择。请求成功但返回 `submitted: true` 时，保存 `task_id` 并进入轮询；不能假设提交成功即已拿到图片。

### 4. 轮询单个图片任务

对每个异步任务调用：

```text
storyboard_api(
  endpoint="/api/canvas/image/generate/<task_id>/status",
  method="GET",
  query={"scriptName":"<script_name>"}
)
```

- 每 5 秒查询一次。
- 返回 `done: true` 且 `success: true` 时，从 `images[0].image`（或等价的 `data[0].image`）读取图片 URL。
- 返回终态失败、`success: false` 或没有图片 URL 时停止；不要继续下一阶段，也不要静默改用其他模型。
- 等待期间只简短告知正在生成，最多持续 5 分钟；超过后告诉用户任务仍在平台处理中，并保留任务由平台后续显示。

### 5. 生成全身三视图

半身特写完成后，提交：

```text
storyboard_api(
  endpoint="/api/canvas/generate",
  method="POST",
  body={
    "scriptName":"<script_name>",
    "prompt":"给图片1生成一张人物设定全身三视图，三视图的站姿和构图参考图片3，保持人物一致性",
    "model":"gpt-image-2-c2",
    "size":"<turnaround_size>",
    "resolution":"<1K_or_2K>",
    "quality":"high",
    "output_format":"png",
    "n":1,
    "reference_images":[
      {"url":"<source_image_url>","name":"人物全身图.png"},
      {"url":"<portrait_image_url>","name":"半身特写图.png"},
      {"url":"<ref1_url>","name":"全身三视图构图参考.png"}
    ]
  }
)
```

`<turnaround_size>` 按上表选择。严格保持参考图顺序：原始全身图、刚生成的半身特写、`ref1`。之后按步骤 4 轮询到获得全身三视图 URL。

### 6. 拼接并返回三张图片

调用：

```text
storyboard_api(
  endpoint="/api/canvas/character-sheet/compose",
  method="POST",
  body={
    "scriptName":"<script_name>",
    "resolution":"<1k_or_2k>",
    "portrait_url":"<portrait_image_url>",
    "turnaround_url":"<turnaround_image_url>"
  }
)
```

`resolution` 只能是小写 `1k` 或 `2k`。接口会按指定最终尺寸，将半身图置于左侧、全身三视图置于右侧，并返回：

```text
images.combined.image
images.portrait.image
images.turnaround.image
```

交付顺序必须是 `combined`、`portrait`、`turnaround`。不要把中间原始参考图、任务 ID、上游模型 ID 或调试信息当作交付内容。

## 失败与授权

- `needsLogin: true` 且有 `loginUrl`：只把授权链接发给用户，待用户完成绑定后从原步骤重试。
- 输入校验不通过：不产生任何图片任务。
- 第一阶段失败：不启动第二阶段或拼接。
- 第二阶段失败：不拼接；可告知半身特写已经生成，但不要把它误报为完整三视图。
- 拼接失败：保留两张已完成图片的链接，并明确完整人设图未生成。

## 回复约束

成功后简洁说明已生成，并按以下顺序展示可访问链接：完整人设图、半身特写图、全身三视图。不要说“已完成”直到拼接接口成功返回三张图片。
