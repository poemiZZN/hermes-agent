# MiniMax H3 基础模式格式

用于 `T2VA`、`I2VA`、`FL2VA` 和 `L2VA`。这些模式不输出 `subject_definitions`、`summary` 或 `retention_analysis`，最终提示词由可选的关键帧对齐指令和三个固定字段组成：

```text
integrated_multimodal_description: [Shot 1] ...

overall_soundscape: ...

non_diegetic_music: ...
```

字段名和格式保留字保持英文；描述性内容跟随用户源文本语言。除非用户明确说明或会话确实可见资产内容，否则不要描述参考图片中未确认的人物、场景、服装、物体或构图细节。

## 1. 关键帧对齐指令

`T2VA` 没有图片对齐指令，直接从三段式字段开始。

`I2VA` 首行必须为：

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.
```

`FL2VA` 首行必须为：

```text
How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot N) aligns with the S.SS-second mark of the target video.
```

`L2VA` 首行必须为：

```text
How the reference pictures align with the target video — <Picture 1> (from [Shot N]) aligns with the S.SS-second mark of the target video.
```

`N` 为实际最后一个镜头编号；`S.SS` 是有效总时长，固定两位小数。关键帧指令后空一行再开始三个字段。

## 2. 时间线主体

`integrated_multimodal_description` 按播放顺序写视觉、动作、镜头、说话人、对白、演唱和画内声音。`[Shot 1]` 开始时写整体风格和初始构图；后续镜头使用严格递增的 `[Shot N] At MM:SS.mmm, ...`。

- `I2VA`：从 `<Picture 1>` 的首帧状态出发，再描述连续发展。只保持已确认或用户明确指出的视觉属性。
- `FL2VA`：描述首帧到尾帧的可观察连续变化，通常使用单镜头；最后一帧必须落在 `<Picture 2>` 的状态与构图上。
- `L2VA`：先写与用户意图相容的前置状态，再通过动作、物体状态、运镜和构图逐步收束到最后镜头的 `<Picture 1>`。不要把尾帧误写成首帧。
- 运镜以自然句子写出移动方式、必要时的幅度和速度，例如 `The camera pushes in with small amplitude at slow speed ...`。只有用户明确要求时使用淡入、叠化或擦除等转场。

## 3. 声音、对白与画面文字

- 实际发声源按首次发声顺序分配 `(S1)`、`(S2)`；多人同时发声可写 `(S1,S2)`。不发声的角色不分配 ID。
- 对白或歌词使用 `<d>[Language] ...</d>`，保持用户提供原话。画外音使用 `says in an off-screen voiceover`，并说明对应画面主体嘴唇保持闭合。
- 屏幕中确实可见的文字用英文双引号包裹并保持原文。
- `overall_soundscape` 用 1-4 个连续句概括全片环境、物理和非语言人声；不重复对白、演唱或画内音乐。
- `non_diegetic_music` 用 1-3 个连续句说明观众配乐的乐器、速度、节奏和动态；没有时使用 `N/A`。
