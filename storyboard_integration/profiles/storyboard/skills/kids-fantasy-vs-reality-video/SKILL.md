---
name: kids-fantasy-vs-reality-video
description: >-
  Generate nostalgic childhood memory short-form video scripts for AI video generation
  (wan3.0, MiniMax H3, Seedance, Kling). All scripts use Minecraft blocky voxel pixel
  art style, vertical-first framing, model-locked duration (MiniMax H3 2×15s segments;
  wan3.0 one 30s video),
  and American English vocals. Covers 5 categories
  of universally resonant childhood content: (1) Fantasy vs Reality — What I see it vs
  What parents see it, (2) Growing Up Stories — sibling rivalry, parent-child bonds,
  family rituals, (3) First Time vs Master — terrified beginner → competent routine →
  confident master, (4) Childhood Fears — dark staircases, midnight bathroom runs,
  closet doors, mirror games, under the bed, (5) Sneaky Childhood Wins — finding money,
  canceled plans, biggest slice, crush looked at you. Use when the user asks for
  childhood memory videos, kids nostalgia content, Minecraft-style short video scripts,
  童年回忆, 儿时记忆, 暗爽瞬间, 童年阴影, 成长故事, or any childhood contrast/comparison
  video concepts.
metadata:
  agent_created: true
  version: 1.3.0
---

# Childhood Memory Video Script Generator

Generate universally resonant short-form video scripts about childhood memories. All scripts use Minecraft blocky voxel pixel art style, vertical-first framing, American English, and emotionally satisfying endings. Prompt-only output defaults to 9:16, but MiniMax H3 generation uses the aspect ratio explicitly confirmed by the user. Duration is fixed by model: MiniMax H3 uses two 15-second segments per story; wan3.0 uses one 30-second video per story.

## Trigger Conditions

Invoke this skill when the user requests:
- "What I see it vs What parents see it" contrast videos
- Childhood memory / nostalgia video scripts
- Minecraft-style short video scripts about growing up
- Sibling rivalry, sibling bonding, parent-child moments
- First time → master, skill progression, before vs after
- Childhood fears, scary moments, monsters, dark hallways
- Sneaky wins, secretly satisfying moments
- 童年回忆 / 儿时记忆 / 小时候 / 成长故事 / 童年阴影 / 暗爽瞬间 / 第一次VS无数次

## Five Content Categories

| Category | Theme | Hook | Beat Structure | Ending |
|----------|-------|------|---------------|--------|
| 1. Fantasy vs Reality | Kid's imagination vs parent's perspective | Epic fantasy → mundane reality | 6 beats: entrance → climax → transition → reality → flashback → split-screen | Parent's small gesture of love |
| 2. Growing Up Stories | Sibling rivalry, parent-child bonds, family rituals | Two family members, one moment | 4 beats: setup → conflict → turning point → warm resolution | Quiet moment of connection |
| 3. First Time vs Master | Terrified beginner → competent routine → confident master | Same person, same activity, three stages of skill | 3 stages × ~10s: crash → correct → cocky | Callback to the first failure |
| 4. Childhood Fears | Dark staircases, midnight bathrooms, closet doors, mirrors | Self-created terror — the monster is always in the imagination | 4 beats: setup → fear emerges → escape → safe (but is it?) | Ambiguous — the fear might be real |
| 5. Sneaky Childhood Wins | Finding money, canceled plans, biggest slice, crush looked | The quiet, secretly satisfying moments | 3 beats: setup → the win → the glow | Trying to play it cool, failing |

### Category 1: Fantasy vs Reality (example concepts)

See `references/category-1-all-20.md` for 20 example storylines. New content should be original.

| # | Fantasy | Reality | Punchline |
|---|---------|---------|-----------|
| ★ | Knight slaying Ender Dragon | Toddler on plastic rocking horse | "Same energy." |
| ★ | Astronaut exploring neon nebula | Child in cardboard box with salad bowl helmet | "Still exploring." |
| ★ | Superhero rescuing city | Diaper toddler in crooked Spider-Man mask | "Not all heroes wear capes." |
| ★ | Mad scientist creating rainbow potion | Child mixing cereal+ketchup+candy+cheese | "Science is messy." |
| ★ | Rock star at sold-out stadium | Child singing into hairbrush in bedroom | "Rock on, little legend." |

