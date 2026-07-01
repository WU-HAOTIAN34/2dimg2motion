from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def bbox_from_alpha(alpha: np.ndarray, threshold: int = 0) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(alpha > threshold)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def morph(mask: np.ndarray, op: str, iterations: int) -> np.ndarray:
    img = Image.fromarray((mask.astype(np.uint8) * 255), "L")
    for _ in range(iterations):
        if op == "dilate":
            img = img.filter(ImageFilter.MaxFilter(3))
        elif op == "erode":
            img = img.filter(ImageFilter.MinFilter(3))
        elif op == "open":
            img = img.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
        elif op == "close":
            img = img.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
        else:
            raise ValueError(op)
    return np.array(img) > 0


def connected_components(mask: np.ndarray) -> list[list[tuple[int, int]]]:
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    comps: list[list[tuple[int, int]]] = []
    for y in range(h):
        xs = np.flatnonzero(mask[y] & ~seen[y])
        for x0 in xs:
            if seen[y, x0]:
                continue
            stack = [(y, int(x0))]
            seen[y, x0] = True
            comp: list[tuple[int, int]] = []
            while stack:
                cy, cx = stack.pop()
                comp.append((cy, cx))
                for ny in (cy - 1, cy, cy + 1):
                    for nx in (cx - 1, cx, cx + 1):
                        if ny == cy and nx == cx:
                            continue
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            stack.append((ny, nx))
            comps.append(comp)
    return comps


def extract_frames(video: Path, tmp_dir: Path) -> list[Path]:
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video), "-an", "-vsync", "0", str(tmp_dir / "frame_%04d.png")],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return sorted(tmp_dir.glob("frame_*.png"))


def make_mask(rgb: np.ndarray) -> np.ndarray:
    arr = rgb.astype(np.float32)
    # White background is near 255. Keep darker character pixels and gray sword-arc effects.
    distance_from_white = np.max(255.0 - arr, axis=2)
    mask = distance_from_white > 22
    # Faint watermarks near the bottom are tiny and pale; this threshold keeps slash effects.
    mask = morph(mask, "close", 1)
    mask = morph(mask, "dilate", 1)
    return mask


def remove_small_and_watermark(mask: np.ndarray) -> np.ndarray:
    out = np.zeros_like(mask, dtype=bool)
    h, w = mask.shape
    for comp in connected_components(mask):
        ys = [p[0] for p in comp]
        xs = [p[1] for p in comp]
        area = len(comp)
        bw = max(xs) - min(xs) + 1
        bh = max(ys) - min(ys) + 1
        cy = sum(ys) / area
        low_faint_text = cy > h * 0.72 and area < 1200 and bw < 180 and bh < 60
        if area >= 90 and not low_faint_text:
            for y, x in comp:
                out[y, x] = True
    return out


def cut_video_frame(path: Path) -> tuple[Image.Image, int]:
    src = Image.open(path).convert("RGB")
    rgb = np.array(src)
    mask = remove_small_and_watermark(make_mask(rgb))
    alpha = (mask.astype(np.uint8) * 255)
    bbox = bbox_from_alpha(alpha)
    if bbox is None:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0)), 1

    rgba = np.dstack([rgb, alpha]).astype(np.uint8)
    cut = Image.fromarray(rgba, "RGBA").crop(bbox)
    visible = cut.getbbox()
    if visible is not None:
        cut = cut.crop(visible)

    # Estimate body scale from high-opacity/dark character pixels; slash effect can be much wider.
    cut_rgb = np.array(cut.convert("RGB")).astype(np.float32)
    cut_alpha = np.array(cut.getchannel("A"))
    dark = (cut_alpha > 0) & (np.max(255.0 - cut_rgb, axis=2) > 70)
    body_bbox = bbox_from_alpha((dark.astype(np.uint8) * 255))
    if body_bbox is None:
        body_bbox = cut.getbbox()
    body_h = max(1, body_bbox[3] - body_bbox[1])
    return cut, body_h


