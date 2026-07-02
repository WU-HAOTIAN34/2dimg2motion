from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image, ImageColor


def parse_background(value: str) -> tuple[int, int, int]:
    try:
        rgb = ImageColor.getrgb(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid color: {value}") from exc
    if len(rgb) == 4:
        return rgb[:3]
    return rgb


def natural_key(path: Path) -> list[int | str]:
    parts = re.split(r"(\d+)", path.name)
    return [int(part) if part.isdigit() else part.lower() for part in parts]


def load_frames(fullframes_dir: Path, pattern: str) -> list[Path]:
    if not fullframes_dir.is_dir():
        raise FileNotFoundError(f"fullframe directory not found: {fullframes_dir}")
    frames = sorted(fullframes_dir.glob(pattern), key=natural_key)
    if not frames:
        raise FileNotFoundError(f"no frames matched {pattern!r} in {fullframes_dir}")
    return frames


def composite_frame(path: Path, background: tuple[int, int, int], canvas: tuple[int, int] | None) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    if canvas is not None and image.size != canvas:
        raise ValueError(f"{path.name}: canvas {image.size} differs from {canvas}")
    bg = Image.new("RGBA", image.size, (*background, 255))
    bg.alpha_composite(image)
    return bg.convert("RGB")


def write_gif(
    *,
    fullframes_dir: Path,
    output: Path,
    duration_ms: int,
    loop: int,
    background: tuple[int, int, int],
    pattern: str,
) -> int:
    if duration_ms <= 0:
        raise ValueError("--duration-ms must be greater than 0")

    frame_paths = load_frames(fullframes_dir, pattern)
    first = Image.open(frame_paths[0]).convert("RGBA")
    canvas = first.size
    frames = [composite_frame(path, background, canvas) for path in frame_paths]

    output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=loop,
        disposal=2,
    )
    return len(frames)


def default_output_for(fullframes_dir: Path) -> Path:
    parent = fullframes_dir.parent
    if fullframes_dir.name.lower() == "fullframe":
        return parent / "preview.gif"
    return fullframes_dir / "preview.gif"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compose transparent fullframe PNG sequence frames into a preview GIF.",
    )
    parser.add_argument("fullframes_dir", type=Path, help="Directory containing fullframe PNG files.")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output GIF path. Defaults to <artifact>/preview.gif when input is a fullframe directory.",
    )
    parser.add_argument(
        "--duration-ms",
        type=int,
        default=120,
        help="Frame duration in milliseconds. Default: 120.",
    )
    parser.add_argument(
        "--loop",
        type=int,
        default=0,
        help="GIF loop count. 0 means loop forever. Default: 0.",
    )
    parser.add_argument(
        "--background",
        type=parse_background,
        default=parse_background("#FFFFFF"),
        help="Background color used behind transparent PNG frames. Default: #FFFFFF.",
    )
    parser.add_argument(
        "--pattern",
        default="*.png",
        help="Glob pattern for frame files inside fullframes_dir. Default: *.png.",
    )
    args = parser.parse_args()

    output = args.output or default_output_for(args.fullframes_dir)
    count = write_gif(
        fullframes_dir=args.fullframes_dir,
        output=output,
        duration_ms=args.duration_ms,
        loop=args.loop,
        background=args.background,
        pattern=args.pattern,
    )
    print(f"Wrote {count} frames to {output}")


if __name__ == "__main__":
    main()
