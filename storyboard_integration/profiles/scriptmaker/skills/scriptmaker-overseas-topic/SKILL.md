---
name: scriptmaker-overseas-topic
description: "Use when the user is choosing what to write (选材, 做什么题材, 哪类故事好做, 想做一部…, 在几个方向之间犹豫, 最近什么火). Confirm whether the project targets overseas (海外) or domestic (国内) audiences; for overseas topics read the latest 数据榜 daily, weekly and monthly reports with read_market_reports and ground the advice in them."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [scriptmaker, 选材, 海外短剧, 数据榜, 市场报告, 题材, 语种市场, 爆款套路]
    related_skills: [scriptmaker-script-generation, scriptmaker-baokuan-outline]
---

# 海外选材：结合数据榜报告回答

数据榜每天、每周、每月从 TikTok、ReelShort、ShortMax、DramaBox、GoodShort、NetShort、DramaWave、FreeReels、iDrama、VibeShort、Vigloo 采集增量榜，并生成日报、周报、月报。这些数据**只覆盖海外平台**。

## 什么时候用

用户在决定写什么，而不是在执行已经定好的项目：

- 问"现在做什么题材好""哪类故事好卖""最近什么火"；
- 给出一个或几个方向，想听比较或建议；
- 题材还模糊，只说了受众或类型（如"想做个女频""想做复仇"）。

不要用在：查询或控制已有任务、读写附件、剧本医生、导出，或者用户已经把题材定死、只要求执行。

## 第一步：确认是不是海外题材

用户没说清楚面向哪里时，先调用 `ask_choice` 确认，不要猜：

```text
ask_choice(questions=[
  {"question": "这部剧主要面向哪里的观众？", "options": ["海外（出海短剧）", "国内"]}
])
```

- 还有其他待确认的关键信息（如受众、集数）时，放进同一张卡，一张卡最多 3 个问题。
- 调用 `ask_choice` 后本轮立即结束，等用户回答。
- 用户已经说了"出海""海外""英语市场""TikTok""ReelShort"等，就视为海外题材，直接进入第二步。
- 用户选国内题材：不要读取报告，这些数据不代表国内市场。照常讨论，需要外部信息时可以用 web_search。

## 第二步：读取报告

确认是海外题材后调用：

```text
read_market_reports()
```

默认返回日报、周报、月报各自最近一期的摘要。每份报告都包含：
- 题材占比与环比（topics）、语种占比与变化来源（languages）；
- 爆款套路（tropes）、新爆款作品（new_hits）；
- 集数结构、受众、免费集数、TikTok 标签；
- 有 AI 解读时，还有要点（key_points）和选材建议（recommendations）。

同一次对话读过一次就复用，不要每轮重读。只关心某个周期时可以只读它，例如 `read_market_reports(periods=["month"])`。

## 第三步：结合报告回答

先给结论，再给依据，最后给可执行的建议：

1. **结论**：一两句话说明值得做的方向，或用户提出的几个方向哪个更有数据支撑。
2. **依据**：引用报告里的数字，并注明出处，例如"据 2026 年第 40 周周报，逆袭复仇占 18.9%（▲0.5 个百分点）"。
   - 数字原样使用，不要换算或重新四舍五入。
   - 月报看中长期结构；周报看趋势和新爆款；日报只看当日异动，不单凭日报下结论。
3. **建议**：给出目标平台与语种、可借鉴的套路、集数规划和付费卡点（参考各平台免费集数）。

注意：

- 头部作品只是代表作品（多为每榜前 5 名的预览数据），不能写成"前 N 名占比"。
- 环比变化标注了主要来自哪个平台（driver）时，说成"某平台上新调整"，不说成市场趋势。
- 各平台播放量口径不同，不比较跨平台的绝对播放量。
- 报告缺失（返回 missing，或 reports 为空）时，如实说明没有数据支撑，再基于常识给出谨慎建议。
- 报告只是参考。用户选定之前，不要把报告里的题材、套路写进 `prepare_script_generation` 的 locked_facts 或 style_directions；只借鉴题材层面的写法，不照搬具体作品的人物和情节。
- 用户选定方向并明确要求启动专业剧本团队时，再按 scriptmaker-script-generation 的流程收集字段。
