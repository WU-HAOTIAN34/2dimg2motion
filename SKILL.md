---
name: img2motion
description: Use when a user provides one baseline image and requests game animation frames, sprite sequences, attack/walk/idle/hit/death/casting motion, transparent PNG frames, a spritesheet, or consistent whole-character pose animation.
---

# img2motion

## Overview

Turn one baseline character, creature, vehicle, weapon, or prop image into a consistent transparent game-animation sequence through whole-character key-pose redraw and reference-guided in-betweens.

**Core principle:** establish an identity lock, approve shared key poses, then generate all in-betweens from the baseline and key-pose sheet. Never generate every frame independently.

Read [references/keypose-redraw.md](references/keypose-redraw.md) before generating animation assets.

## Input contract

Collect or infer:

- baseline image and facing direction;
- motion type, ordered beats, and loop behavior;
- frame count or timing preference;
- canvas size, stable foot baseline, and naming prefix;
- required deliverables: frames, spritesheet, contact sheet, and playback preview.

Ask only for information that materially changes the result. Default to 8 transparent RGBA frames and a seamless return to the source pose.

## Workflow

### 1. Inspect and establish the identity lock

Inspect the source at original resolution. Record every invariant that must survive redraw:

- face, expression, silhouette, proportions, and facing direction;
- palette, outline weight, shading style, and material treatment;
- limb count, hand order, clothing, armor, markings, and accessories;
- weapon shape, grip, length, emblem, and distinctive small details.

Record uncertain or occluded regions explicitly. Keep the source visible during every generation and correction pass.

### 2. Design motion beats and key poses

Choose readable beats before generating art:

- idle: settle -> rise -> settle;
- walk: contact -> down -> passing -> up -> opposite contact;
- attack: guard -> anticipation -> acceleration -> contact -> contact hold -> recovery;
- hit: contact -> recoil -> settle;
- death: imbalance -> collapse -> impact -> rest.

Select 3-5 key poses that define the motion. For attacks, use guard, anticipation, contact, and recovery. Make contact the clearest silhouette and preserve a contact hold when impact needs emphasis.

### 3. Generate one coherent key-pose sheet

**REQUIRED SUB-SKILL:** Use `imagegen` for whole-character key-pose redraw.

Generate all key poses together on one evenly divided sheet. Redraw the complete character in every cell. Permit natural squash, perspective, foreshortening, overlap, and newly visible surfaces while preserving the identity lock.

Use a perfectly flat chroma-key background with generous gutters and no labels, borders, shadows, effects, debris, or fused cells. Prefer `#ff00ff` when the subject contains green or blue.

Reject the sheet if any pose changes identity, loses details, duplicates limbs, reverses hand order, crops the subject, or breaks the stable foot baseline.

### 4. Generate reference-guided in-betweens

**REQUIRED SUB-SKILL:** Use `imagegen` with both the original baseline and approved key-pose sheet as references.

Generate in-betweens together in chronological order. Specify the exact beat assigned to each cell, identical cell geometry, stable character scale, coherent limb trajectories, and the intended contact hold.

Never generate every frame independently. Never accept an in-between pass whose style or identity differs from the approved key poses.

### 5. Remove the background and normalize frames

Remove the flat chroma-key background locally and check soft edge alpha plus magenta residue. Split cells in reading order.

Place each frame on one RGBA canvas using one common scale and alignment transform. Do not independently auto-fit frames. Maintain the stable foot baseline and direction. Use the exact source as the first and last frame when it improves loop continuity.

Name frames contiguously, such as `hero-attack_00.png` through `hero-attack_07.png`.

### 6. Correct temporal and identity drift

Compare adjacent frames and correct only the failing region or pose. Regenerate affected in-betweens after a key pose changes.

Check face, emblem, palette, outline, accessories, limb count, markings, weapon dimensions, scale, center, baseline, trajectories, and silhouette continuity.

### 7. Validate outputs

Run deterministic validation:

```powershell
python scripts/validate_outputs.py --frames-dir output/frames --width 471 --height 478 --prefix hero-attack
```

Inspect a contact sheet and playback loop. Confirm:

- contiguous names, RGBA mode, one canvas size, and transparent corners;
- no chroma fringe or magenta residue;
- no identity drift, missing details, extra limbs, or scale popping;
- stable foot baseline and center;
- readable anticipation, acceleration, contact, contact hold, and recovery;
- smooth loop endpoints when looping is requested.

Correct failures and repeat both visual and deterministic validation. Report exact output paths and evidence.

## Output contract

```text
output/
|-- keyposes.png           # approved whole-character key poses
|-- frames/                # contiguous transparent RGBA sequence
|-- spritesheet.png        # packed sequence
|-- contact-sheet.png      # visual consistency review
|-- preview.gif            # playback loop
`-- manifest.json          # source, canvas, baseline, beats, frame order
```

## Quick reference

| Stage | Gate |
|---|---|
| Identity | Immutable features are recorded from the baseline |
| Key poses | All defining poses share one coherent sheet |
| In-betweens | Baseline and approved key poses constrain every frame |
| Normalize | One scale, canvas, direction, and stable foot baseline |
| Correct | Adjacent frames preserve identity and trajectory continuity |
| Deliver | Deterministic checks, contact sheet, and playback loop pass |

## Example

User: "Use this golem image to make an eight-frame heavy ground-smash attack."

Record its identity lock, generate guard/anticipation/contact/recovery together, approve the key poses, generate ordered in-betweens from both references, remove chroma, normalize all frames to one baseline, preserve the exact source at loop endpoints, inspect contact and playback, validate outputs, and deliver the transparent sequence.

## Common mistakes

- Generating each frame separately: identity and timing drift. Use one shared key-pose sheet and reference-guided in-betweens.
- Auto-fitting every pose: scale pops between frames. Apply one common transform.
- Accepting a pretty key pose with changed details: visual quality does not excuse identity drift.
- Adding effects during character generation: detached dust and motion lines complicate extraction. Add effects later as separate assets.
- Checking only individual PNGs: a frame can look good alone and fail in motion. Inspect the contact sheet and playback loop.
- Trusting the generated background: remove chroma locally and measure magenta residue.
