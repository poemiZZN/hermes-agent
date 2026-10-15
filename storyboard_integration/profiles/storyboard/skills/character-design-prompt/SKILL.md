---
name: character-design-prompt
description: "Use when the user wants to design a character reference sheet (人设图) or generate prompts for character design images — whether starting from an existing reference image (图生图) or from a pure text description (纯提示词). Covers structured analysis, design research, redesign proposals, and natural-language prompt generation for GPT-image-2, DALL·E 3, Ideogram, Flux, and similar models."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [character-design, prompt-engineering, image-generation, concept-art, 人设图]
    related_skills: [seedance-prompt]
---

# Character Design Prompt (人物设定图提示词)

## Overview

Design distinctive, memorable character reference sheets (人设图) with a clear aesthetic vision. This skill enforces a structured workflow: analyze → research → redesign → prompt. The core philosophy: **特色 ≠ 好看 (distinctive ≠ pretty)**. A strong character design has visual language that stands apart from generic templates, even if it defies mainstream beauty standards.

Two workflows are provided:
- **Workflow A — 有原图 (With Reference Image)**: Full pipeline starting from an existing character image.
- **Workflow B — 纯提示词 (Pure Text Prompt)**: Design from a text description, no image needed.

Both workflows produce natural-language prompts suitable for GPT-image-2, DALL·E 3, Ideogram, Flux, and similar models. Prompts use complete descriptive sentences, not comma-separated tags.

## When to Use

- User uploads a character image and asks to improve/redesign the character
- User describes a character concept and wants a design prompt
- User asks for 人设图, 人物设定, character reference sheet, or character design prompt
- User wants to add distinctive features to a generic-looking character

Don't use for: scene/environment design, pure outfit design without character context, photorealistic portrait prompts without design intent.

---

## Shared Design Principles (Both Workflows)

### Core Values

1. **Distinctive over pretty**: Design for memorability, not mainstream appeal. A character may be ugly, asymmetrical, or unsettling — as long as it's unforgettable.
2. **Narrative density**: A well-designed character lets the viewer "read" their backstory from appearance alone.
3. **Cross-style fusion**: Blend design elements from different visual traditions. A realistic character can borrow from anime design language; a cartoon character can reference haute couture. Fusion is about design logic, not just style overlay.
4. **Detail rhythm**: High-design characters have dense details, but density needs breathing room. Use 疏密对比 (density contrast) — cluster detail in focal areas, leave other zones cleaner.

### Anti-Patterns

- "Beautiful," "精致," "独特的" — replace with concrete visual descriptions
- Tag-list prompts (comma-separated keywords) — use full descriptive sentences
- Vague colors ("深色," "亮色") — use precise names ("墨绿," "铁锈橙," "暗玫红")
- Piling on every dimension equally — choose 5-7 dimensions to emphasize

---

## Style Gate: 风格确认 (Mandatory — Both Workflows)

**If the user has not explicitly specified a target art style, you MUST ask before proceeding to research or design.** This is a hard gate — do not assume a default.

### Supported Style Categories

Present the user with these options (or a relevant subset):

| 风格类别 | 说明 | 提示词关键词 |
|----------|------|-------------|
| **真人写实** | Photorealistic, 照片级真实感 | photorealistic, hyper-realistic, 真人 |
| **3D国漫** | 3D Chinese donghua style (e.g., 秦时明月, 眷思量, 白蛇) | 3D donghua, Chinese 3D animation style |
| **2D动漫** | 2D anime (日系/韩系) | anime style, 2D animation, cel-shaded |
| **半写实** | Semi-realistic, between anime and photorealism | semi-realistic, stylized realism |
| **概念美术** | Concept art / key visual style | concept art, key visual, splash art |
| **像素艺术** | Pixel art | pixel art, 8-bit/16-bit style |
| **韩系游戏** | Korean game art (e.g., 天命之子, 妮姬) | Korean game art style, semi-realistic anime |
| **厚涂插画** | Painterly / thick-paint illustration | digital painting, impasto,厚涂 |
| **其他** | User specifies custom style | — |

### How to Ask

Use `clarify` with a concise question and the most likely 3-4 options based on context:

```
clarify(question="请确认目标画风", choices=["真人写实", "3D国漫", "2D动漫", "概念美术"])
```

### Workflow-Specific Behavior

- **Workflow A (有原图)**: After A1 analysis, infer the likely style from the image but still confirm with the user. The original image's style is a hint, not a decision.
- **Workflow B (纯提示词)**: If the user's description implies a style (e.g., "游戏角色" → likely 概念美术 or 3D), include that as the first choice in clarify options, but still ask.

