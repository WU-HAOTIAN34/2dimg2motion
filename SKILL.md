---
name: 2dimg2motion
description: Use when a user provides one baseline image and requests game animation frames, sprite sequences, attack/walk/idle/hit/death/casting motion, transparent PNG frames, a spritesheet, or consistent whole-character pose animation.
---

# 2dimg2motion

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

Ask only for information that materially changes the result. Default to 14 transparent RGBA frames per action and a seamless return to the source pose.

## Limb-side and topology lock

Establish limb identity before designing poses:

- Do not infer anatomical left/right from an unqualified word such as "left" or "right" when the source faces front, back, or is mirrored. Ask whether it means screen space or character anatomy unless prior context makes the mapping explicit.
- Normalize every side to `screen-left` or `screen-right`. If anatomy matters, record both forms, such as `character-left (screen-right)`.
- Record the `active limb`, its `active shoulder`, the opposite `anchor limb`, and distinctive markings or spikes that identify both limbs.
- Keep the active limb connected to the same shoulder through every key pose and in-between, including when it crosses the body centerline.
- Keep the anchor limb visible and attached to its original shoulder as a continuity reference. Do not let it lift, disappear, or become the attacking limb.
- Use the normalized side names in image-generation prompts and contact-sheet review. Before generation, state the lock explicitly, for example `active=screen-left; anchor=screen-right`.
- Persist `coordinateSpace`, `activeLimb`, `activeShoulder`, and `anchorLimb` in `manifest.json`. Never alternate between anatomical and screen-space naming inside one animation.

## Default 14-frame plan

Use six immutable anchors in this order: `00 -> 02 -> 05 -> 08 -> 11 -> 13`.

| Index | Role | Rule |
|---|---|---|
| 00 | baseline start | Place the exact source on the final canvas; do not redraw or rescale it. |
| 01 | in-between | Interpolate 00 -> 02. |
| 02 | key frame 1 | First generated defining pose. |
| 03-04 | in-betweens | Interpolate 02 -> 05 in chronological order. |
| 05 | key frame 2 | Second generated defining pose. |
| 06-07 | in-betweens | Interpolate 05 -> 08 in chronological order. |
| 08 | key frame 3 | Third generated defining pose. |
| 09-10 | in-betweens | Interpolate 08 -> 11 in chronological order. |
| 11 | key frame 4 | Fourth generated defining pose. |
| 12 | in-between | Interpolate 11 -> 13. |
| 13 | baseline end | Copy frame 00 exactly. |

Generate exactly four key frames at indices 02, 05, 08, and 11. Save exact copies of those images in both `keyframe/` and their matching `fullframe/` positions. Never redraw a key frame during interpolation. Use one inserted frame around each baseline endpoint and two inserted frames between each pair of generated key frames.

Persist `frameCount: 14`, `keyframeIndices: [2, 5, 8, 11]`, `anchorIndices: [0, 2, 5, 8, 11, 13]`, and `segmentInsertions: [1, 2, 2, 2, 1]` in `manifest.json`.
Persist `previewBackground: "#FFFFFF"` in `manifest.json`.

## Workflow

### 1. Inspect and establish the identity lock

Inspect the source at original resolution. Record every invariant that must survive redraw:

- face, expression, silhouette, proportions, and facing direction;
- palette, outline weight, shading style, and material treatment;
- limb count, hand order, clothing, armor, markings, and accessories;
- shoulder-to-limb topology, active-side mapping, anchor limb, and side-specific markings;
- weapon shape, grip, length, emblem, and distinctive small details.

Record uncertain or occluded regions explicitly. Keep the source visible during every generation and correction pass.

### 2. Design motion beats and key poses

Choose readable beats before generating art:

- idle: settle -> rise -> settle;
- walk: contact -> down -> passing -> up -> opposite contact;
- attack: guard -> anticipation -> acceleration -> contact -> contact hold -> recovery;
- hit: contact -> recoil -> settle;
- death: imbalance -> collapse -> impact -> rest.

Select exactly four generated key poses for indices 02, 05, 08, and 11. For attacks, use anticipation, acceleration/contact, contact hold/follow-through, and recovery; frames 00 and 13 supply the neutral guard. Make contact the clearest silhouette.

For one-limb actions, describe both limbs in every beat: state how the active limb remains attached to its locked shoulder and how the anchor limb stays fixed. Track the shoulder-to-hand trajectory, not only the hand position.

### 3. Generate one coherent key-pose sheet

**REQUIRED SUB-SKILL:** Use `imagegen` for whole-character key-pose redraw.

Generate all key poses together on one evenly divided sheet. Redraw the complete character in every cell. Permit natural squash, perspective, foreshortening, overlap, and newly visible surfaces while preserving the identity lock.

After approval, split the sheet into four transparent files named with their final indices: `_02`, `_05`, `_08`, and `_11`. These files become immutable anchors for interpolation.

Use a perfectly flat chroma-key background with generous gutters and no labels, borders, shadows, effects, debris, or fused cells. Prefer `#ff00ff` when the subject contains green or blue.

Reject the sheet if any pose changes identity, loses details, duplicates limbs, reverses hand order, crops the subject, breaks the stable foot baseline, obscures the active shoulder attachment, or moves/hides the anchor limb. A limb crossing the torso must still be traceable to its locked shoulder.

### 4. Generate reference-guided in-betweens

**REQUIRED SUB-SKILL:** Use `imagegen` with both the original baseline and approved key-pose sheet as references.

Generate in-betweens together in chronological order. Specify the exact beat assigned to each cell, identical cell geometry, stable character scale, coherent limb trajectories, and the intended contact hold.

