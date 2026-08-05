---
name: character-three-view
description: "Use when the user asks to turn one full-body character image into a character reference sheet, character three-view, 三视图, 人设三视图, 半身特写加全身三视图, or wants the ready-to-use three-image character-sheet workflow on the Storyboard platform."
version: 1.2.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [storyboard, character-sheet, character-design, three-view, 人设三视图, 生图]
    related_skills: [art-asset-production, character-design-prompt]
---

# 人设三视图生成

仅在用户明确要生成三视图、人设图或角色设定图时使用。使用原生工具
`character_three_view_generate`，不要改用 `storyboard_api` 或
`canvas_image_generate` 手动拆分流程。

## 必要输入

- 一张可访问的、单一人物的清晰全身图 URL 或平台图片资产。
- 分辨率：`1K` 或 `2K`。

嵌入平台会话优先使用当前上下文中的剧本名，不要向用户追问或自行编造剧本名。

用户没有提供合格的全身图时，说明需要一张单人全身图后停止。用户未指定分辨率时，只询问一次：`请选择 1K 或 2K。`

## 调用

输入齐全后只调用一次：

```text
character_three_view_generate(
  source_image_url="<人物全身图 URL>",
  source_image_name="<可选文件名>",
  resolution="<1K 或 2K>"
)
```

工具会自行验证全身图，并由平台后端完成固定参考图准备、半身特写、全身三视图和最终拼接。不要自行提交额外生图请求或查询中间任务。

## 回复约束

- 成功提交后简洁告知用户正在生成；前端会自动展示完成的完整人设图、半身特写图和全身三视图。
- 不要在回复中提及任务 ID、Job ID、请求 ID、模型 ID、固定提示词或内部接口路径。
- 工具返回授权链接时，只发送授权链接，等待用户完成授权后从原调用重试。
- 工具返回“请换一张人物全身图”时，直接向用户索取合格全身图，不要继续生成。
