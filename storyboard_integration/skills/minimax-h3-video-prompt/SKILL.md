---
name: minimax-h3-video-prompt
description: "Use when the user asks to write, rewrite, improve, or validate a MiniMax H3 video-generation prompt, especially for prompts using image, video, or audio references; 全参考模式, 视频提示词, 分镜提示词, 图生视频, 视频续写, 视频编辑, 音频参考, or 人物一致性."
metadata:
  hermes:
    tags: [minimax, h3, video, video-prompt, full-reference, 图生视频, 视频提示词]
    related_skills: [seedance-2.0, character-design-prompt]
---

# MiniMax H3 视频提示词

构建可直接提交给 MiniMax H3 的视频提示词。优先交付最终提示词，不解释通用提示词知识，除非用户要求说明。

## 先确定模式

- 用户提供或要求使用图片、视频、音频参考时，使用**全参考模式**。读取 `references/full-reference-format.md`，并严格输出六个章节。
- 用户没有参考资产时，写简洁的英文镜头提示词。不要虚构 `<Subject N>`、`<Picture N>`、`<Video N>` 或 `<Audio N>` 标签，也不要输出全参考的 `retention_analysis`。

把用户上传的资产按用途映射：人物、场景、服装/道具、首帧/关键帧/尾帧、源视频剪辑或续写、音色/原音/配乐。无法判断资产用途时，只问一个最关键的问题。

## 收集最少必要信息

在开始前确认缺失的关键项：

- 目标事件、主体和地点。
- 参考资产分别提供什么内容，以及哪些特征必须保持。
- 视频关系：生成、关键帧补全、编辑，或续写。
- 是否存在对白、歌词、原音复用或音色参考。
- 用户明确指定的时长、镜头、风格、比例或结尾画面。

用户已提供的信息不得重复追问。没有指定的风格、时长、镜头或声音，使用克制而连贯的默认设定，不要为了填模板编造复杂剧情。

## 全参考模式工作流

1. 给实际会在目标视频中出现或起作用的参考内容建立稳定标签。视觉内容用 `<Subject N>`；具体帧锚点用 `<Picture N>`；剪辑/续写/结构来源用 `<Video N>`；独立声音参考用 `<Audio N>`。
2. 选择与真实关系一致的任务类型前缀。不要因为有视频或音频文件就误写 `video editing`、`video continuation` 或 `audio reuse`。
3. 用英文依次输出：`subject_definitions`、`summary`、`retention_analysis`、`detailed_description`、`overall_soundscape`、`non_diegetic_music`。
4. 在 `detailed_description` 中按时间顺序写镜头。每个镜头明确构图、人物/物体位置、环境、光线、动作变化、运镜、同步声音和参考标签生效的位置。
5. 对实际发声源按首次发声顺序分配 `(S1)`、`(S2)` 等，并在后续镜头复用。对白和歌词放入 `<d>[Language] ...</d>`；直接复用的歌词/对白必须保留原话，听不清则写 `[unclear]`。

## 输出约束

- 全参考模式的六个章节和描述正文使用英文。仅 `<d>` 内的对白/歌词及画面可见文本保留原语言。
- 不要引入未定义的参考标签，不要改变同一标签的含义，不要在 `retention_analysis` 写 `(Sx)`。
- 生成类的 `detailed_description` 通常为 350-500 个英文词；以镜头和对白信息完整为优先。
- 不要把整段对白或歌词同时写入 `overall_soundscape` 或 `non_diegetic_music`。
- 只描述用户提供或合理推断的内容；不把新剧情、背景或动作错误标记为参考保留失败。

## 交付前检查

在输出前逐项检查：

- 六个章节齐全且顺序正确（仅全参考模式）。
- 标签定义、摘要、保留分析和镜头描述完全一致。
- 每个保留分析条目只使用允许的关系标记。
- `[Shot 1]` 无时间戳；后续切镜使用 `At MM:SS.mmm`。
- 每个说话人 ID 稳定，对白语言和标点正确。
- 声场、同步声和非画内配乐没有混淆。

全参考模式的标签、关系标记、镜头格式和模板见 `references/full-reference-format.md`。
