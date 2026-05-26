---
name: trading-video-script
description: "Generate a 10-15 minute video script for trading strategies by analyzing strategy description, Pine Script code, and settings. Use when creating YouTube walkthroughs, educational explainers, or product demos for algorithmic strategies."
argument-hint: "Provide paths to description file, Pine Script file, and settings file plus audience/style constraints."
---

# Trading Strategy Video Script

## What This Skill Produces

This skill creates a structured, narration-ready script for a 10-15 minute strategy video.

The script is designed to:

- Open by teaching one core market behavior behind the strategy without naming the strategy at all
- Explain how that behavior forms in price action before talking about any indicator or branded setup
- Show the practical trading opportunity inside that behavior pattern
- Blend the strategy in only after the viewer understands the market idea it is built to exploit
- Explain logic, settings, and practical interpretation clearly
- Stay aligned with the actual Pine Script and configuration

The opening should feel like a trading lesson first, not a product introduction.

For example:

- If the strategy is trend-based, start by explaining how a trend forms through higher highs and higher lows
- Then explain a practical way traders may act on that behavior, such as using a break above the previous higher high as a continuation trigger
- Only after that foundation should the script introduce the strategy as a structured way to capture that idea

## When To Use

Use this skill when you need to:

- Turn a strategy specification into a full spoken script
- Explain strategy mechanics for traders with mixed experience levels
- Produce consistent strategy videos with the same intro pattern

## Required Inputs

- Strategy description file (concept, intent, rules)
- Pine Script source file (actual implementation)
- Strategy settings source (JSON, UI defaults, or documented parameters)

Optional inputs:

- Audience level (`beginner`, `intermediate`, `advanced`)
- Narration tone (`educational`, `confident`, `analytical`, `story-driven`)
- Platform and time preference (YouTube long-form, tutorial chaptering)

## Workflow

1. Read and summarize the strategy intent from the description.
2. Parse Pine Script to extract:

- Entry logic
- Exit logic
- Filters and confirmations
- Risk controls (stops, targets, sizing)
- Time/session constraints

3. Parse settings and map every user-facing parameter to behavior.
4. Build a concept-first intro:

- Start with one core market behavior the strategy is built around
- Explain how that behavior forms in raw price action before mentioning the strategy
- Explain how traders can act on that behavior in practical terms
- Do not mention the strategy name in the first intro beat
- Transition by introducing the strategy as a structured way to trade that market behavior

5. Create a chaptered script outline for 10-15 minutes.
6. Draft the full script with timestamps, narration, and optional on-screen cues.
7. Run quality checks and revise for clarity, pacing, and technical accuracy.

## Decision Rules

- If code and description disagree, prefer Pine Script as source of truth and explicitly note the mismatch.
- If settings are incomplete, keep assumptions minimal and label them clearly.
- If the strategy belongs to a familiar class (trend, breakout, mean reversion, range, momentum), teach the class behavior first before introducing the strategy itself.
- If logic is complex, explain in three layers:
- Intuition (why)
- Rule (what)
- Trigger condition (when)
- If the opening starts sounding like a direct strategy pitch, rewrite it so it begins as a trading concept lesson instead.
- If there is no explicit risk management in code, include a clear caution section.
- If the strategy is repaint-prone or confirmation-dependent, include a dedicated disclaimer section.

## Script Structure (Target 10-15 Minutes)

Use this sequence and adjust depth by complexity.

1. Generic Market Context Hook (0:00-1:15)

- Explain the market behavior/problem this type of strategy is built around.
- Teach how that behavior forms and what traders typically look for in it.
- Keep it generic and concept-first.

2. Strategy Introduction As Solution (1:15-2:00)

- Introduce the strategy name only after the market behavior is clearly established.
- Position it as a helper for the previously framed market behavior and trade idea.

3. Core Logic Breakdown (2:00-6:30)

- Inputs/signals
- Entry conditions
- Exit/invalidations
- Filters and edge cases

4. Settings Deep Dive (6:30-10:00)

- Explain each high-impact setting and trade-off.
- Include practical guidance on sensitivity and false signals.

5. Example Walkthrough (10:00-13:00)

- Show one clean setup and one problematic setup.
- Explain decision points and what the script would have done.

6. Risk, Limitations, and Best Use Cases (13:00-14:30)

- Where strategy performs well/poorly
- Risk controls and execution caveats

7. Closing Summary and Next Step (14:30-15:00)

- Recap who this is for
- Suggest what to test next

## Output Requirements

- Duration target: 10-15 minutes
- Approximate word target: 1300-2000 words
- Tone: clear, precise, non-hype
- Must not invent settings or Pine variables not present in input files
- Include concise chapter headings and timestamps
- Include optional on-screen cue notes in brackets

## Quality Checklist

- Intro is concept-first and generic before naming strategy
- Intro explains the underlying market behavior in a way that makes sense even without the strategy
- Intro includes a practical trading interpretation before the strategy is introduced
- Strategy is introduced as solution/helper
- All major rules match Pine Script behavior
- All key settings are explained with effect/trade-off
- Includes both strengths and failure modes
- Includes risk disclaimer and non-financial-advice wording
- Script can be read aloud naturally in 10-15 minutes

## Prompt Pattern

Use prompts like:

- "Create a 10-15 minute script using this description: <path>, Pine Script: <path>, settings: <path>. Audience is intermediate traders."
- "Generate a chaptered YouTube script. Start by teaching the market behavior first, then introduce the strategy as the way to trade it."
- "Open by explaining the trading concept without naming the strategy, then blend the strategy into that explanation once the setup is clear."
