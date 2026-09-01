# Prompt Templates (提示词模板)

## Writing Principles

- **Use sentences, not tags.** Describe like briefing an illustrator verbally, not dumping keywords.
- **Narrative flow**: atmosphere/style first → top-to-bottom appearance → lighting/mood last.
- **Materials are sensory**: 绸缎的光泽 (satin sheen), 做旧皮革的粗糙 (worn leather roughness), 金属链的冷感 (cold feel of metal chains).
- **Colors are precise**: "墨绿" not "深绿", "铁锈橙" not "橙色", "暗玫红" not "红色".
- **Named style references are welcome**: "in the style of concept art for [game/artist]" is valid.
- **Length**: Main prompt ≤ 3000 chars for GPT-image-2 / Flux compatibility.
- **Language**: English preferred (models understand it more precisely); add Chinese annotations for intent where helpful.
- **If user specifies 真人画风**: explicitly state "photorealistic" / "photo-realistic" in the prompt.
- **Background**: Always "plain white background" / "纯白背景".

---

## Workflow A Templates (有原图)

### 🎯 主版提示词 (Main — most faithful to redesign)

Structure as a flowing paragraph or sectioned description:

```
A full-body character reference sheet illustration of [identity + temperament], standing against a plain white background.

FACE & MAKEUP: [Specific facial features, distinguishing marks, makeup details. Avoid "beautiful" — describe shapes, colors, asymmetries.]

HAIR: [Style, color, texture, silhouette. Include gradients or special treatments if applicable.]

HEADPIECE: [If any — describe as an asymmetric statement piece where relevant.]

EARRINGS: [Style, material, length, any mismatch or asymmetry.]

NECKWEAR: [Layering, materials, visual weight.]

UPPER GARMENT: [Silhouette, structure, fabric texture, layering, colors. Use sensory material language.]

LOWER GARMENT: [Balance with upper body, silhouette, texture.]

FOOTWEAR: [Style, material, details — don't neglect.]

ACCESSORIES: [Hand accessories, waist items, props. Each with material and narrative significance.]

COLOR PALETTE: [Primary, secondary, accent — with precise color names.]

ART STYLE: [Specific style reference — concept art, anime, semi-realistic, etc. — with named influences if helpful.]

LIGHTING: [Soft studio lighting, or specific mood lighting — but keep background clean white.]

The overall design should convey a sense of [emotional/narrative tone].
```

### 🌑 原图修改版 (Image Revision — for img2img)

Describe modifications to the original image:

```
A full-body character illustration of [identity + temperament], a revised version of the original character design, standing against a plain white background.

Modifications from original:
- Hair: [Specific change — restyle, recolor, add gradient, etc.]
- Face: [Specific change — add beauty mark, reshape jawline, add makeup, etc.]
- Upper garment: [Specific change — new silhouette, added layering, new fabric, etc.]
- Lower garment: [Specific change]
- Footwear: [Specific change]
- Accessories: [Specific additions/modifications with materials]

Preserved from original: [What stays — pose, general body type, core color direction, etc.]

Style: [Target style], rendered with [quality descriptor — e.g., "clean linework and flat color" or "semi-realistic rendering with soft shading"].
Lighting: [Studio lighting description].
The overall color palette centers on [color scheme].
```

### 💫 极简版 (Compact — for quick iteration)

```
Full-body character reference sheet, [identity], plain white background. [Hair description]. [Key face detail]. [Upper garment in one phrase]. [Lower garment in one phrase]. [Footwear]. [1-2 key accessories]. [Color palette in one phrase]. [Art style]. [Lighting].
```

---

## Workflow B Templates (纯提示词)

### 🎯 主版提示词 (Main)

Same structure as Workflow A 主版. The character is designed from scratch, so describe with full conviction — no "modified from" language.

### 🎨 风格变体版 (Style Variant)

Same character design, different art style:

```
A full-body character reference sheet illustration of [same identity + temperament], standing against a plain white background. [Same appearance description as main prompt, condensed].

The art style is [new style — e.g., "anime concept art with cel-shading and bold outlines" or "semi-realistic digital painting with textured brushwork"], whereas the main version was rendered in [original style].

Color palette and design elements remain consistent; only the rendering style changes.
```

### 💫 极简版 (Compact)

Same format as Workflow A 极简版.

---

## Quality Examples

### Good (descriptive sentences):

> Silver-white hair swept into an asymmetrical high ponytail, the ends fading to a pale lavender. Her left eye is covered by a swept fringe, while the visible right eye is deep crimson with a faint golden ring around the pupil.

### Bad (tag list):

> white hair, ponytail, red eyes, heterochromia

### Good (precise color + material):

> A structured jacket in oxblood leather with matte black hardware, worn over a raw silk wrap top in charcoal grey.

### Bad (vague):

> dark red jacket with black details, grey top

### Good (narrative accessory):

> A tarnished silver locket hangs from a thin chain at her collarbone, its surface etched with a barely visible constellation pattern — the only remnant of her former life.

### Bad (generic):

> a necklace
