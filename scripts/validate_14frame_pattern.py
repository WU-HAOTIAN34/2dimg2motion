from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageChops


FULL_INDICES = tuple(range(14))
KEY_INDICES = (2, 5, 8, 11)


def _load_rgba(path: Path, errors: list[str]) -> Image.Image | None:
    if not path.is_file():
        errors.append(f"missing file: {path}")
        return None
    image = Image.open(path)
    if image.mode != "RGBA":
        errors.append(f"{path.name}: expected RGBA, got {image.mode}")
        return None
    return image


def _pixel_equal(left: Image.Image, right: Image.Image) -> bool:
    return left.size == right.size and ImageChops.difference(left, right).getbbox() is None


def validate_pattern(
    *,
    baseline: str | Path,
    keyframes_dir: str | Path,
    fullframes_dir: str | Path,
    preview: str | Path,
    prefix: str,
) -> list[str]:
    baseline = Path(baseline)
    keyframes_dir = Path(keyframes_dir)
    fullframes_dir = Path(fullframes_dir)
    preview = Path(preview)
    errors: list[str] = []

    expected_full = [fullframes_dir / f"{prefix}_{index:02d}.png" for index in FULL_INDICES]
    expected_keys = [keyframes_dir / f"{prefix}_{index:02d}.png" for index in KEY_INDICES]
    actual_full = sorted(fullframes_dir.glob("*.png")) if fullframes_dir.is_dir() else []
    actual_keys = sorted(keyframes_dir.glob("*.png")) if keyframes_dir.is_dir() else []
    if actual_full != expected_full:
        errors.append("fullframe directory must contain exactly prefix_00.png through prefix_13.png")
    if actual_keys != expected_keys:
        errors.append("keyframe directory must contain exactly indices 02, 05, 08, and 11")

    source = _load_rgba(baseline, errors)
    full = [_load_rgba(path, errors) for path in expected_full]
    keys = [_load_rgba(path, errors) for path in expected_keys]
    if source is None or any(image is None for image in full) or any(image is None for image in keys):
        return errors

    full_images = [image for image in full if image is not None]
    key_images = [image for image in keys if image is not None]
    canvas = full_images[0].size
    baselines: list[int] = []
    for path, image in zip(expected_full, full_images):
        if image.size != canvas:
            errors.append(f"{path.name}: canvas {image.size} differs from {canvas}")
        corners = ((0, 0), (image.width - 1, 0), (0, image.height - 1), (image.width - 1, image.height - 1))
        if any(image.getpixel(point)[3] != 0 for point in corners):
            errors.append(f"{path.name}: corners must be transparent")
        bbox = image.getbbox()
        if bbox is None:
            errors.append(f"{path.name}: empty frame")
        else:
            baselines.append(bbox[3])
    if baselines and len(set(baselines)) != 1:
        errors.append(f"unstable foot baseline: {baselines}")

    if expected_full[0].read_bytes() != expected_full[13].read_bytes():
        errors.append("frames 00 and 13 must be byte-identical")

    source_bbox = source.getbbox()
    frame_bbox = full_images[0].getbbox()
    if source_bbox is None or frame_bbox is None:
        errors.append("baseline or frame 00 is empty")
    elif (source_bbox[2] - source_bbox[0], source_bbox[3] - source_bbox[1]) != (
        frame_bbox[2] - frame_bbox[0],
        frame_bbox[3] - frame_bbox[1],
    ):
        errors.append("frame 00 must preserve the baseline scale")
    else:
        translated = Image.new("RGBA", canvas, (0, 0, 0, 0))
        translated.alpha_composite(
            source,
            (frame_bbox[0] - source_bbox[0], frame_bbox[1] - source_bbox[1]),
        )
        if not _pixel_equal(translated, full_images[0]):
            errors.append("frame 00 must be an exact translated copy of the baseline")

    for index, key in zip(KEY_INDICES, key_images):
        if not _pixel_equal(key, full_images[index]):
            errors.append(f"keyframe {index:02d} must be pixel-identical to fullframe {index:02d}")

    if not preview.is_file():
        errors.append(f"missing file: {preview}")
    else:
        animation = Image.open(preview)
        if getattr(animation, "n_frames", 1) != 14:
            errors.append(f"{preview.name}: expected 14 GIF frames")
        for index in range(getattr(animation, "n_frames", 1)):
            animation.seek(index)
            frame = animation.convert("RGB")
            if frame.size != canvas:
                errors.append(f"{preview.name} frame {index:02d}: canvas {frame.size} differs from {canvas}")
                continue
            corners = ((0, 0), (frame.width - 1, 0), (0, frame.height - 1), (frame.width - 1, frame.height - 1))
            if any(frame.getpixel(point) != (255, 255, 255) for point in corners):
                errors.append(f"{preview.name} frame {index:02d}: preview background must be solid white #FFFFFF")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the fixed 14-frame 2dimg2motion pattern.")
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--keyframes-dir", required=True)
    parser.add_argument("--fullframes-dir", required=True)
    parser.add_argument("--preview", required=True)
    parser.add_argument("--prefix", required=True)
    args = parser.parse_args()
    errors = validate_pattern(
        baseline=args.baseline,
        keyframes_dir=args.keyframes_dir,
        fullframes_dir=args.fullframes_dir,
        preview=args.preview,
        prefix=args.prefix,
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("OK")


if __name__ == "__main__":
    main()