### Category 2: Growing Up Stories (example concepts)

See `references/category-2-all-20.md` for 20 example storylines. New content should be original.

| # | Storyline | Hook | Ending |
|---|-----------|------|--------|
| ★ | The Last Cookie | Two siblings, one cookie, epic standoff | "Siblings." |
| ★ | Dad's Secret Scar | Dad reveals his old scar to comfort a scraped-knee child | "We all have scars." |
| ★ | Mom's Midnight Snack | Caught sneaking snacks — Mom joins in | "Midnight alliance." |
| ★ | The Pillow Fort | Mom says bedtime — siblings build a kingdom | "Kingdom." |
| ★ | The Monster Check | Every night, Dad checks under the bed, closet, window | "Every night. No exceptions." |

### Category 3: First Time vs Master (example concepts)

See `references/category-3-all-20.md` for 20 example storylines. New content should be original.

| # | Storyline | Stage 1 | Stage 3 | Ending |
|---|-----------|---------|---------|--------|
| ★ | Riding a Bike | Crashes into bush, crying | No-hands wheelie | "From scraped knees to no hands." |
| ★ | Cooking | Egg explodes on counter | Omelet flip, chef's kiss | "From egg on face to chef's kiss." |
| ★ | Swimming | Falls in shallow water | Racing dive, cannonball | "From floaties to cannonballs." |
| ★ | Skateboarding | Falls on tiny ramp | Kickflips stairs | "From pillow armor to kickflips." |

### Category 4: Childhood Fears (example concepts)

See `references/category-4-all-20.md` for 20 example storylines. New content should be original.

| # | Storyline | Hook | Ending |
|---|-----------|------|--------|
| ★ | Running Up the Stairs | Turned off basement light. Something is coming. | "You know it's still there." |
| ★ | The Midnight Bathroom Run | 3 AM. The bathroom is at the end of the dark hallway. | "3:00 AM. Every night." |
| ★ | The Closet Door | It was closed. Now it's open. Just a crack. | "It was already open." |
| ★ | The Mirror Game | Don't say the name three times. | "It's just a game. Right?" |
| ★ | What's Under the Bed | Your foot is hanging off. Something touched it. | "You checked. It wasn't there. But it is now." |

### Category 5: Sneaky Childhood Wins (example concepts)

See `references/category-5-all-20.md` for 20 example storylines. New content should be original.

| # | Storyline | Hook | Ending |
|---|-----------|------|--------|
| ★ | Finding Money in Your Pocket | Hand goes into yesterday's jacket. Touches paper. | "Rich." |
| ★ | Teacher Called in Sick | You walk into class expecting a test. Substitute is at the desk. | "Free day." |
| ★ | Getting the Biggest Slice | Mom cuts the cake. Your slice is visibly larger. | "Jackpot." |
| ★ | Your Crush Looked at You | For 0.3 seconds, the universe aligned. | "They looked." |
| ★ | The Last-Minute Cancel | You didn't want to go anyway. Now you don't have to. | "Canceled." |

Individual sneaky-win stories are ~10-12s. For wan3.0, combine 2-3 scenes into one 30s video. For MiniMax H3, distribute 2-3 related scenes across two 15s segments.

## Output Formats

This skill supports two AI video generation formats. Choose based on the user's target model:

### wan3.0 Format (Multi-shot, 30s single prompt)

Use when the target is wan3.0-video. Read and follow the sibling [`wan3-drama-prompt-v2` skill](../wan3-drama-prompt-v2/SKILL.md) for the multi-shot structure and formatting rules.

- Category 1: 6-shot structure for a single 30s story.
- Categories 2, 4: 4-shot structure for a single 30s story.
- Category 3: 3-stage structure, ~10s per stage, calendar/time-lapse transition.
- Category 5: Combine 2-3 scenes into one 30s video using themed sequence.

### MiniMax H3 Format (2×15s Segmented T2VA)

Use when the target is MiniMax H3. Read and follow the sibling [`minimax-h3-video-prompt` skill](../minimax-h3-video-prompt/SKILL.md) for the H3 T2VA field structure and formatting rules.

