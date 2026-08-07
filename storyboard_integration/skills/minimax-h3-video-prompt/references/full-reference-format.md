# MiniMax H3 全参考格式

仅在任务使用图片、视频或音频参考时使用本格式。六个章节必须按以下顺序输出，章节名称保持英文：

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

除 `<d>` 内对白/歌词与画面中可见文字外，所有内容使用英文。

## 1. 参考标签

| 标签 | 用途 | 不要用于 |
| --- | --- | --- |
| `<Subject N>` | 实际出现在目标视频中的人物、动物、物体、场景、服装、风格、动作或特效 | 仅标识源文件 |
| `<Picture N>` | 首帧、关键帧、尾帧、改写帧或明确构图锚点 | 仅提供人物或风格特征的图片 |
| `<Video N>` | 被剪辑的源视频、续写起点、全片节奏或剪辑结构来源 | 替代视频中的人物、场景或物体主体 |
| `<Audio N>` | 原音复用、音色、音乐、对白、歌词、音效或节奏参考 | 自动代表每一个带声音的视频 |

在 `subject_definitions` 中一行定义一个实际需要追踪的内容。标签一经定义，在后文保持相同含义。

```text
<Subject 1> is the young woman in <Picture 1>, with a navy cardigan, long dark hair, and a thin silver necklace.
<Picture 2> is the first frame of [Shot 1], defining the café-window composition.
<Video 1> is the source video whose final moment the target video continues from.
<Audio 1> is the voice-timbre reference for <Subject 1> (S1).
```

## 2. `summary` 的任务类型

以方括号开头；多个真实关系用 ` + ` 组合且不重复：

| 类型 | 何时使用 |
| --- | --- |
| `keyframe completion` | 图片是首帧、关键帧、尾帧或其他具体帧锚点 |
| `reference generation` | 资产提供人物、场景、风格、动作、镜头或分镜引导，但不是具体帧，也不被直接剪辑/续写 |
| `video editing` | 直接修改或剪辑源视频 |
| `video continuation` | 从源视频继续、延长或过渡 |
| `audio reuse` | 直接复制完整或部分音频信号 |
| `audio reference` | 仅参考音色、音乐风格、节奏、歌词/对白内容或音效质感 |

```text
[reference generation + audio reference] The target video follows <Subject 1> through a quiet café, using <Audio 1> only for her vocal timbre.
```

仅参考视频节奏或运镜时通常是 `reference generation`。源视频被编辑且原音清晰保留时，同时写 `audio reuse`。

## 3. `retention_analysis`

每个已定义且实际相关的标签独占一行。视觉标签只使用以下关系：

| 关系 | 含义 |
| --- | --- |
| `fully_preserved` | 定义特征完整保留 |
| `partially_preserved` | 仍被使用，但部分特征改变或缺失 |
| `attribute_transfer` | 特征被转移到另一个可识别主体 |
| `weak_reference` | 仅保留大致风格、类别、构图或氛围 |

音频标签只使用：`fully_copy`、`partially_copy`、`reference`、`weak_reference`。

```text
<Subject 1> (appears in [Shot 1], [Shot 2]): fully_preserved - her navy cardigan, long dark hair, and silver necklace remain unchanged.
<Picture 2> ([Shot 1] first frame): fully_preserved - the opening composition matches the reference frame.
<Audio 1>: reference - its vocal timbre guides <Subject 1>'s delivery without copying the source signal.
```

不要把新加入的剧情、背景或动作误判为参考保留失败。不要在这里写 `(Sx)`。

## 4. `detailed_description`

先用一两句建立整体视觉风格，再按播放顺序写镜头：

```text
The target video uses a naturalistic cinematic style with soft late-afternoon window light and restrained handheld movement.
[Shot 1] A medium shot establishes <Subject 1> beside the café window. ...
[Shot 2] At 00:03.000, the shot cuts to a close-up of <Subject 1>. ...
```

- `[Shot 1]` 不写时间戳；后续镜头使用 `[Shot N] At MM:SS.mmm, ...`。
- 每个镜头写清构图、可见主体及位置、环境与光线、动作和状态变化、运镜、同步声音，以及参考标签何时出现或起作用。
- 重要主体首次清晰出现时，结合 `<Subject N>` 描述其可见参考特征。后续只复用标签，不要重新定义。
- 具体帧锚点自然写作 `the shot begins from <Picture 1>`、`the shot's keyframe corresponds to <Picture 2>` 或 `the shot ends on <Picture 3>`。
- 生成类任务通常 350-500 英文词；视频编辑可按源视频复杂度伸缩。

### 说话人和对白

为实际发声源按首次发声顺序分配一次 `(S1)`、`(S2)`，之后始终复用。参考主体开口时写 `<Subject N> (Sx)`；画外说话保留该形式并写明 `off-screen`。

```text
<Subject 1> (S1) looks toward the door and says, <d>[Chinese] 你终于来了。</d>
```

直接复用的对白或歌词必须原样保留；听不清写 `[unclear]`。只参考音色、节奏或情感时，不要把原参考音频的台词带入目标视频。直接复用的背景音乐或完整原音中没有独立说话人的语音，可只引用 `<Audio N>`，不要凭空建立 `(Sx)`。

## 5. 声音章节

`overall_soundscape` 只概括持续环境音和物理发声：

```text
overall_soundscape: Quiet café room tone, soft cup clinks, and a low ventilation hum continue throughout.
```

`non_diegetic_music` 只写角色听不到的观众配乐；说明配器、速度和动态。没有时写 `N/A`。

```text
non_diegetic_music: A restrained solo-piano score at a slow tempo, with sustained low cello and no dramatic swell.
```

不要在这两个章节重复完整对白或歌词；它们只放在 `detailed_description` 的 `<d>` 中。
