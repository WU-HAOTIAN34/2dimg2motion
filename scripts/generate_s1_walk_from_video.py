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


def alpha_bbox(alpha: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.nonzero(alpha > 0)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def largest_subject_mask(rgb: np.ndarray) -> np.ndarray:
    arr = rgb.astype(np.float32) / 255.0
    mx = arr.max(axis=2)
    mn = arr.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1e-6)

    # The watermark is white/gray and low saturation. Start from colorful body
    # pixels, then grow the mask to recover dark outlines around the subject.
    core = ((sat > 0.12) & (mx > 0.07)) | ((sat > 0.04) & (mx > 0.24))
    core = morph(core, "open", 1)
    core = morph(core, "dilate", 4)
    core = morph(core, "close", 3)
    mask = keep_largest_component(core)
    mask = morph(mask, "dilate", 1)
    mask = fill_holes_by_flood(mask)
    return mask


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


def keep_largest_component(mask: np.ndarray) -> np.ndarray:
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    best: list[tuple[int, int]] = []
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
            if len(comp) > len(best):
                best = comp
    out = np.zeros_like(mask, dtype=bool)
    for y, x in best:
        out[y, x] = True
    return out


def fill_holes_by_flood(mask: np.ndarray) -> np.ndarray:
    h, w = mask.shape
    outside = np.zeros_like(mask, dtype=bool)
    stack: list[tuple[int, int]] = []
    for x in range(w):
        if not mask[0, x]:
            stack.append((0, x))
        if not mask[h - 1, x]:
            stack.append((h - 1, x))
    for y in range(h):
        if not mask[y, 0]:
            stack.append((y, 0))
        if not mask[y, w - 1]:
            stack.append((y, w - 1))
    while stack:
        y, x = stack.pop()
        if outside[y, x] or mask[y, x]:
            continue
        outside[y, x] = True
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < h and 0 <= nx < w and not outside[ny, nx] and not mask[ny, nx]:
                stack.append((ny, nx))
    return mask | ~outside


def extract_video_frames(video: Path, tmp_dir: Path) -> list[Path]:
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    pattern = tmp_dir / "frame_%04d.png"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(video),
            "-an",
            "-vsync",
            "0",
            str(pattern),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return sorted(tmp_dir.glob("frame_*.png"))


def clean_video_frame(path: Path, canvas: tuple[int, int], subject_target: int) -> Image.Image:
    src = Image.open(path).convert("RGB")
    rgb = np.array(src)
    mask = largest_subject_mask(rgb)

    # Feather very slightly, preserving sprite-like edges without black halos.
    alpha = (mask.astype(np.uint8) * 255)
    bbox = alpha_bbox(alpha)
    if bbox is None:
        return Image.new("RGBA", canvas, (0, 0, 0, 0))

    rgba = np.dstack([rgb, alpha]).astype(np.uint8)
    cut = Image.fromarray(rgba, "RGBA").crop(bbox)

    cut_alpha = np.array(cut.getchannel("A"))
    cb = alpha_bbox(cut_alpha)
    if cb:
        cut = cut.crop(cb)

    scale = subject_target / max(cut.size)
    new_size = (max(1, round(cut.width * scale)), max(1, round(cut.height * scale)))
    cut = cut.resize(new_size, Image.Resampling.LANCZOS)

    out = Image.new("RGBA", canvas, (0, 0, 0, 0))
    x = (canvas[0] - cut.width) // 2
    bottom = int(canvas[1] * 0.82)
    y = bottom - cut.height
    out.alpha_composite(cut, (x, y))
    out = remove_watermark_residue(out)
    out = remove_tiny_alpha_fragments(out)
    return out


def remove_tiny_alpha_fragments(image: Image.Image) -> Image.Image:
    arr = np.array(image)
    alpha = arr[:, :, 3] > 0
    for comp in connected_components(alpha):
        if len(comp) < 500:
            for y, x in comp:
                arr[y, x, 3] = 0
    return Image.fromarray(arr, "RGBA")


def remove_watermark_residue(image: Image.Image) -> Image.Image:
    arr = np.array(image)
    rgb = arr[:, :, :3].astype(np.float32) / 255.0
    alpha = arr[:, :, 3] > 0
    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1e-6)
    h, w = alpha.shape
    yy, xx = np.mgrid[:h, :w]

    roi = (xx > int(w * 0.58)) & (yy > int(h * 0.58))
    candidate = alpha & roi & (sat < 0.12)
    labels = connected_components(candidate)
    for comp in labels:
        if len(comp) < 20:
            continue
        ys = [p[0] for p in comp]
        xs = [p[1] for p in comp]
        bw = max(xs) - min(xs) + 1
        bh = max(ys) - min(ys) + 1
        if 12 <= bw <= 80 and 6 <= bh <= 36:
            for y, x in comp:
                arr[y, x, 3] = 0
    return Image.fromarray(arr, "RGBA")


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


