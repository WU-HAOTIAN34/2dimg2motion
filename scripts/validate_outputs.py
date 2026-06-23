from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from PIL import Image


def validate_parts(parts_dir: str | Path):
    parts_dir = Path(parts_dir)
    errors = []
    manifest_path = parts_dir / "manifest.json"
    if not manifest_path.is_file():
        return [f"missing manifest: {manifest_path}"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    covered = 0
    for part in manifest.get("parts", []):
        path = parts_dir / part["file"]
        if not path.is_file():
            errors.append(f"missing part: {path.name}")
            continue
        image = Image.open(path)
        if image.mode != "RGBA":
            errors.append(f"{path.name}: expected RGBA, got {image.mode}")
        corners = ((0, 0), (image.width - 1, 0), (0, image.height - 1), (image.width - 1, image.height - 1))
        if image.mode == "RGBA" and any(image.getpixel(point)[3] != 0 for point in corners):
            errors.append(f"{path.name}: transparent padding is missing")
        covered += part.get("opaquePixels", 0)
    expected = manifest.get("sourceOpaquePixels")
    if expected is not None and covered != expected:
        errors.append(f"component coverage mismatch: {covered} != {expected}")
    return errors


def validate_frames(
    frames_dir: str | Path,
    *,
    width: int,
    height: int,
    prefix: str | None = None,
):
    frames_dir = Path(frames_dir)
    errors = []
    files = sorted(frames_dir.glob("*.png"))
    if not files:
        return [f"no PNG frames found in {frames_dir}"]
    indices = []
    for path in files:
        image = Image.open(path)
        if image.mode != "RGBA":
            errors.append(f"{path.name}: expected RGBA, got {image.mode}")
        if image.size != (width, height):
            errors.append(f"{path.name}: expected {width}x{height}, got {image.width}x{image.height}")
        if image.mode == "RGBA" and any(
            image.getpixel(point)[3] != 0
            for point in ((0, 0), (image.width - 1, 0), (0, image.height - 1), (image.width - 1, image.height - 1))
        ):
            errors.append(f"{path.name}: corners must be transparent")
        if prefix:
            match = re.fullmatch(re.escape(prefix) + r"_(\d+)\.png", path.name)
            if not match:
                errors.append(f"{path.name}: expected {prefix}_NN.png")
            else:
                indices.append(int(match.group(1)))
    if prefix and indices and indices != list(range(len(indices))):
        errors.append(f"frame sequence is not contiguous: {indices}")
    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate img2motion component and frame outputs.")
    parser.add_argument("--parts-dir")
    parser.add_argument("--frames-dir")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--prefix")
    args = parser.parse_args()
    if not args.parts_dir and not args.frames_dir:
        parser.error("provide --parts-dir or --frames-dir")
    errors = []
    if args.parts_dir:
        errors.extend(validate_parts(args.parts_dir))
    if args.frames_dir:
        if args.width is None or args.height is None:
            parser.error("--frames-dir requires --width and --height")
        errors.extend(validate_frames(args.frames_dir, width=args.width, height=args.height, prefix=args.prefix))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("OK")


if __name__ == "__main__":
    main()
