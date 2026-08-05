---
name: character-three-view
description: "Use when the user asks to turn one full-body character image into a character reference sheet, character three-view, 三视图, 人设三视图, 半身特写加全身三视图, or wants the ready-to-use three-image character-sheet workflow on the Storyboard platform."
version: 1.1.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [storyboard, character-sheet, character-design, three-view, 人设三视图, 生图]
    related_skills: [art-asset-production, character-design-prompt]
---

# 人设三视图生成

将一张人物全身图通过后端聚合任务生成三份可交付图片，顺序固定为：

1. 完整人设图：半身特写在左、全身三视图在右。
2. 半身特写图。
3. 全身三视图。

仅在用户明确要生成三视图、人设图或角色设定图时使用。这个 Skill 会实际提交一个聚合任务；不要只写提示词冒充已经生成，也不要自行拆成多次图片请求。

## 使用的工具

只使用平台已注册的 `storyboard_api`。后端聚合接口负责准备固定参考图、两阶段 C2 生图、图片任务轮询和最终拼接；不要由 Hermes 单独提交两次生图任务。

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

### 2. 提交聚合任务

调用一次接口。它会在后台完成固定参考图准备、半身特写、全身三视图、每一阶段的轮询以及最终拼接：

```text
storyboard_api(
  endpoint="/api/canvas/character-sheet/generate",
  method="POST",
  body={
    "scriptName":"<script_name>",
    "resolution":"<1k_or_2k>",
    "source_image":{
      "url":"<source_image_url>",
      "name":"人物全身图.png"
    }
  }
)
```

成功提交后保存响应中的 `task_id`。不要自行调用 `/api/canvas/generate`、`/references` 或 `/compose`，也不要生成额外图片。

### 3. 轮询聚合任务

每 5 秒调用：

```text
storyboard_api(
  endpoint="/api/canvas/character-sheet/generate/<task_id>/status",
  method="GET",
  query={"scriptName":"<script_name>"}
)
```

- `task.status` 为 `pending` 或 `running` 时，读取 `task.message` 作为当前阶段状态。
- `task.status` 为 `succeeded` 时，从以下字段按顺序交付三张图：

```text
task.images.combined.image
task.images.portrait.image
task.images.turnaround.image
```

- `task.status` 为 `failed` 时停止并直接反馈 `task.error`，不要补发或改用其他模型。
- 单个聚合任务由后端最多等待 20 分钟完成两阶段生图；Hermes 不应另起重复任务。

交付顺序必须是 `combined`、`portrait`、`turnaround`。不要把中间原始参考图、任务 ID、上游模型 ID 或调试信息当作交付内容。

## 失败与授权

- `needsLogin: true` 且有 `loginUrl`：只把授权链接发给用户，待用户完成绑定后从原步骤重试。
- 输入校验不通过：不产生任何图片任务。
- 第一阶段失败：不启动第二阶段或拼接。
- 第二阶段失败：不拼接；可告知半身特写已经生成，但不要把它误报为完整三视图。
- 拼接失败：保留两张已完成图片的链接，并明确完整人设图未生成。

## 回复约束

成功后简洁说明已生成，并按以下顺序展示可访问链接：完整人设图、半身特写图、全身三视图。不要说“已完成”直到拼接接口成功返回三张图片。使用![](<url>) Markdown 语法展示图片。