def clean_video_frame(
    path: Path,
    canvas: tuple[int, int],
    scale: float,
    baseline_bottom: int,
) -> Image.Image:
    cut, _ = cut_video_frame(path)
    new_size = (max(1, round(cut.width * scale)), max(1, round(cut.height * scale)))
    cut = cut.resize(new_size, Image.Resampling.LANCZOS)
    visible = cut.getbbox()
    if visible is None:
        return Image.new("RGBA", canvas, (0, 0, 0, 0))

    out = Image.new("RGBA", canvas, (0, 0, 0, 0))
    visible_center_x = (visible[0] + visible[2]) / 2
    x = round(canvas[0] / 2 - visible_center_x)
    y = baseline_bottom - visible[3]
    out.alpha_composite(cut, (x, y))
    out = remove_tiny_alpha_fragments(out)
    return out


def remove_tiny_alpha_fragments(image: Image.Image) -> Image.Image:
    arr = np.array(image)
    alpha = arr[:, :, 3] > 0
    rgb = arr[:, :, :3].astype(np.float32)
    for comp in connected_components(alpha):
        area = len(comp)
        ys = [p[0] for p in comp]
        xs = [p[1] for p in comp]
        bw = max(xs) - min(xs) + 1
        bh = max(ys) - min(ys) + 1
        sample = rgb[ys, xs]
        avg = sample.mean(axis=0)
        pale_blue_text = (
            area < 5000
            and avg.mean() > 150
            and avg[2] > avg[0] + 8
            and avg[2] > avg[1]
        )
        tiny_fragment = area < 1200 and bw < 180 and bh < 80
        if tiny_fragment or pale_blue_text:
            for y, x in comp:
                arr[y, x, 3] = 0
    return Image.fromarray(arr, "RGBA")


def place_baseline(source: Path, canvas: tuple[int, int], baseline_bottom: int) -> Image.Image:
    src = Image.open(source).convert("RGBA")
    bbox = src.getbbox()
    if bbox is None:
        return Image.new("RGBA", canvas, (0, 0, 0, 0))
    out = Image.new("RGBA", canvas, (0, 0, 0, 0))
    x = (canvas[0] - src.width) // 2
    y = baseline_bottom - bbox[3]
    out.alpha_composite(src, (x, y))
    return out