Generate the five anchor-to-anchor segments with fixed insertion counts: 00->02 gets one frame; 02->05, 05->08, and 08->11 get two frames each; 11->13 gets one frame. Use the two adjacent anchors plus the baseline and full key-pose set as references. Do not include generated substitutes for any anchor index.

Repeat the side lock verbatim in the in-between prompt: name the active limb in screen space, require connection to the same shoulder in every cell, and state that the anchor limb must remain visible and stationary. Treat a switched or ambiguous shoulder attachment as a failed generation, even if each frame looks plausible by itself.

Never generate every frame independently. Never accept an in-between pass whose style or identity differs from the approved key poses.

### 5. Remove the background and normalize frames

Remove the flat chroma-key background locally and check soft edge alpha plus magenta residue. Split cells in reading order.

Place each frame on one RGBA canvas using one common scale and alignment transform. Do not independently auto-fit frames. Maintain the stable foot baseline and direction. Place the exact source at frame 00 using translation only, then copy frame 00 byte-for-byte to frame 13.

Keep all PNG frames transparent. Build `preview.gif` by compositing every RGBA frame over a perfectly solid white `#FFFFFF` background. Do not use transparency, checkerboards, gray, or dark preview backgrounds.

Name full frames contiguously from `hero-attack_00.png` through `hero-attack_13.png`. Name key frames with the same prefix and their reserved indices: `_02`, `_05`, `_08`, and `_11`.

### 6. Correct temporal and identity drift

Compare adjacent frames and correct only the failing region or pose. Regenerate affected in-betweens after a key pose changes.

Check face, emblem, palette, outline, accessories, limb count, markings, weapon dimensions, scale, center, baseline, trajectories, and silhouette continuity.

If an active limb switches shoulders, becomes ambiguous behind the torso, or inherits the anchor limb's markings, reject the affected pose. Regenerate the key pose and every dependent in-between. Never repair a limb switch by mirroring an isolated frame, relabeling the side, or accepting the hand trajectory without checking its shoulder origin.

### 7. Validate outputs

Run deterministic validation for the 14-frame relationship:

```powershell
python scripts/validate_14frame_pattern.py --baseline source.png --keyframes-dir output/keyframe --fullframes-dir output/fullframe --preview output/preview.gif --prefix hero-attack
```

Inspect a contact sheet and playback loop. Confirm:

- contiguous names, RGBA mode, one canvas size, and transparent corners;
- exactly 14 full frames and exactly four key frames at 02/05/08/11;
- frame 00 equals frame 13 byte-for-byte after output, and both are the source translated without redraw or scaling;
- every key-frame file is pixel-identical to its matching full-frame index;
- `preview.gif` contains exactly 14 frames on a solid white `#FFFFFF` background;
- no chroma fringe or magenta residue;
- no identity drift, missing details, extra limbs, or scale popping;
- the active limb traces back to the same shoulder in every adjacent frame;
- the anchor limb stays visible, attached to its original shoulder, and non-attacking;
- side-specific spots, claws, armor, or accessories follow the correct limb across torso overlap;
- stable foot baseline and center;
- readable anticipation, acceleration, contact, contact hold, and recovery;
- smooth loop endpoints when looping is requested.

Correct failures and repeat both visual and deterministic validation. Report exact output paths and evidence.

## Output contract

```text
output/
|-- keyframe/              # exact generated anchors at 02, 05, 08, 11
|-- fullframe/             # contiguous transparent RGBA sequence 00-13
|-- spritesheet.png        # packed sequence
|-- contact-sheet.png      # visual consistency review
|-- preview.gif            # 14-frame playback loop on solid white #FFFFFF
`-- manifest.json          # source, canvas, side/topology lock, key indices, segment plan, frame order
```

## Quick reference

| Stage | Gate |
|---|---|
| Identity | Immutable features, screen-space side mapping, and limb topology are recorded |
| Key poses | Exactly four anchors occupy 02, 05, 08, and 11 |
| In-betweens | Fixed 1/2/2/2/1 insertions fill the five anchor segments |
| Normalize | One scale, canvas, direction, and stable foot baseline |
| Correct | Adjacent frames preserve identity and trajectory continuity |
| Deliver | Deterministic checks, contact sheet, and playback loop pass |

## Example

User: "Use this golem image to make a heavy ground-smash attack."

Record its identity lock, generate four anchors for 02/05/08/11 together, fill the 1/2/2/2/1 segment insertions, place the exact baseline at 00 and 13, inspect contact and playback, validate the 14-frame relationships, and deliver the transparent sequence.

## Common mistakes

- Generating each frame separately: identity and timing drift. Use one shared key-pose sheet and reference-guided in-betweens.
- Treating key poses as loose references: copy the approved 02/05/08/11 files exactly into `fullframe/`; never regenerate them during interpolation.
- Redrawing loop endpoints: frames 00 and 13 must be the same translated baseline pixels, not similar-looking generations.
- Auto-fitting every pose: scale pops between frames. Apply one common transform.
- Accepting a pretty key pose with changed details: visual quality does not excuse identity drift.
- Treating "left" or "right" as self-evident: normalize to screen space and record anatomy separately when needed.
- Tracking only the hand tip: an arm can cross the torso while silently switching shoulders. Trace the complete limb and keep the opposite arm as an anchor.
- Fixing a switch by mirroring one frame: this reverses markings and topology. Regenerate the key pose and dependent in-betweens.
- Adding effects during character generation: detached dust and motion lines complicate extraction. Add effects later as separate assets.
- Checking only individual PNGs: a frame can look good alone and fail in motion. Inspect the contact sheet and playback loop.
- Trusting the generated background: remove chroma locally and measure magenta residue.
- Using a transparent, checkerboard, gray, or dark GIF background: composite every preview frame over solid white `#FFFFFF`.