- Category 1: Segment 1 is the 15s fantasy; Segment 2 is the 15s transition, reality, flashback, split-screen, and warm payoff.
- Categories 2, 4: Segment 1 contains the 15s setup and escalation; Segment 2 contains the 15s turning point/escape and resolution.
- Category 3: Segment 1 contains the first failure and competent-routine stages; Segment 2 contains the confident-master stage and callback.
- Category 5: Use two 15s segments, each containing 1-2 related sneaky-win scenes, with the second segment delivering the final glow.
- Output two separately copyable H3 prompts labeled `Segment 1 (15s)` and `Segment 2 (15s)`. Preserve character, setting, prop, audio, and opening/ending-state continuity between them.

H3 prompt field structure:
```text
integrated_multimodal_description: <visual timeline with shots, actions, camera, dialogue, diegetic sound>
overall_soundscape: <ambient sounds, 1-4 sentences>
non_diegetic_music: <background music, or N/A>
```

## Hard Constraints (Apply to All Output)

1. **Style**: Minecraft blocky voxel pixel art. Anchor phrase: `blocky voxel Minecraft scene`. Never use generic "pixel art" or "low-poly".
2. **Language**: All vocals and on-screen text in American English. Dialogue: `<d>[English] text</d>` (H3) or direct quotes (wan3.0).
3. **Aspect ratio**: Use 9:16 vertical for prompt-only drafts unless the user specifies another ratio. Before submitting a MiniMax H3 generation task, the aspect ratio must be explicitly confirmed; never silently reuse the draft default.
4. **Duration**: Duration is model-locked. Each MiniMax H3 story must contain exactly two independently generated 15-second segments; each H3 generation task is `duration=15`, never `duration=30`. Each wan3.0 story is one 30-second prompt and one generation task with `duration=30`. This rule overrides any conflicting example timing.
5. **Warm/Resonant ending**: Every storyline ends with an emotional payoff appropriate to the category.
6. **No extraneous text**: `No additional on-screen text or subtitles appear in the video beyond the opening subtitle.` — prevents AI-generated gibberish.
7. **Sound**: Always explicit audio. 8-bit chip music appropriate to mood. Non-diegetic music: single warm chord at ending.
8. **Subtitles**: Category 1 uses "What I see it" / "What parents see it" throughout. Categories 2-5 use a single evocative title at the end. Pixel font, white/black outline, bottom center.

## Music Selection by Mood

| Mood | 8-bit Style |
|------|------------|
| Epic / Heroic | Orchestral brass, timpani |
| Wonder / Awe | Synthwave, cosmic arpeggios |
| Tense / Rivalry | Spaghetti western guitar, ticking |
| Sneaky / Mischievous | Stealth bass, plucked strings |
| Cozy / Warm | Acoustic guitar, music box |
| Triumphant / Joyful | Orchestral swell, bells |
| Nostalgic / Bittersweet | Solo piano, wind chimes |
| Playful / Energetic | Chase music, stomping rhythm |
| Horror / Suspense | Dissonant strings, heartbeat, scraping |
| Ambiguous / Uneasy | Warped music box, deep bass rumble |

## Workflow — Pre-Generation Consultation (MANDATORY)

Before generating any prompt, always ask the user three questions in order. Do not skip any step.

### Step 1: Ask for Category

Display the 5 categories and ask the user to choose one:

> 请选择要生成的内容类别：
>
> **1. 幻想VS现实** — 小孩想象中的场景 vs 父母眼中的真实场景
> **2. 成长故事** — 兄弟姐妹、父母子女之间的家庭回忆
> **3. 第一次VS无数次** — 从小白到大师的三阶段蜕变
> **4. 童年阴影** — 关灯后楼梯有人追、衣柜门自己开了、床底下有东西
> **5. 暗爽瞬间** — 口袋摸到钱、老师请假、暗恋的人看了我一眼
>
> 你想生成哪个类别的内容？

### Step 2: Ask for Story Count

> 你选择了「[category name]」。你想生成几条？

No fixed maximum — the skill can generate any number of original stories.

### Step 3: Ask for AI Model

> 你希望用哪个 AI 模型生成视频提示词？
>
> **A. wan3.0** — 单条 30 秒多镜头 prompt，直接复制使用
> **B. MiniMax H3** — 2×15 秒分段 T2VA prompt，两段分别生成后拼接

### Step 4: Creative Generation (CRITICAL)

**DO NOT simply pick from existing storylines.** The 100 reference storylines are examples of what good content looks like, not a fixed menu. Every generation session must produce **original, creative content** by:

