# Whole-Character Key-Pose Redraw

Use this path for large silhouette changes, heavy overlap, squash, perspective, or foreshortening that a rigid cutout cannot express cleanly.

## 1. Establish the identity lock

Record the immutable features: face, palette, proportions, outline weight, emblems, accessories, moss or markings, limb count, hand order, facing direction, and weapon dimensions. Keep the baseline visible during every generation and correction pass.

## 2. Create shared key poses

Generate guard, anticipation, contact, and recovery together on one sheet. For an attack, make the contact pose the clearest silhouette and add a contact hold when timing benefits from impact emphasis.

Use a complete whole-character redraw for each pose. Permit newly visible surfaces, natural overlap, squash, and perspective. Never rotate cutout limbs to fake a pose that requires redrawing.

## 3. Generate reference-guided in-betweens

Use both the baseline and approved key-pose sheet as references. Generate in-betweens together in chronological order so trajectories remain coherent. Never generate every frame independently.

Reject any pass that changes identity, duplicates features, loses accessories, reverses hand order, or jumps between silhouettes without a readable transition.

## 4. Produce transparency and normalize

For built-in image generation, render on a flat `#ff00ff` chroma-key background when the character contains green or blue. Remove the key locally, then check transparent corners, soft edge alpha, and magenta residue.

Split cells in reading order. Apply one common scale to the sequence, center consistently, and maintain a stable foot baseline. Do not auto-fit each frame independently because that creates scale popping. Use the exact baseline as the first and last frame when a seamless loop is required.

## 5. Correct and validate

Inspect a contact sheet and playback loop. Compare adjacent frames for:

- face, emblem, palette, outline, and accessory drift;
- missing or duplicated limbs and markings;
- unstable scale, center, or stable foot baseline;
- abrupt limb trajectories or weak anticipation;
- contact and contact hold readability;
- dirty alpha, chroma fringe, or magenta residue.

Correct only the failing region or frame, regenerate affected in-betweens, and recheck the complete playback loop. Run `scripts/validate_outputs.py` after visual acceptance.

## Prompt contract

Specify the ordered beats, immutable identity features, equal cell geometry, stable baseline, flat chroma color, and prohibited extras. Require complete characters with no labels, borders, shadows, effects, debris, or fused cells.