**Completion criterion**: User has explicitly stated or selected a target style. Do not proceed to research (A2/B2) until confirmed.

---

## Workflow A: 有原图 (With Reference Image)

Use when the user provides a character image. The full pipeline: analyze the existing design → research references → propose a redesign → generate prompts.

### A1: Character Analysis

When the user provides an image, first use `vision_analyze` to examine it, then structure your analysis.

**Image aspect ratio rule for `canvas_image_generate`**: If a reference image is uploaded and the user has NOT explicitly specified an aspect ratio, default `aspect_ratio` to match the reference image's proportions. Do not override a user-specified ratio.

**1.1 Baseline Assessment**
- Overall style: 写实 / 半写实 / 动漫 / 像素 / 概念美术 / other
- Color system: primary, secondary, accent colors; warm/cool; saturation level
- Line language: hard/soft/bold/delicate
- Existing memory points: any current visual highlights

**1.2 Design Deficiency Audit**

Check each dimension below. Mark dimensions that feel generic or underdesigned:

| Dimension | What to Check |
|-----------|---------------|
| 五官 (Facial features) | Template-like? Any distinctive marks (beauty marks, unique eye shape)? |
| 脸型 (Face shape) | Does it match the character's temperament? |
| 美妆 (Makeup, primarily female) | Eye makeup, lip color — intentional or absent? |
| 发型 (Hairstyle) | Common silhouette? Design intent in the shape? |
| 发色 (Hair color) | Does it integrate with the overall palette? Gradient/texture opportunities? |
| 耳饰 (Ear accessories) | Present? Style match or intentional contrast? |
| 颈饰 (Neck accessories) | Layering and visual weight? |
| 服装上身 (Upper garment) | Silhouette, structure, fabric texture, detail layers |
| 服装下身 (Lower garment) | Balance with upper body, silhouette design |
| 鞋子 (Footwear) | Often neglected — does it complete the design? |
| 腿饰 (Leg accessories) | Stockings, leg rings, greaves — any detail? |
| 其他首饰 (Other jewelry) | Hand accessories, waist chains, etc. |
| 身材 (Body type) | Distinctive physique? |
| 配饰 (Props) | Weapons, bags, tools — do they carry narrative? |

**1.3 Core Problems**

Summarize 2-4 most impactful issues, e.g.:
- "Color system lacks hierarchy — secondary colors don't contrast with primary"
- "Detail density is uneven — upper body overdesigned, lower body bare"
- "Facial features too standardized — no identifying local characteristic"
- "Accessories carry no narrative — can't read the character's background from appearance"

→ **After A1, check Style Gate**: If the user hasn't specified a target style, infer a likely candidate from the image and use `clarify` to confirm before proceeding to A2.

### A2: Reference Research

Use `web_search` to find design references. **Limit: 3 web_search calls max** to avoid context bloat.

**Search strategy:**
- Build style keywords from the character's temperament
- Cross-style: search outside the original image's genre (真人 → search anime/game designs; 动漫 → search fashion photography, concept art)
- Targeted detail searches: specific dimensions identified as weak (e.g., "asymmetric earring design concept art," "fantasy footwear design")

**Reference analysis output:**
Extract 3-5 reference directions, each with:
- Source style/genre
- Specific borrowable elements
- How to fuse with the original character

### A3: Redesign Proposal

Output a complete redesign plan. **Background should remain pure white** — this is a character reference sheet.

**Format:**

```
## 方案名称: [Design intent in 4-8 characters]

【五官】改造建议: ... | 设计意图: ...
【发型 & 发色】改造建议: ... | 设计意图: ...
... (each changed dimension)

整体配色:
- 主色: HEX / description
- 辅色: HEX / description
- 点缀色: HEX / description

风格融合说明: [Which styles were fused and the fusion logic]
```

### A4: Prompt Generation

Generate three prompt variants. See `[ref:prompt-templates]` for format details and examples.

1. **🎯 主版 (Main)**: Most faithful to the redesign — for first generation
2. **🌑 原图修改版 (Image Revision)**: Describes modifications to the original image — for img2img workflows
3. **💫 极简版 (Compact)**: Short version for quick iteration

All prompts must:
- Use complete descriptive sentences, not tag lists
- Describe top-to-bottom: atmosphere → face → hair → garments → accessories → lighting
- Use precise material descriptions (绸缎的光泽, 做旧皮革的粗糙, 金属链的冷感)
- Embed narrative intent into appearance descriptions
- If the user specifies 真人画风, explicitly state "photorealistic" / "真人"

---

## Workflow B: 纯提示词 (Pure Text Prompt)

