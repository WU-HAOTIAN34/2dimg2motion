# Whole-Character Key-Pose Redraw

Use this path when an action requires large silhouette changes, heavy overlap, squash/stretch, perspective, or foreshortening. These motions cannot be expressed cleanly by rotating rigid cutouts; built-in `image_gen` should redraw the complete character.

Keyframes and in-betweens must come from model image generation. Do not use scripts, Pillow, OpenCV, canvas, SVG, bone slicing, affine transforms, or procedural interpolation to produce motion artwork. Local scripts are allowed only for chroma-key removal, splitting, packing, previews, manifests, and validation.

## 0. Hard Failure Constraints

Reject the batch and call `image_gen` again if any of the following occurs:

- Weapon or active hand swaps sides: prompts must lock `weaponHand` and `emptyHand`, for example `screen-right sword hand remains the sword hand in every frame; screen-left hand remains empty/counterbalance`. If a sword, club, spear, staff, or similar weapon moves to the other hand, regenerate.
- Chroma key conflicts with subject colors: choose the key based on subject colors before generation. For green/blue subjects, prefer `#ff00ff`; for pink/purple/magenta subjects, avoid `#ff00ff` and prefer `#00ffff` or another absent pure color. If matting removes body, weapon, eyes, armor, horns, teeth, or outlines, change the key and regenerate.
- Gutters are insufficient: sprite strips must require large chroma-key gutters, centered cells, complete weapons inside cells, and no mutual contact. If equal splitting cuts the subject or creates neighboring fragments, do not deliver; regenerate with larger gutters or shorter strips.
- Canvas is insufficient: if a weapon tip, horn, ear, foot, or tail touches an edge or is cropped, enlarge the final canvas or regenerate.
- Validation passes but visuals fail: structural validation is not art acceptance. Inspect `contact-sheet.png` and `preview.gif` for no hand swaps, cuts, missing colors, fragments, or scale popping.
- Output is polluted: the final directory contains only contract artifacts. Model source images, alpha sources, failed drafts, and temporary splits must live in a temporary directory and be cleaned before delivery.

## 1. Establish the Identity Lock

Record all immutable features: face, palette, proportions, outline weight, emblems, accessories, moss or markings, limb count, hand order, facing direction, and weapon dimensions. Keep the baseline visible during every generation and correction pass.

Prompts are pose instructions, not the identity source. When generating key poses, use the baseline frame image as the visual identity anchor. If the tool cannot pass the baseline image directly as reference, require `image_gen` to create a `reference identity cell` as the first cell of the pose sheet, closely reproducing the baseline appearance; the next four cells are 02/05/08/11. The reference cell is only for alignment review and must not enter the final frame sequence.

## 2. Create Shared Key Poses

Call built-in `image_gen` and generate the four defining poses together in one pose sheet, assigning them to final indices 02, 05, 08, and 11. Attacks usually use anticipation, acceleration/contact, contact hold/follow-through, and recovery; frames 00 and 13 remain the exact baseline frame.

Do not generate 02, 05, 08, and 11 in four independent calls. Independent generation makes the model reinterpret the character each time, causing subtle cumulative identity drift such as eye placement changes, weapon length changes, clothing pattern changes, thinner/fatter proportions, outline-weight changes, or color shifts. Key poses must be same-batch, same-sheet, same-chroma-key, same-canvas, same-gutter generation, sharing the same identity block.

The pose-sheet prompt must explicitly state:

- `use the provided baseline image as the exact visual identity source, not loose inspiration`;
- `only change pose and animation timing`;
- `preserve silhouette language, body-part count, face/eyes, markings, weapon size, color palette, outline weight, and style`;
- `do not redesign, simplify, beautify, add details, remove details, change proportions, or reinterpret the character`.

Each pose should redraw the complete character. Newly visible surfaces, natural overlap, squash/stretch, and perspective changes are allowed. Never rotate cutout limbs to fake a pose that requires redraw.

The key-pose sheet must explicitly specify gutter and topology constraints: complete character, complete weapon, equal centered cells, large chroma-key gutters, no labels, no borders, no neighboring fragments. For weapon actions, repeat the same `weaponHand` and `emptyHand` lock in every cell.

Before approving the key-pose sheet, compare the baseline frame, reference identity cell, and four key poses side by side. Pose, overlap, and perspective may vary; subject identity, art style, proportion language, signature details, weapon ownership, body-part count, and color relationships may not drift. If it reads like "same series variant" rather than "same character in a new pose," the whole batch fails and must be regenerated.

## 3. Generate Reference-Guided In-Betweens

Call built-in `image_gen` while using both the baseline image and the approved key-pose sheet as references. Fill the anchor sequence `00 -> 02 -> 05 -> 08 -> 11 -> 13` with 1/2/2/2/1 inserted frames. Generate each segment in chronological order; do not replace any anchor with a newly generated approximation.

Reject any pass that changes identity, duplicates features, loses accessories, reverses hand order, or creates unreadable jumps between silhouettes.

If a single 14-frame strip is crowded or unstable to split, generate shorter strips such as `01-06` and `07-12`. Shorter batches still must come from `image_gen` and must share the same identity lock, weaponHand/emptyHand lock, chroma key, and gutter constraints.

If a key pose or in-between fails, rewrite the prompt and call `image_gen` again. Do not use script warping, copied limbs, local rotation, or procedural interpolation to "fix" it into a new pose.

## 4. Produce Transparency and Normalize

When using built-in `image_gen`, use a flat `#ff00ff` chroma-key background if the character contains green or blue. Then remove the key locally and inspect transparent corners, soft-edge alpha, and chroma residue.

Do not mechanically use `#ff00ff`. If the character contains pink, purple, magenta, or similar soft edges, use `#00ffff` or another non-conflicting pure color. After matting, check whether subject colors were removed; if any subject color is missing, stop post-processing and regenerate the source image.

Split cells in reading order. Apply one common scale to the entire sequence, center consistently, and maintain a stable foot/bottom baseline. Do not auto-fit each frame independently, because that creates scale popping. Place the exact baseline into frame 00 using translation only, and copy frame 00 exactly to frame 13. Copy the four approved keyframes exactly into full-frame indices 02/05/08/11. Local processing may organize generated images only; it must not create new character motion.

After splitting cells, only remove small disconnected alpha fragments separated from the subject. If the subject, weapon, horn, or foot is cut, or a fragment is connected to the subject, regenerate the source image instead of painting or locally deforming it.

All PNG frames should remain transparent. When encoding `preview.gif`, composite each frame over pure white `#FFFFFF`.

## 5. Correct and Validate

Inspect the contact sheet and playback loop. When comparing adjacent frames, focus on:

- face, emblems, palette, silhouette, and accessory drift;
- missing or duplicated limbs and markings;
- whether the weapon remains in the same screen-space hand and the other hand remains anchoring/counterbalancing;
- unstable proportions, center, or foot/bottom baseline;
- abrupt limb trajectories or weak anticipation;
- contact pose and contact-hold readability;
- dirty alpha, chroma edges, or magenta residue.

Correct only the failing region or failing frame. If a key pose changes, regenerate affected in-betweens and recheck the complete playback loop. After visual acceptance, run `scripts/validate_14frame_pattern.py`. After validation passes, inspect the contact sheet and GIF again; never use validation `OK` as a substitute for visual acceptance.

## Prompt Contract

Prompts should explicitly state ordered motion beats, immutable identity features, equal cell geometry, stable baseline, flat chroma-key background, and prohibited extras. Require a complete character in every cell, with no labels, borders, shadows, effects, debris, or fused cells.