def make_contact_sheet(frames: list[Image.Image], out: Path) -> None:
    w, h = frames[0].size
    cols = 7
    label_h = 24
    rows = math.ceil(len(frames) / cols)
    sheet = Image.new("RGB", (cols * w, rows * (h + label_h)), (245, 245, 245))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, frame in enumerate(frames):
        x = (i % cols) * w
        y = (i // cols) * (h + label_h)
        draw.text((x + 6, y + 5), f"{i:02d}", fill=(20, 20, 20), font=font)
        bg = Image.new("RGBA", frame.size, (245, 245, 245, 255))
        bg.alpha_composite(frame)
        sheet.paste(bg.convert("RGB"), (x, y + label_h))
    sheet.save(out)


def make_spritesheet(frames: list[Image.Image], out: Path) -> None:
    w, h = frames[0].size
    sheet = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        sheet.alpha_composite(frame, (i * w, 0))
    sheet.save(out)


def make_preview(frames: list[Image.Image], out: Path) -> None:
    rgb_frames = []
    for frame in frames:
        bg = Image.new("RGBA", frame.size, (255, 255, 255, 255))
        bg.alpha_composite(frame)
        rgb_frames.append(np.array(bg.convert("RGB")))
    imageio.mimsave(out, rgb_frames, duration=0.075, loop=0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", default="sample/角色挥剑劈砍动作视频生成 (1).mp4")
    parser.add_argument("--source", default="sample/s7-standard.png")
    parser.add_argument("--output", default="output/s7-standard-attack-from-video")
    args = parser.parse_args()

    video = Path(args.video)
    source = Path(args.source)
    out_dir = Path(args.output)
    tmp_dir = Path("tmp") / "s7_attack_from_video_extract"
    full_dir = out_dir / "fullframe"
    key_dir = out_dir / "keyframe"

    if out_dir.exists():
        shutil.rmtree(out_dir)
    full_dir.mkdir(parents=True, exist_ok=True)
    key_dir.mkdir(parents=True, exist_ok=True)

    extracted = extract_frames(video, tmp_dir)
    if len(extracted) < 14:
        raise RuntimeError(f"expected at least 14 frames, got {len(extracted)}")

    baseline = Image.open(source).convert("RGBA")
    baseline_bbox = baseline.getbbox()
    if baseline_bbox is None:
        raise RuntimeError(f"empty source: {source}")

    canvas = baseline.size
    baseline_bottom = baseline_bbox[3]
    body_target = baseline_bbox[3] - baseline_bbox[1]

    # Skip the first static frame and sample through the full slash/recovery arc.
    sampled = [round(i) for i in np.linspace(12, len(extracted) - 1, 12, endpoint=False)]
    body_heights = [cut_video_frame(extracted[i])[1] for i in sampled[:12]]
    stable_body_height = float(np.median(body_heights))
    fixed_scale = body_target / stable_body_height
    frames: list[Image.Image] = [place_baseline(source, canvas, baseline_bottom)]
    frames.extend(clean_video_frame(extracted[i], canvas, fixed_scale, baseline_bottom) for i in sampled[:12])
    frames.append(frames[0].copy())

    prefix = "s7-standard-attack-video"
    for i, frame in enumerate(frames):
        frame.save(full_dir / f"{prefix}_{i:02d}.png")
    for i in [2, 5, 8, 11]:
        frames[i].save(key_dir / f"{prefix}_{i:02d}.png")

    make_spritesheet(frames, out_dir / "spritesheet.png")
    make_contact_sheet(frames, out_dir / "contact-sheet.png")
    make_preview(frames, out_dir / "preview.gif")

    (out_dir / "keyframe-prompts.md").write_text(
        "# Keyframe Notes\n\n"
        "Reference-driven sword slash extracted from `sample/角色挥剑劈砍动作视频生成 (1).mp4`.\n\n"
        "- 02: rising anticipation, sword lifts from guard.\n"
        "- 05: fast horizontal slash/contact with wide sword arc.\n"
        "- 08: contact hold/follow-through, cloak and torso overcommitted.\n"
        "- 11: recovery, sword rises and returns toward ready stance.\n\n"
        "Local processing removed the white video background and faint watermark text, "
        "kept the sword-arc effect, and centered frames on the source baseline canvas.\n",
        encoding="utf-8",
    )

    manifest = {
        "source": str(source).replace("\\", "/"),
        "referenceVideo": str(video).replace("\\", "/"),
        "output": str(out_dir).replace("\\", "/"),
        "motionType": "attack",
        "attackType": "sword slash",
        "frameCount": 14,
        "prefix": prefix,
        "canvas": list(canvas),
        "keyframeIndices": [2, 5, 8, 11],
        "anchorIndices": [0, 2, 5, 8, 11, 13],
        "segmentInsertions": [1, 2, 2, 2, 1],
        "previewBackground": "#FFFFFF",
        "coordinateSpace": "screen-space",
        "activeWeapon": "katana/sword",
        "weaponHand": "screen-left hand in the source baseline and video reference",
        "processing": [
            "fresh extraction from source video",
            "white background matting",
            "small watermark/component removal",
            "sword arc effect preserved",
            "one fixed video-to-baseline scale for all extracted frames",
            "transparent RGBA frame output",
            "source-based frame 00 copied to frame 13 for loop closure",
        ],
        "videoSampledFrameIndicesFor01To12": sampled[:12],
        "videoBodyHeightsForScale": body_heights,
        "fixedVideoScale": fixed_scale,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(out_dir)


if __name__ == "__main__":
    main()
