# Motion Prompt Patterns

This document distills reusable prompt patterns learned from sample motion frames. The samples are study inputs only; this skill does not depend on those source files being present.

Sections:

- [Library Shape](#library-shape)
- [Attack Timing](#attack-timing)
- [Stable Canvas Rules](#stable-canvas-rules)
- [Topology Locks](#topology-locks)
- [Weapons, Props, and Accessories](#weapons-props-and-accessories)
- [Non-Humanoid Creature Motion](#non-humanoid-creature-motion)
- [Action Templates](#action-templates)
- [Recommended Prompt Block](#recommended-prompt-block)
- [Practical Generation Notes](#practical-generation-notes)

## Library Shape

The study sample used for this distillation contained 17 character folders and 213 named sequences.

Common action families:

| Action | Count | Typical frame count | Motion scale |
|---|---:|---|---|
| `idle` | 17 | 21 | very small breathing, about 5% width/height variation |
| `move` | 17 | 12-21 | walk cycle, about 16% width variation |
| `block` | 17 | 11 | guarded pose, mostly fixed baseline |
| `attack01/02/03` | 51 | 14-21 | wide silhouette expansion, about 1.5-1.6x width |
| `suffer/suffer02` | 34 | 15-18 | recoil, squash, stars/bones sometimes present |
| `death` | 17 | 11-30 | large fall/collapse, about 1.9x height variation |
| `born` | 17 | 15-42 | very large emergence/reveal |
| `skill01` | 8 | 21-61 | broadest special-effect or cast sequence |
| `vertigo` | 17 | 21 | small body cycle with eye/effect variation |

The strongest general rule is: **the foot/bottom baseline is usually stable**. Attacks may grow wider and lower, but they should not appear to resize frame by frame.

## Attack Timing

Most attacks follow this beat structure:

1. **Neutral guard**: readable source pose.
2. **Anticipation**: 2-4 frames of crouch, wind-up, arm lift, or body lean.
3. **Acceleration**: 1-3 frames that travel quickly toward the contact silhouette.
4. **Contact**: the clearest frame; active weapon, claw, horn, fist, or body point is extended.
5. **Contact hold / follow-through**: 2-5 frames, often duplicated or only slightly changed.
6. **Recovery**: 3-6 frames returning to the neutral guard.

Prompt language:

```text
Design the attack as guard -> anticipation -> acceleration -> contact -> contact hold -> recovery.
The contact pose must have the clearest silhouette.
Use a short contact hold; do not make every frame equally different.
Keep the foot/bottom baseline stable while allowing the attack silhouette to widen.
```

## Stable Canvas Rules

The reference library commonly keeps a fixed canvas and a stable lower anchor. For generated sprite sheets, make the prompt explicit:

```text
Same apparent character size in every cell.
Same foot/bottom baseline in every cell.
Body center stays near the same cell center except for intentional lunges.
Complete character, weapons, horns, ears, tails, claws, and effects remain inside the cell.
Allow the silhouette to widen for attacks, but do not scale the character smaller or larger.
```

For local post-processing, prefer:

```text
Use one shared scale for all generated frames.
Use one fixed foot/bottom baseline.
Do not auto-fit each frame independently.
If an attack pose needs more horizontal room, enlarge the output canvas instead of shrinking the character.
```

## Topology Locks

Weapon and active-limb side consistency must be stated in screen space.

Weapon attack:

```text
coordinateSpace: screen-space.
weaponHand: screen-right hand remains the weapon hand in every frame.
The weapon handle stays visibly inside the screen-right hand or wrist cuff.
emptyHand: screen-left hand remains empty and counterbalancing, never touching the weapon.
The active arm stays connected to the same screen-right shoulder even when crossing the torso.
Do not mirror the character. Do not swap hands.
```

Central body or horn attack:

```text
active attack: central head/top horn and whole torso lunge.
screen-left claw and screen-right claw remain on their original sides as anchors.
The top horn remains centered on the head in every frame.
Side spikes remain attached to the same sides of the body.
Do not duplicate, hide, or swap side-specific claws, horns, ears, armor, or markings.
```

## Weapons, Props, and Accessories

Classify every non-body element before writing motion beats:

| Type | Meaning | Prompt lock |
|---|---|---|
| `activeWeapon` | Sword, club, axe, spear, staff, shield bash, or held object that creates contact | lock `weaponHand`, handle contact, weapon length, arc, and return pose |
| `carriedProp` | Torch, bottle, orb, bag, food, banner, or object held but not used as the main hit | lock owner hand and attachment; allow secondary sway only |
| `passiveAccessory` | Helmet crest, cape, embedded arrow/sword, shell spikes, antlers, back crystals, belt items | lock attachment point on the body surface; do not turn it into a limb or weapon |
| `detachedProp` | Thrown axe, released projectile, dropped item | specify release frame, flight path, visibility, and whether it returns before the loop |

Ownership prompt:

```text
prop taxonomy:
- activeWeapon: screen-right sword; screen-right hand owns the handle in every frame.
- carriedProp: none.
- passiveAccessory: helmet crest and belt pouch follow the torso surface.
- detachedProp: none; do not release or duplicate the weapon.
The handle/contact point remains visibly attached to the same screen-space hand or cuff.
The offhand keeps its role: empty, shield, brace, or counterbalance; it never becomes the weapon hand.
```

Shield or offhand prop:

```text
screen-left shield remains attached to the screen-left forearm in every frame.
The shield may raise, brace, or lead a block, but it does not switch arms and does not become the sword.
screen-right sword hand remains separate and readable.
```

Torch, flame, orb, or glowing carried prop:

```text
The flame/orb is a carriedProp owned by the locked hand.
The glow may flicker and trail slightly, but the handle/core stays attached to the same hand.
Do not detach the flame into loose particles in the character sheet unless a separate effect layer is requested.
Choose a chroma key absent from the glow color.
```

Embedded or surface-bound accessories:

```text
Embedded sword/arrow/spikes/crystals are passiveAccessory features.
They follow the same body-surface attachment points through squash/stretch.
They may tilt with the surface, but they do not float, slide, multiply, become attacking limbs, or detach.
```

Long weapons, antlers, tails, branches, and banners need larger canvas gutters. Do not shrink the whole character to fit them; enlarge the final canvas and keep the apparent body scale stable.

Common prop failures to reject:

- weapon or shield changes screen-space hand;
- prop jumps to the opposite side when crossing the body centerline;
- weapon length, shield size, torch handle, or embedded accessory count drifts;
- passive decoration becomes an active attack without being requested;
- embedded accessories float above a squashing body surface;
- thrown/detached props appear without a release/return beat;
- chroma key removes glow, metal edges, outlines, horns, or accessory highlights.

## Non-Humanoid Creature Motion

For creatures, define `activeFeature` instead of forcing a humanoid `activeLimb`.

| Archetype | Useful activeFeature | Stable anchors |
|---|---|---|
| Blob / slime | belly mass, head nub, whole-body squash, embedded surface item | bottom puddle, face, embedded accessories |
| Quadruped / beast | head, jaw, horn, front paw, torso lunge, tail | feet contact pattern, shoulder/hip mass, head direction |
| Tree / antler / branch creature | trunk, branch sweep, antlers, root-feet | trunk base, root feet, branch attachment |
| Spiked / armored creature | shell, belly, horn, shoulder spike, body bash | bottom line, side spikes, armor plates |
| Tail / wing creature | tail root-to-tip arc, wing sweep, horn, jaw | tail root, body mass, feet/bottom anchor |

Creature prompt block:

```text
subject topology: non-humanoid creature.
activeFeature: [horn / tail / branch / jaw / shell / whole-body mass].
anchorSurface: [bottom mass / root feet / four feet / shell rim / tail root].
Do not invent human arms or hands unless they exist in the baseline.
Side-specific spikes, horns, spots, plates, and accessories remain attached to their original side.
Track the feature from root to tip, not only the tip position.
```

Blob / slime attack:

```text
Motion beats: low squash anticipation -> forward belly/head stretch -> compressed contact hold -> rebound to puddle baseline.
The bottom puddle remains the anchor.
Face features stretch with the body but keep identity.
Embedded passive accessories stay planted in the slime surface and follow the deformation.
```

Branch, antler, or tail sweep:

```text
Motion beats: root braces -> feature coils/pulls back -> root-to-tip sweep creates the widest contact silhouette -> feature follows through -> returns.
The tail/branch/antler root remains attached in every frame.
Use a larger canvas gutter for the widest arc; do not shrink the creature.
```

Quadruped or beast lunge:

```text
Use contact/down/passing/up logic for feet when moving.
For attack, compress hind mass, push forward with front feature or jaw, hold contact briefly, then recover.
Head and torso counterbalance; do not redesign the creature into a biped.
```

## Action Templates

### Compact Melee Slash

Best for sword, club, axe, spear butt, or one-arm slash.

```text
Attack type: compact one-handed melee slash.
Motion beats:
- frame 02 anticipation: knees compress, torso leans back, weapon hand draws the weapon up/back on its locked screen side.
- frame 05 acceleration/contact: fast slash or chop, weapon extended in the clearest readable silhouette.
- frame 08 contact hold/follow-through: weapon reaches the low/front end of the arc; body is overcommitted but balanced.
- frame 11 recovery: weapon returns to ready guard on the same screen side.
Constraints: weapon hand never swaps; empty hand stays empty; same scale and foot baseline; no motion trails unless generated as separate effects.
```

### Horn / Body Bash

Best for creatures with horns, shells, heads, or whole-body charge attacks.

```text
Attack type: horn-and-body bash.
Motion beats:
- frame 02 anticipation: body compresses low, head/horn pulls back, side limbs brace.
- frame 05 acceleration/contact: body lunges forward/down; horn, shell, or face is the contact point.
- frame 08 contact hold: body is lowest and most compressed after impact; active central feature remains attached and readable.
- frame 11 recovery: body rises and re-centers toward neutral.
Constraints: active attack is central body/head, not a side limb; side claws or legs remain anchors; same scale and stable bottom baseline.
```

### Claw Swipe

Best for monsters with large visible claws.

```text
Attack type: locked-side claw swipe.
Motion beats:
- frame 02 anticipation: active claw pulls back; anchor claw stays visible and attached.
- frame 05 contact: active claw reaches maximum extension across the front of the body.
- frame 08 follow-through: torso twists, active claw passes through the target line, anchor claw counterbalances.
- frame 11 recovery: active claw returns to guard.
Topology: active=screen-left or screen-right; anchor=opposite side. Track shoulder-to-claw, not just claw tip.
```

### Ground Smash

Best for heavy monsters, golems, fists, clubs, shields, or two-arm attacks.

```text
Attack type: heavy ground smash.
Motion beats:
- frame 02 anticipation: body rises or pulls weapon/fists overhead.
- frame 05 acceleration/contact: body drops hard; fists/weapon reach the ground line.
- frame 08 contact hold: lowest squash, shoulders compressed, impact silhouette widest.
- frame 11 recovery: body rebounds upward but remains heavy.
Constraints: stable feet or bottom mass, strong vertical squash/stretch, no detached dust in character frames.
```

### Idle

```text
Motion type: idle breathing loop.
Small settle -> rise -> settle cycle.
Only change body height, shoulders, head bob, and accessory sway slightly.
Width and height variation should remain subtle, around 5%.
Same foot baseline and same center.
```

### Move / Walk

```text
Motion type: walk cycle.
Use contact -> down -> passing -> up -> opposite contact.
Feet alternate clearly while body mass stays stable.
Canvas, scale, and foot baseline remain consistent.
Allow small vertical bob and cape/tail/accessory drag.
```

### Block

```text
Motion type: block.
Raise shield, weapon, arms, or body armor into guard, hold briefly, then return.
Motion is compact, with fixed feet and very little scale change.
The guard silhouette should be readable by frame 03-05.
```

### Suffer / Hit

```text
Motion type: hit reaction.
Impact -> recoil -> squash/stretch -> recovery.
The face and eyes may exaggerate; accessories may lag.
Keep the character identity intact.
Use small floating hit icons only if requested; otherwise keep effects separate.
```

### Death

```text
Motion type: death collapse.
Imbalance -> fall -> impact -> rest.
This action may use a larger canvas and bigger silhouette changes than attacks.
Keep the final rest pose readable and stable for several frames.
Do not force the final frame to loop back to neutral.
```

### Born / Spawn

```text
Motion type: spawn / born.
Start from a small seed, egg, portal, or curled silhouette, then unfold into the full character.
This action may have very large size changes because the subject is emerging.
Final frames should converge to the exact neutral identity.
```

### Skill / Cast

```text
Motion type: skill cast.
Anticipation -> charge -> peak cast -> hold -> recovery.
The body may stretch upward or open arms/wings, but identity features stay locked.
If effects are needed, generate them as separate overlays or clearly detached layers.
```

## Recommended Prompt Block

Use this block in every sprite-generation prompt:

```text
Preserve the exact baseline identity: silhouette language, body-part count, face/eyes, markings, clothing/armor, weapon or active feature, color palette, outline weight, and cartoon sprite style.
Only change pose, squash/stretch, overlap, and animation timing.
Do not redesign, simplify, beautify, add details, remove details, change proportions, or reinterpret the character.

Declare prop taxonomy before motion:
- activeWeapon: [none or locked owner + contact role].
- carriedProp: [none or locked owner + secondary sway].
- passiveAccessory: [surface attachment points; follows body deformation].
- detachedProp: [none unless release frame/path/return is specified].

For non-humanoid subjects, declare creature topology:
- activeFeature: [horn / jaw / tail / branch / shell / belly mass / whole body].
- anchorSurface: [bottom puddle / root feet / four feet / shell rim / tail root].
- do not invent human limbs or hand ownership that the baseline does not show.

Generate equal cells with large flat chroma-key gutters.
Same apparent character size in every cell.
Same foot/bottom baseline in every cell.
Complete subject inside each cell with generous safety margin.
No labels, numbers, borders, shadows, dust, trails, detached effects, floor plane, or gradients.
```

## Practical Generation Notes

- Use 5-cell key-pose sheets: reference identity + frame 02 + frame 05 + frame 08 + frame 11.
- Use short in-between sheets instead of crowded long strips. Two 4-cell sheets, `01/03/04/06` and `07/09/10/12`, are easier to keep consistent.
- If model output changes scale, regenerate the source sheet. Do not hide scale drift by auto-fitting frames independently.
- If a pose needs more horizontal room, enlarge the final canvas rather than shrinking the sequence.
- If validation passes but contact sheet shows hand swaps, scale popping, cut weapons, or drifting centers, reject the batch.
