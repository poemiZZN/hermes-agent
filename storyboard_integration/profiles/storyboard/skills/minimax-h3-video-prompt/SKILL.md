---
name: minimax-h3-video-prompt
description: "Use when the user asks to write, rewrite, improve, or validate a MiniMax H3 video-generation prompt, including T2VA, I2VA, FL2VA, L2VA, and full-reference Ref2VA prompts with image, video, or audio references; 全参考模式, 视频提示词, 分镜提示词, 图生视频, 首尾帧, 尾帧, 视频续写, 视频编辑, 音频参考, or 人物一致性."
metadata:
  hermes:
    tags: [minimax, h3, video, video-prompt, full-reference, 图生视频, 视频提示词]
    related_skills: [seedance-2.0, character-design-prompt]
---

# MiniMax H3 视频提示词

构建可直接提交给 MiniMax H3 的视频提示词。优先交付最终提示词；除非用户要求，不解释通用提示词知识。

## 先确定输入模式

根据资产在目标视频中的实际作用选择一种模式：

| 模式 | 适用情况 | 参考文件 |
| --- | --- | --- |
| `T2VA` | 仅文字生成完整视听时间线 | `references/base-prompt-format.md` |
| `I2VA` | 图片是明确首帧，从首帧向后发展 | `references/base-prompt-format.md` |
| `FL2VA` | 两张图片分别是明确首帧与尾帧，生成连续过渡 | `references/base-prompt-format.md` |
| `L2VA` | 图片是明确尾帧，前文收束到该画面 | `references/base-prompt-format.md` |
| `Ref2VA` | 资产定义人物、场景、风格、动作、分镜、源视频编辑/续写或音频关系 | `references/full-reference-format.md` |

- 不要只因存在图片就使用 `Ref2VA`；首帧、首尾帧、尾帧任务优先选对应的基础模式。
- 不要只因存在视频或音频就写 `video editing`、`video continuation` 或 `audio reuse`；只有直接编辑、续写或复制原始信号时才使用这些关系。
- 资产同时承担多个独立保留关系，或用户明确要求全参考、人物/场景一致性、源视频或音频复用时，使用 `Ref2VA`。

## 参考资产的事实边界

只有用户明确描述，或当前会话确实能看见参考资产内容时，才能写入角色、场景、服装、道具、构图等视觉特征。看不到或无法确认时，只写资产的功能、来源和镜头关系，例如 `<Picture 1> is the first-frame reference for [Shot 1].`；不要根据文件名、相邻资源、上下文或常识猜测画面内容。

同样不要把未确认画面内容转写为新的角色、场景、动作或保留要求。用户提供的是首帧或尾帧时，可以说明目标视频从该帧开始或最终落在该帧，但不虚构该帧内的视觉细节。

## 收集最少必要信息

确认尚未提供的关键项：目标事件、主体和地点；资产的实际作用；视频关系；对白、歌词、原音或音色；以及用户指定的时长、镜头、风格、比例和结尾画面。已提供的信息不得重复追问；未指定项采用克制且连续的默认设定。

## 共同写作规则

1. 先完成可见与可听的播放时间线，再补充环境声和非画内配乐。不要只交付剧情概要。
2. `[Shot 1]` 不写时间戳；后续镜头使用 `[Shot N] At MM:SS.mmm, ...`，切镜时间严格递增且不超过总时长。只有新信息、时空、视角或状态变化时才切镜，微小视角变化优先写运镜。
3. 每个镜头交代构图、主体位置、环境与光线、动作与状态变化、运镜、同步声音，以及参考内容生效的位置。运镜自然写入句子；需要时同时说明方式、幅度和速度。
4. 实际发声源按首次发声顺序分配稳定 `(S1)`、`(S2)`。对白与歌词使用 `<d>[Language] ...</d>`；保持用户提供的原文，听不清写 `[unclear]`。画外音必须使用 `says in an off-screen voiceover`，并说明画面内角色嘴唇保持闭合。
5. 对白跨镜时使用 `<scenetrans>` 并说明声音连续；视频结尾截断发声时使用 `<cutoff>`。屏幕内可见文字用英文双引号并保留原文。
6. `overall_soundscape` 只概括持续环境音、物理声和非语言人声；`non_diegetic_music` 只写角色听不到的观众配乐。完整对白和歌词只出现在镜头正文中。

## 语言与格式

- 保留字必须使用英文：模式名、字段名、`<Subject N>`/`<Picture N>`/`<Video N>`/`<Audio N>`、任务类型、关系标记、`[Shot N]`、`At MM:SS.mmm`、`(Sx)`、`<d>`、`[Language]`、`<scenetrans>`、`<cutoff>` 和 `N/A`。
- 除保留字外，描述性文本跟随用户源文本语言；用户输入混合语言或无法判断时使用中文。这是本平台的输出兼容规则，优先于官方示例的全英文叙述约定。
- 对白、歌词和可见文字始终保留原始语言。不要翻译、改写或补全用户直接提供的台词。

## 交付前检查

- 模式与资产真实用途一致，选中的格式完整且字段顺序正确。
- 标签、保留分析、镜头描述和声音章节含义一致；不引入未定义标签。
- 时长、时间码、镜头顺序、说话人 ID 和音频连续性一致。
- 没有根据不可见或未说明的参考资产补造视觉内容。

基础模式模板见 `references/base-prompt-format.md`；全参考标签、保留关系和六段格式见 `references/full-reference-format.md`。
