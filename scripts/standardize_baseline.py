from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from PIL import Image


def _is_near_white(pixel: tuple[int, int, int, int], threshold: int) -> bool:
    r, g, b, a = pixel
    return a > 0 and r >= threshold and g >= threshold and b >= threshold


def foreground_bbox(image: Image.Image, *, white_threshold: int) -> tuple[int, int, int, int] | None:
    rgba = image.convert("RGBA")
    alpha_bbox = rgba.getchannel("A").getbbox()
    if alpha_bbox is None:
        return None

    # Treat transparent pixels as background. If the image is fully opaque on a white
    # field, also trim near-white pixels so illustration PNGs export cleanly.
    pixels = rgba.load()
    width, height = rgba.size
    min_x, min_y = width, height
    max_x, max_y = -1, -1
    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            if pixel[3] == 0 or _is_near_white(pixel, white_threshold):
                continue
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
    if max_x < min_x or max_y < min_y:
        return alpha_bbox
    return (min_x, min_y, max_x + 1, max_y + 1)


def default_output_path(input_path: Path, sample_dir: Path) -> Path:
    return sample_dir / f"{input_path.stem}-standard.png"


def standardize(
    input_path: Path,
    output_path: Path,
    *,
    subject_max: int,
    margin_ratio: float,
    white_threshold: int,
) -> dict[str, object]:
    source = Image.open(input_path).convert("RGBA")
    bbox = foreground_bbox(source, white_threshold=white_threshold)
    if bbox is None:
        raise SystemExit(f"No foreground pixels found in {input_path}")

    subject = source.crop(bbox)
    src_w, src_h = subject.size
    longest = max(src_w, src_h)
    scale = subject_max / longest
    new_size = (max(1, round(src_w * scale)), max(1, round(src_h * scale)))
    resized = subject.resize(new_size, Image.Resampling.LANCZOS)

    margin = max(32, round(subject_max * margin_ratio))
    canvas_size = (new_size[0] + margin * 2, new_size[1] + margin * 2)
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    offset = ((canvas_size[0] - new_size[0]) // 2, (canvas_size[1] - new_size[1]) // 2)
    canvas.alpha_composite(resized, offset)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)

    margins = {
        "left": offset[0],
        "top": offset[1],
        "right": canvas_size[0] - offset[0] - new_size[0],
        "bottom": canvas_size[1] - offset[1] - new_size[1],
    }
    return {
        "input": str(input_path),
        "output": str(output_path),
        "sourceSize": list(source.size),
        "sourceSubjectBBox": list(bbox),
        "standardSubjectSize": list(new_size),
        "standardCanvasSize": list(canvas_size),
        "margins": margins,
        "subjectMax": subject_max,
        "marginRatio": margin_ratio,
        "scale": scale,
    }


def assess(report: dict[str, object]) -> list[str]:
    warnings: list[str] = []
    subject_w, subject_h = report["standardSubjectSize"]  # type: ignore[index]
    canvas_w, canvas_h = report["standardCanvasSize"]  # type: ignore[index]
    longest = max(subject_w, subject_h)
    if longest < 300 or longest > 400:
        warnings.append("standardized subject longest side is outside the 300-400 px target")
    margins = report["margins"]  # type: ignore[assignment]
    min_margin = min(margins.values())  # type: ignore[union-attr]
    if min_margin < 120:
        warnings.append("minimum transparent margin is under 120 px; wide attacks may need more space")
    if canvas_w > 900 or canvas_h > 900:
        warnings.append("standard canvas is still large; consider lowering --subject-max or --margin-ratio")
    return warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Standardize a 2dimg2motion baseline image: trim subject, resize to 300-400 px, add transparent action margins, and save under sample/."
    )
    parser.add_argument("input", help="Input image path, for example sample/s7.png")
    parser.add_argument("--output", help="Output path. Defaults to sample/<stem>-standard.png")
    parser.add_argument("--sample-dir", default="sample", help="Directory for default output path")
    parser.add_argument("--subject-max", type=int, default=360, help="Longest side of the visible subject after resizing")
    parser.add_argument("--margin-ratio", type=float, default=0.65, help="Transparent margin on each side, as a ratio of subject-max")
    parser.add_argument("--white-threshold", type=int, default=248, help="Opaque pixels at or above this RGB value are treated as white background")
    parser.add_argument("--check-only", action="store_true", help="Print the standardization report without writing the output")
    args = parser.parse_args()

    input_path = Path(args.input)
    sample_dir = Path(args.sample_dir)
    output_path = Path(args.output) if args.output else default_output_path(input_path, sample_dir)

    if args.subject_max < 300 or args.subject_max > 400:
        raise SystemExit("--subject-max must be between 300 and 400")
    if args.margin_ratio < 0.25:
        raise SystemExit("--margin-ratio must be at least 0.25")

    if args.check_only:
        temp_dir = Path(tempfile.mkdtemp(prefix="2dimg2motion-baseline-"))
        temp_output = temp_dir / output_path.name
        report = standardize(
            input_path,
            temp_output,
            subject_max=args.subject_max,
            margin_ratio=args.margin_ratio,
            white_threshold=args.white_threshold,
        )
        temp_output.unlink(missing_ok=True)
        temp_dir.rmdir()
    else:
        report = standardize(
            input_path,
            output_path,
            subject_max=args.subject_max,
            margin_ratio=args.margin_ratio,
            white_threshold=args.white_threshold,
        )

    warnings = assess(report)
    report["warnings"] = warnings
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
