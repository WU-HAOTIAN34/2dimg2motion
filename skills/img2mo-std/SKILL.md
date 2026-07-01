---
name: img2mo-std
description: Standardize a 2D animation baseline image with `/img2mo-std xxx.png/pos`. Use when preparing a character, creature, prop, or weapon baseline before motion generation, especially if the source image is too large, tightly cropped, lacks transparent action margin, has a white background, or later walk/attack/idle frames show clipping, overlap, scale popping, or inconsistent character size.
---

# Img2mo-std

## Overview

Use this skill when the user invokes:

```text
/img2mo-std xxx.png/pos
```

The command audits and standardizes a baseline frame before animation generation. It creates a smaller, padded, transparent-canvas source image that leaves enough room for walk, attack, idle, weapon swing, cape, tail, horn, or limb stretch poses.

## Input Resolution

Resolve the argument after `/img2mo-std` as follows:

1. If it is an existing relative or absolute path, use it directly.
2. If it is a bare file name such as `s7.png`, first try `sample\s7.png`.
3. If it has no extension such as `s7`, first try `sample\s7.png`, then `sample\s7.jpg`, then `sample\s7.webp`.
4. If no matching image exists, report the missing path and do not guess from unrelated files.

Examples:

```text
/img2mo-std s7
/img2mo-std s7.png
/img2mo-std sample\s7.png
/img2mo-std C:\AI\2dimg2motion-v1\sample\s7.png
```

## Audit Criteria

A baseline is not standard if any of these are true:

- The foreground subject is larger than about 300-400 px on its longest side.
- The subject touches or nearly touches the canvas edge.
- There is not enough empty transparent space for arms, legs, weapons, tails, capes, horns, or effects to extend during motion.
- The background is opaque white or near-white when the character should be isolated.
- The source has a huge canvas that will slow generation without adding useful detail.
- Previous generated frames show inconsistent character size, off-center motion, clipped body parts, or crowded sprite-sheet cells.

## Tool

Run the repository tool from the workspace root after resolving the image path:

```powershell
python scripts\standardize_baseline.py <resolved-image-path>
```

Default output:

```text
sample\<input-stem>-standard.png
```

Useful options:

```powershell
python scripts\standardize_baseline.py sample\s7.png --subject-max 360 --margin-ratio 0.75
python scripts\standardize_baseline.py sample\s7.png --output sample\s7-standard.png
python scripts\standardize_baseline.py sample\s7.png --check-only
```

Recommended default target:

- Subject longest side: `360`
- Margin ratio: `0.65` to `0.85`
- Output format: PNG with transparency

## Report Interpretation

The tool prints a JSON report. Treat the standardized output as ready when:

- `needs_standardization` is `false` after processing.
- `subject_longest_side` is between 300 and 400.
- `edge_clearance_ratio` leaves enough room for the intended motion.
- `warnings` is empty or only contains acceptable notes.

If the report still warns that the image is tight or too large, rerun with a smaller `--subject-max` or larger `--margin-ratio`.

## Animation Workflow Rule

After `/img2mo-std`, use the standardized output image as the baseline for all later walk, attack, idle, or other sprite generation. Do not continue from the original oversized or tightly cropped source unless the user explicitly asks to bypass standardization.
