# Whole-Character Key-Pose Redraw

Use this path for large silhouette changes, heavy overlap, squash, perspective, or foreshortening that a rigid cutout cannot express cleanly.

## 1. Establish the identity lock

Record the immutable features: face, palette, proportions, outline weight, emblems, accessories, moss or markings, limb count, hand order, facing direction, and weapon dimensions. Keep the baseline visible during every generation and correction pass.

## 2. Create shared key poses

Generate exactly four defining poses together on one sheet and assign them to final indices 02, 05, 08, and 11. For an attack, use anticipation, acceleration/contact, contact hold/follow-through, and recovery; reserve the exact baseline for frames 00 and 13.

Use a complete whole-character redraw for each pose. Permit newly visible surfaces, natural overlap, squash, and perspective. Never rotate cutout limbs to fake a pose that requires redrawing.

## 3. Generate reference-guided in-betweens

Use both the baseline and approved key-pose sheet as references. Fill the anchor sequence `00 -> 02 -> 05 -> 08 -> 11 -> 13` with 1/2/2/2/1 inserted frames. Generate each segment in chronological order and never replace an anchor with a newly generated approximation.

Reject any pass that changes identity, duplicates features, loses accessories, reverses hand order, or jumps between silhouettes without a readable transition.

## 4. Produce transparency and normalize

For built-in image generation, render on a flat `#ff00ff` chroma-key background when the character contains green or blue. Remove the key locally, then check transparent corners, soft edge alpha, and magenta residue.

Split cells in reading order. Apply one common scale to the sequence, center consistently, and maintain a stable foot baseline. Do not auto-fit each frame independently because that creates scale popping. Place the exact baseline at frame 00 using translation only and copy it exactly to frame 13. Copy the four approved key frames exactly into full-frame indices 02/05/08/11.

Keep PNG frames transparent. Composite each playback frame over solid white `#FFFFFF` when encoding `preview.gif`.

## 5. Correct and validate

Inspect a contact sheet and playback loop. Compare adjacent frames for:

- face, emblem, palette, outline, and accessory drift;
- missing or duplicated limbs and markings;
- unstable scale, center, or stable foot baseline;
- abrupt limb trajectories or weak anticipation;
- contact and contact hold readability;
- dirty alpha, chroma fringe, or magenta residue.

Correct only the failing region or frame, regenerate affected in-betweens, and recheck the complete playback loop. Run `scripts/validate_14frame_pattern.py` after visual acceptance.

## Prompt contract

Specify the ordered beats, immutable identity features, equal cell geometry, stable baseline, flat chroma color, and prohibited extras. Require complete characters with no labels, borders, shadows, effects, debris, or fused cells.
