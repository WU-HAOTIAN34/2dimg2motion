---
name: img2mo-learn
description: Learn reusable 2D motion-generation knowledge from user-specified action resources with `/img2mo-learn <resource>`. Use when the user provides videos, extracted frame sequences, spritesheets, Spine assets, generated outputs, failed attempts, or reference motion folders and wants to summarize animation timing, pose beats, style traits, prompt patterns, extraction/cropping rules, or failure lessons into the project `img2mo-knowledge/` folder for later `/img2motion` generation.
---

# Img2mo-learn

## Overview

Use this skill when the user invokes:

```text
/img2mo-learn <resource-path-or-folder>
img2mo-learn <resource-path-or-folder>
```

The goal is to turn finished or reference motion assets into reusable project knowledge. Store learned knowledge in the project-level `img2mo-knowledge/` folder, never in the installed Codex skill directory during normal work.

## Input Resolution

Resolve the argument after `img2mo-learn` as follows:

1. If it is an existing relative or absolute path, use it directly.
2. If it is a bare name, first try `sample\<name>`, then `output\<name>`, then `motion\<name>`.
3. If it is a folder, inspect likely assets in this order: `manifest.json`, `preview.gif`, `contact-sheet.*`, `spritesheet.*`, `fullframe/`, `frames/`, Spine `.json/.atlas/.skel`, then videos.
4. If no matching resource exists, report the missing path and ask for the correct path.

Supported resources:

- video files such as `.mp4`, `.mov`, `.webm`;
- PNG frame folders, spritesheets, contact sheets, or GIF previews;
- project outputs from this skill such as `output/<action-id>/`;
- Spine-style assets such as `.json`, `.atlas`, `.skel`, texture folders;
- local reference-library folders under `motion/`.

## Knowledge Location

Create this structure if missing:

```text
img2mo-knowledge/
|-- index.md
|-- learnings.jsonl
|-- action-patterns.md
|-- style-patterns.md
|-- prompt-patterns.md
`-- failures.md
```

Append one JSON object per learning session to `img2mo-knowledge/learnings.jsonl`. Keep Markdown files concise and curated; do not paste huge logs, full prompts, or complete frame listings.

## Learning Workflow

1. **Identify the resource type.**
   - For video: read frame size, fps, duration, and frame count with `ffprobe` when available.
   - For frame sequences: count frames, inspect canvas sizes, alpha/background, and contact sheet if present.
   - For spritesheets: infer grid/cell count when possible; otherwise describe visible beats.
   - For Spine assets: inspect animation names, bone/slot names, skins, attachments, timeline names, and texture organization without assuming rendered motion if frames are not available.

2. **Create review surfaces if useful.**
   - For video or frame folders, create temporary or output-side contact sheets and preview GIFs if they do not exist.
   - Do not alter the source resource.
   - Do not store bulky extracted frames in `img2mo-knowledge/`; store outputs under `output/` or `tmp/` and reference their paths in JSON.

3. **Summarize motion timing.**
   - Identify action type: attack, walk, idle, block, suffer, death, born, skill/cast, or other.
   - Record frame count, fps, loop behavior, and major beats.
   - For attacks, prefer beat labels such as `guard`, `anticipation`, `acceleration`, `contact`, `contact hold`, `follow-through`, `recovery`.
   - Record which frame ranges are most useful as key poses.

4. **Summarize pose and topology lessons.**
   - Record active limb/feature, weapon or prop owner, anchor limb/surface, facing direction, and stable baseline behavior.
   - Note silhouette expansion, squash/stretch, center drift, foot/bottom baseline, and whether motion needs extra canvas margin.

5. **Summarize style lessons.**
   - Record line weight, palette, shading, material treatment, outline softness, shape language, effects style, and background/keying considerations.
   - Distinguish character style from detached effects.

6. **Summarize prompt lessons.**
   - Write reusable prompt clauses that could improve later generation.
   - Keep prompt clauses short and parameterized; avoid overfitting to one character name unless the lesson is character-specific.

7. **Summarize failures and constraints.**
   - Record what should be rejected: hand swaps, scale popping, bad alpha, cut weapons, over-crowded sheets, text/watermark contamination, or mismatched style.

8. **Write project knowledge.**
   - Append structured session data to `learnings.jsonl`.
   - Update the relevant Markdown files with durable, reusable lessons.
   - If the learning is only useful for one output, also write `output/<action-id>/retro.md`.

## JSONL Schema

Each line in `img2mo-knowledge/learnings.jsonl` should be a compact JSON object:

```json
{
  "id": "learn-YYYYMMDD-HHMMSS-short-name",
  "date": "YYYY-MM-DD",
  "source": "relative/or/absolute/path",
  "resource_type": "video|frame_sequence|spritesheet|spine|output|reference_folder",
  "action_type": "attack|walk|idle|block|suffer|death|born|skill|unknown",
  "fps": 24,
  "frame_count": 14,
  "loop": true,
  "beats": [
    {"name": "anticipation", "frames": "02-04", "notes": "body compresses before strike"}
  ],
  "key_pose_guidance": ["frame 05 should be the clearest contact silhouette"],
  "topology": {
    "active": "screen-left sword hand",
    "anchor": "screen-right hand",
    "weapon_owner": "screen-left hand"
  },
  "style": ["thick dark outline", "warm orange shadow shapes"],
  "prompt_clauses": ["same foot/bottom baseline in every cell"],
  "failure_lessons": ["reject sheets where the weapon hand swaps"],
  "artifacts": ["output/.../contact-sheet.jpg"]
}
```

Use `null` for unknown scalar fields and `[]` for empty lists. Keep one line per session.

## Markdown Update Rules

- `index.md`: list recent learning sessions and high-level tags.
- `action-patterns.md`: update durable motion timing rules by action type.
- `style-patterns.md`: update durable visual style observations.
- `prompt-patterns.md`: update short reusable prompt clauses and anti-clauses.
- `failures.md`: update rejection checks and known failure modes.

When adding Markdown entries, include the source path and date. Keep entries short enough that `/img2motion` can read them quickly.

## Use During Generation

Later `/img2motion` work must read `img2mo-knowledge/index.md` first when it exists. Then read only the relevant knowledge files for the requested action/style:

- action timing: `action-patterns.md`;
- visual style: `style-patterns.md`;
- prompt wording: `prompt-patterns.md`;
- known pitfalls: `failures.md`;
- detailed recent examples: search `learnings.jsonl` for matching `action_type`, source tags, or character style.

Do not let learned knowledge override the current user's explicit request or the current baseline image identity. Treat project knowledge as guidance, not ground truth.