1. **Understand the category's beat structure and emotional core** (see below)
2. **Brainstorm original scenarios** that fit the category's pattern. Think about:
   - What universal childhood experiences have NOT been covered in the examples?
   - What specific, vivid details would make this story feel real and relatable?
   - What unexpected twist or detail would make this story stand out?
3. **Write each prompt from scratch** using the category's beat structure as a scaffold, but filling it with entirely new, specific content
4. **Vary the details aggressively**: different locations, different props, different seasons, different times of day, different family compositions, different emotional tones
5. Load the relevant category reference file ONLY for inspiration and to avoid accidentally duplicating existing ideas

### Creative Thinking Guidelines Per Category

**Category 1 — Fantasy vs Reality:**
- Brainstorm: What everyday household object could a child transform into an epic adventure? Think beyond the obvious — a mop isn't just a mop, it's a wizard's staff. A staircase isn't stairs, it's a mountain. A garden hose isn't a hose, it's a fire-breathing serpent.
- The fantasy should be cinematic and grandiose; the reality should be mundane and slightly embarrassing
- The parent's reaction is always deadpan but loving
- Vary the fantasy genre: medieval, sci-fi, superhero, spy, western, fantasy, sports, etc.

**Category 2 — Growing Up Stories:**
- Brainstorm: What small, specific moment between a child and a family member carries enormous emotional weight? A shared glance. A hand on a shoulder. A note in a lunchbox.
- The conflict is internal, not external — no villains, only misunderstandings and unspoken feelings
- The turning point is always a tiny gesture, not a big speech
- Vary the relationship: father-daughter, mother-son, grandparent, sibling, aunt/uncle

**Category 3 — First Time vs Master:**
- Brainstorm: What everyday skill did you struggle with as a child that you now do without thinking? Tying shoes, whistling, snapping fingers, riding a bike, swimming, cooking an egg.
- Stage 1 MUST end in failure — the more spectacular the failure, the better the callback in Stage 3
- Stage 3 MUST include a callback to the Stage 1 failure — the bush, the egg mess, the tangled laces
- Vary the transition between stages: calendar flip, seasons changing, the child growing taller, the same location aging

**Category 4 — Childhood Fears:**
- Brainstorm: What ordinary household object or situation terrified you as a child? The vacuum cleaner in the dark hallway. The mannequin at the department store. The basement stairs. The portrait on the wall whose eyes seemed to follow you.
- The fear must be self-created by the child's imagination — never show a real monster
- The ending must be ambiguous — was it imagination or real? Never answer this question
- Sound design is half the horror: describe specific sounds (scratching, breathing, footsteps, creaking)

**Category 5 — Sneaky Wins:**
- Brainstorm: What tiny, unearned victory made your entire day as a child? Finding a dollar. Getting away with something. The universe randomly giving you a gift.
- The key technique: external neutral face vs internal explosion of joy
- Use freeze-frame moments where the world stops for the child to process the win
- The "glow" phase is the best part — the child trying to hide the smile and failing

### Step 5: Output

After creative generation:

1. If model is **wan3.0**: create exactly one 30s video prompt per story, then read and follow the [`wan3-drama-prompt-v2` skill](../wan3-drama-prompt-v2/SKILL.md) for its multi-shot and timestamp rules.
2. If model is **MiniMax H3**: create exactly two 15s prompts per story, then read and follow the [`minimax-h3-video-prompt` skill](../minimax-h3-video-prompt/SKILL.md) for H3 T2VA formatting. Segment 2 must continue from Segment 1's ending state without repeating its events.
3. Output all prompts with fixed generation parameters: wan3.0 uses one `duration=30` task; MiniMax H3 uses two separate `duration=15` tasks.
4. Include a summary table of all generated stories.

### Video Generation Tool Calls

Only call a video generation tool when the user explicitly asks to generate or submit the videos. For the Storyboard platform, use `canvas_video_generate`.

#### MiniMax H3 Pre-Submission Gate (MANDATORY)

Immediately before the first MiniMax H3 `canvas_video_generate` call, verify that the user has explicitly provided all three generation parameters below. Treat an earlier selection of "MiniMax H3" in Step 3 as selection of the model family only, not as selection of the exact variant.

1. **Exact model variant**:
   - MiniMax H3 → `model: "minimax-h3"`
   - MiniMax H3 Turbo → `model: "minimax-h3-turbo"`