def place_source(source: Path, canvas: tuple[int, int], subject_target: int) -> Image.Image:
    src = Image.open(source).convert("RGBA")
    bbox = src.getbbox()
    if bbox is None:
        return Image.new("RGBA", canvas, (0, 0, 0, 0))
    out = Image.new("RGBA", canvas, (0, 0, 0, 0))
    x = (canvas[0] - src.width) // 2
    y = int(canvas[1] * 0.82) - bbox[3]
    out.alpha_composite(src, (x, y))
    return out


def make_contact_sheet(frames: list[Image.Image], out: Path) -> None:
    cell_w, cell_h = frames[0].size
    label_h = 24
    cols = 7
    rows = math.ceil(len(frames) / cols)
    sheet = Image.new("RGB", (cols * cell_w, rows * (cell_h + label_h)), (245, 245, 245))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for i, frame in enumerate(frames):
        x = (i % cols) * cell_w
        y = (i // cols) * (cell_h + label_h)
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
    preview = []
    for frame in frames:
        bg = Image.new("RGBA", frame.size, (255, 255, 255, 255))
        bg.alpha_composite(frame)
        preview.append(bg.convert("RGB"))
    imageio.mimsave(out, [np.array(frame) for frame in preview], duration=0.08, loop=0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", default="sample/784a63e6bfcc4a54baae80ee9e189ebd.mp4")
    parser.add_argument("--source", default="sample/s1.png")
    parser.add_argument("--output", default="output/s1-walk-from-video")
    args = parser.parse_args()

    video = Path(args.video)
    source = Path(args.source)
    out_dir = Path(args.output)
    full_dir = out_dir / "fullframe"
    key_dir = out_dir / "keyframe"
    tmp_dir = Path("tmp") / "s1_walk_from_video_extract"

    if out_dir.exists():
        shutil.rmtree(out_dir)
    full_dir.mkdir(parents=True, exist_ok=True)
    key_dir.mkdir(parents=True, exist_ok=True)

    extracted = extract_video_frames(video, tmp_dir)
    if len(extracted) < 14:
        raise RuntimeError(f"expected at least 14 frames, got {len(extracted)}")

    canvas = (384, 320)
    source_bbox = Image.open(source).convert("RGBA").getbbox()
    if source_bbox is None:
        raise RuntimeError(f"empty source image: {source}")
    subject_target = max(source_bbox[2] - source_bbox[0], source_bbox[3] - source_bbox[1])
    # Use video-derived motion for 01-12, while 00/13 are exact source-based loop anchors.
    sampled = [round(i) for i in np.linspace(4, len(extracted) - 1, 12, endpoint=False)]
    frames: list[Image.Image] = [place_source(source, canvas, subject_target)]
    frames.extend(clean_video_frame(extracted[i], canvas, subject_target) for i in sampled[:12])
    frames.append(frames[0].copy())

    prefix = "s1-walk-video"
    for i, frame in enumerate(frames):
        frame.save(full_dir / f"{prefix}_{i:02d}.png")
    for i in [2, 5, 8, 11]:
        frames[i].save(key_dir / f"{prefix}_{i:02d}.png")

    make_spritesheet(frames, out_dir / "spritesheet.png")
    make_contact_sheet(frames, out_dir / "contact-sheet.png")
    make_preview(frames, out_dir / "preview.gif")

    (out_dir / "keyframe-prompts.md").write_text(
        "# Keyframe Notes\n\n"
        "Reference-driven walk extraction from `sample/784a63e6bfcc4a54baae80ee9e189ebd.mp4`.\n\n"
        "- 02: contact/down pose from the reference walk.\n"
        "- 05: passing/up pose from the reference walk.\n"
        "- 08: opposite contact/down pose from the reference walk.\n"
        "- 11: recovery/up pose before returning to the source loop anchor.\n\n"
        "Local processing removed the black video background and low-saturation watermark text, "
        "then centered the subject on a transparent canvas.\n",
        encoding="utf-8",
    )

    manifest = {
        "source": str(source).replace("\\", "/"),
        "referenceVideo": str(video).replace("\\", "/"),
        "output": str(out_dir).replace("\\", "/"),
        "motionType": "walk",
        "frameCount": 14,
        "prefix": prefix,
        "canvas": list(canvas),
        "keyframeIndices": [2, 5, 8, 11],
        "anchorIndices": [0, 2, 5, 8, 11, 13],
        "segmentInsertions": [1, 2, 2, 2, 1],
        "previewBackground": "#FFFFFF",
        "processing": [
            "fresh extraction from source video",
            "color-saturation subject mask to reject watermark text",
            "mask dilation/fill to preserve dark sprite outlines",
            "transparent RGBA frame output",
            "source-based frame 00 copied to frame 13 for loop closure",
        ],
        "videoSampledFrameIndicesFor01To12": sampled[:12],
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    shutil.rmtree(tmp_dir, ignore_errors=True)
    print(out_dir)


if __name__ == "__main__":
    main()
