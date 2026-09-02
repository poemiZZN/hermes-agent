# MiniMax H3 全参考格式

仅在 `Ref2VA` 使用本格式。按固定顺序输出六个章节：

```text
subject_definitions:
...

summary:
...

retention_analysis:
...

detailed_description:
...

overall_soundscape:
...

non_diegetic_music:
...
```

章节名、标签、任务类型、关系标记、镜头和时间格式保持英文。其他描述文字遵循用户源文本语言；对白、歌词和画面内文字保持原文。除本项目语言规则外，本格式遵循 MiniMax H3 官方 `Ref2VA` 结构。

## 1. 标签与定义

| 标签 | 作用 | 不要用于 |
| --- | --- | --- |
| `<Subject N>` | 目标视频中实际复用或改写的可见内容：人物、物体、场景、服装、风格、动作、表情或特效 | 仅代表源文件 |
| `<Picture N>` | 首帧、关键帧、尾帧、编辑帧、构图锚点或分镜参考 | 只提供人物、场景或风格特征的图片 |
| `<Video N>` | 源视频编辑、续写起点、全片节奏、镜头或剪辑结构 | 替代视频中可见的主体 |
| `<Audio N>` | 复制或参考的独立音频信号、同步音轨、音色、音乐、对白、歌词、音效或节奏 | 因视频文件含声音而自动创建 |

- 每个实际需要追踪的内容单独定义一行；同一标签在全部章节含义一致。
- 一个 `<Subject N>` 可以来自多个资产；同一资产也可提供多个 `<Subject N>`。
- 如果 `<Picture N>` 或 `<Video N>` 仅用来说明某个 Subject 的来源、后文不独立分析，就在该 Subject 定义中引用它，不要另建独立条目。
- 只有确认资产内容后才能描述视觉属性。无法确认时，只描述功能和关系：

```text
<Picture 1> is the first-frame reference for [Shot 1].
<Subject 1> is the character represented by <Picture 1>; visible attributes are preserved without adding unverified details.
```

- `<Audio N>` 对应实际说话主体时，复用目标视频的全局 `(Sx)`；音频定义不独立分配说话人 ID。同一源视频的 `<Video N>` 和 `<Audio N>` 独立编号。

## 2. `summary`

用一个短段落，以方括号中的任务类型开始。多个真实关系以 ` + ` 连接且不重复：

| 类型 | 何时使用 |
| --- | --- |
| `keyframe completion` | 图片是首帧、关键帧、尾帧或其他具体帧锚点 |
| `reference generation` | 资产提供人物、场景、风格、动作、镜头、分镜或节奏引导，但不是具体帧，也不直接编辑/续写 |
| `video editing` | 直接修改或剪辑源视频 |
| `video continuation` | 从源视频继续、延长、恢复或过渡 |
| `audio reuse` | 完整或部分直接复用原始音频信号 |
| `audio reference` | 只参考音色、音乐风格、节奏、歌词/对白内容、音效质感或声音连续性 |

仅参考视频节奏、运镜或剪辑时通常为 `reference generation`。编辑源视频且保留原音时同时写 `audio reuse`。视频编辑任务在类型后以 `The target video is an edited version of <Video 1>.` 开始。

## 3. `retention_analysis`

每个实际相关标签独占一行。视觉标签 `<Subject N>`、`<Picture N>`、`<Video N>` 只使用：`fully_preserved`、`partially_preserved`、`attribute_transfer`、`weak_reference`。音频标签 `<Audio N>` 只使用：`fully_copy`、`partially_copy`、`reference`、`weak_reference`。

```text
<Subject 1> (appears in [Shot 1], [Shot 2]): fully_preserved - ...
<Picture 1> ([Shot 1] first frame): fully_preserved - ...
<Video 1> (cut and pacing structure): weak_reference - ...
<Audio 1>: reference - ...
```

选择的关系必须符合 `subject_definitions` 中的角色。新剧情、背景或动作不等于参考保留失败。不要在本章节写 `(Sx)`。

## 4. `detailed_description`

先用一两句建立整体视觉风格，再按播放顺序写镜头。生成任务通常为 350-500 个英文词等量的信息密度；对白密集时以完整时序为先，视频编辑可随源片复杂度调整。

- `[Shot 1]` 无时间戳；后续镜头使用 `[Shot N] At MM:SS.mmm, ...`。
- 在重要 `<Subject N>` 首次清晰出现时，描述已确认的参考特征、画面位置和当前动作；后续只复用标签，不重新定义。
- 帧锚点自然写为 `the shot begins from <Picture 1>`、`the shot's keyframe corresponds to <Picture 2>` 或 `the shot ends on <Picture 3>`。
- 编辑或续写时，在源状态、结构或衔接处引用 `<Video N>`；音频关系生效时引用 `<Audio N>`。
- 实际发声主体使用 `<Subject N> (Sx)`；不对应 Subject 的声音使用稳定描述加 `(Sx)`。直接复用的背景音乐或完整原声若没有独立发声主体，只引用 `<Audio N>`，不要凭空新增 `(Sx)`。
- 直接复用或用户明确要求复演的台词/歌词必须保留原话；听不清写 `[unclear]`。只参考音色、节奏或情感时，不带入原参考音频的台词。

## 5. 声音章节

`overall_soundscape` 使用连续段落概括环境音、物理声和非语言人声。`non_diegetic_music` 说明角色听不到的配乐之乐器、速度、节奏和动态。无非画内配乐时写 `N/A`；只有用户明确要求全程完全静音时才在 `overall_soundscape` 写 `N/A`。

复用或参考的声音必须放入相应章节：环境/音效归 `overall_soundscape`，观众配乐归 `non_diegetic_music`。完整对白和歌词只写在 `detailed_description` 的 `<d>` 中。