2. **Aspect ratio**: `16:9`, `9:16`, `1:1`, `4:3`, or `3:4`
3. **Resolution**: `480p`, `720p`, or `1080p`

If any value is missing, ask one consolidated question containing **only the missing items**. Do not repeat questions for values the user has already supplied, and do not infer or silently default a missing value. Do not call the generation tool until all three values are explicitly confirmed.

Suggested question when all three are missing:

> 生成视频前还需要确认 3 个参数：
> 1. 模型：MiniMax H3 或 MiniMax H3 Turbo
> 2. 比例：16:9、9:16、1:1、4:3 或 3:4
> 3. 分辨率：480p、720p 或 1080p
>
> 请告诉我你的选择；确认后我再提交生成。

- **MiniMax H3**: Call `canvas_video_generate` twice per story, once for each segment. Pass Segment 1's prompt to the first call and Segment 2's prompt to the second call. Both calls must use the user's confirmed exact `model`, `ratio`, and `resolution`, and every call must use `duration: 15`. Never submit both prompts in one call and never pass `duration: 30` to a MiniMax H3 call. If the user changes a confirmed parameter before submission, apply the newest value consistently to both segment calls.
- **wan3.0**: Call `canvas_video_generate` once per story with the complete 30s prompt, the selected wan3.0 model ID, and `duration: 30`.
- Before submitting, count the planned calls: H3 must have exactly two calls per story and wan3.0 exactly one. Do not report internal task or model IDs after successful submission.

### Example Consultation Flow

```
User: 帮我生成一些童年回忆视频
AI: [Displays 5 categories with descriptions]
User: 选第1类，幻想VS现实
AI: 你想生成几条？
User: 3条
AI: 你希望用哪个模型？A. wan3.0  B. H3
User: A
AI: [Brainstorms 3 original fantasy-vs-reality scenarios not in the existing library,
     writes 3 complete wan3.0 prompts with unique details]
```

## When Creating New Storylines

**Default behavior: Always create original content.** The existing 100 storylines in the reference files are examples and inspiration, NOT a picklist. Use them only to:
- Understand the category's beat structure and emotional tone
- Avoid accidentally duplicating ideas
- See what level of detail and specificity is expected

| Category | Beat Structure | Creative Direction |
|----------|---------------|-------------------|
| 1. Fantasy vs Reality | 6 beats: entrance → climax → transition → reality → flashback → split-screen + warm ending | Invent new fantasy/reality pairings from everyday objects. Vary the fantasy genre. |
| 2. Growing Up Stories | 4 beats: setup → conflict → turning point → warm resolution | Find specific, tiny moments of family connection. Love through actions, not words. |
| 3. First Time vs Master | 3 stages × ~10s: terrified crash → competent routine → confident master | Choose any skill a child learns. Stage 1 MUST fail. Stage 3 MUST callback. |
| 4. Childhood Fears | 4 beats: setup → fear emerges → escape → safe (ambiguous) | Find the terror in the ordinary. Never show a real monster. Always leave the ending ambiguous. |
| 5. Sneaky Wins | 3 beats: setup → the win (freeze frame) → the glow | Find the tiny, unearned victories. External neutral face vs internal explosion. |

## Resources

The reference files below contain **100+ example storylines** for inspiration and pattern reference. They are NOT a fixed menu — every generation should produce original content. Load them to understand structure, tone, and to avoid duplication.

- `references/category-1-all-20.md` — 20 example fantasy-vs-reality storylines
- `references/category-2-all-20.md` — 20 example growing up / family storylines
- `references/category-3-all-20.md` — 20 example skill progression storylines
- `references/category-4-all-20.md` — 20 example childhood fears storylines
- `references/category-5-all-20.md` — 20 example sneaky wins + 5 combo templates
- `references/5-storylines.md` — Original 5 detailed Category 1 storylines (legacy)

Prompt-formatting guidance is maintained by these sibling skills rather than duplicated locally:

- [`../wan3-drama-prompt-v2/SKILL.md`](../wan3-drama-prompt-v2/SKILL.md) — wan3.0 multi-shot prompt structure and formatting rules
- [`../minimax-h3-video-prompt/SKILL.md`](../minimax-h3-video-prompt/SKILL.md) — MiniMax H3 T2VA prompt structure and formatting rules