Use when the user describes a character concept without providing an image. Skip image analysis; go straight to design.

### B1: Requirements Gathering

Extract from the user's description:
- Character identity/role (e.g., 刺客, 魔法学院学生, 赛博朋克佣兵)
- Desired temperament/personality
- Any must-have elements (weapons, specific colors, cultural references)
- Target art style (写实/动漫/概念美术/etc.)
- Gender, rough age range

If critical details are missing, ask the user before proceeding (max 2-3 clarifying questions).

→ **After B1, check Style Gate**: If the user hasn't specified a target style, use `clarify` to ask. If the description implies a style (e.g., "游戏角色" → likely 概念美术), include it as the first option but still confirm. Do not proceed to B2 until the style is confirmed.

### B2: Reference Research

Same as Workflow A2 — use `web_search` (max 3 calls) to find design references for the character type, target style, and key design elements.

### B3: Original Design Proposal

Since there's no existing image to critique, build a complete design from scratch:

```
## 方案名称: [Design intent]

## 整体风格定位
Style, color temperature, line language, visual references

【五官 & 脸型】设计: ... | 设计意图: ...
【发型 & 发色】设计: ... | 设计意图: ...
【服装上身】设计: ... | 设计意图: ...
【服装下身】设计: ... | 设计意图: ...
【配饰 & 道具】设计: ... | 设计意图: ...
... (cover at least 5 dimensions)

整体配色:
- 主色: HEX / description
- 辅色: HEX / description
- 点缀色: HEX / description

风格参考: [Named style references — specific games, artists, or design movements]
```

### B4: Prompt Generation

Same three-variant output as Workflow A4. The 原图修改版 variant is not applicable here, so replace it with:

**🎨 风格变体版 (Style Variant)**: Same design but rendered in a different art style (e.g., if main is 写实, variant could be 动漫概念美术).

See `[ref:prompt-templates]` for full format and examples.

---

## Output Checklist (Both Workflows)

Before delivering final output, verify:

- [ ] Analysis/design addresses specific issues, not vague generalities
- [ ] References span at least two distinct style types
- [ ] Redesign/proposal covers at least 5 dimensions
- [ ] Prompts can reproduce the design's core identity
- [ ] Overall design has a unified aesthetic logic, not patchwork
- [ ] Background is specified as pure white (人设图 convention)
- [ ] Prompts use descriptive sentences, not comma tags
- [ ] Colors are precise, materials are sensory, no hollow adjectives

---

## Image Generation Handoff: 图片生成确认 (Both Workflows)

**After all prompts are delivered, always pause and ask the user whether to proceed with image generation.** Do NOT automatically generate images — the user must confirm first.

### Handoff Rule

1. Deliver the design proposal + three prompt variants in full.
2. End your response with a `clarify` asking:
   ```
   clarify(question="是否使用以上提示词生成图片？", choices=["用主版提示词生成", "用原图修改版/风格变体版生成", "用极简版生成", "暂不生成，先看看"])
   ```
   Adapt the choices to match the actual variants delivered (Workflow A vs B).
3. If the user selects a variant → proceed with `canvas_image_generate` using that prompt.
4. If the user chooses "暂不生成" → stop, task complete.

### Generation Tips

- When calling `canvas_image_generate`, include the reference image if using the 原图修改版 variant (Workflow A).
- Respect the aspect ratio rule from A1: if a reference image exists and user hasn't overridden, use its proportions.
- After generation, present the result image to the user for feedback.

---

## Common Pitfalls

1. **Beautifying instead of distinguishing.** The goal is memorability, not conventional attractiveness. A scar, asymmetry, or unusual proportion can be the strongest design choice.

2. **Skipping research.** Even if you "know" the design space, 2-3 web searches surface specific reference points that ground the proposal in concrete visual language.

3. **Prompting in tags.** "white hair, red eyes, black coat" is weak. "Silver-white hair swept asymmetrically across one eye, the exposed eye a deep crimson with a faint glow" is strong.

4. **Ignoring the lower half.** Shoes, legwear, and lower garment details are the most commonly neglected dimensions — and the highest-impact fix for generic designs.

5. **Equal detail everywhere.** A character covered in equal-density detail reads as noise. Create focal points with concentrated detail and let other areas breathe.

6. **Forgetting the white background.** Character reference sheets need clean backgrounds. Always specify "纯白背景" / "plain white background."

---

## Verification

After completing either workflow:
1. Re-read the prompts and check: can someone who has never seen this conversation generate the intended character?
2. Verify each prompt specifies a plain white background.
3. Confirm at least one cross-style reference was incorporated into the design logic.
