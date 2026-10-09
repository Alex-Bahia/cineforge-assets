"""Step 6 — Generate thumbnail via Pollinations.ai (free) + text overlay with Pillow."""
import io
import logging
import sys
import urllib.parse
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import OUTPUT, ASSETS, VIDEO_WIDTH, VIDEO_HEIGHT

log = logging.getLogger(__name__)

THUMB_W, THUMB_H = 1280, 720   # YouTube recommended thumbnail size


NICHE_AI_PREFIXES = {
    "dark":          "cinematic dark mysterious",
    "sports":        "dynamic sports action energetic stadium",
    "kids":          "colorful bright cheerful cartoon friendly",
    "tech":          "sleek modern futuristic glowing screens",
    "finance":       "professional elegant wealth money success",
    "education":     "educational curiosity knowledge books discovery",
    "health":        "healthy vibrant natural wellness vitality",
    "entertainment": "exciting bold colorful entertainment show",
    "news":          "breaking news impactful documentary",
    "cooking":       "delicious food close-up warm appetizing",
}

NICHE_TEXT_COLORS = {
    "dark":          (220, 30, 30),     # red
    "sports":        (255, 165, 0),     # orange
    "kids":          (255, 80, 180),    # pink
    "tech":          (0, 180, 255),     # cyan
    "finance":       (40, 200, 100),    # green
    "education":     (60, 130, 220),    # blue
    "health":        (100, 210, 80),    # lime green
    "entertainment": (220, 80, 220),    # purple
    "news":          (220, 50, 50),     # red
    "cooking":       (255, 140, 0),     # orange
}

NICHE_OVERLAY_ALPHA = {
    "dark": 120, "sports": 80, "kids": 50, "tech": 90,
    "finance": 80, "education": 80, "health": 60,
    "entertainment": 80, "news": 100, "cooking": 60,
}


def _generate_ai_background(prompt: str, niche: str = "dark") -> Image.Image | None:
    """Fetch an AI-generated background from Pollinations.ai."""
    prefix = NICHE_AI_PREFIXES.get(niche, "cinematic")
    encoded = urllib.parse.quote(
        f"{prefix} {prompt}, dramatic lighting, 8k, ultra realistic, no text"
    )
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={THUMB_W}&height={THUMB_H}&nologo=true"
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception as e:
        log.warning("Pollinations thumbnail failed: %s", e)
        return None


NICHE_GRADIENT_COLORS = {
    "dark":          ((5, 0, 20),   (20, 5, 40)),
    "sports":        ((10, 20, 5),  (30, 60, 10)),
    "kids":          ((30, 10, 50), (80, 30, 120)),
    "tech":          ((5, 10, 25),  (10, 25, 60)),
    "finance":       ((5, 15, 5),   (10, 40, 15)),
    "education":     ((10, 15, 25), (20, 35, 70)),
    "health":        ((5, 20, 5),   (10, 50, 20)),
    "entertainment": ((20, 5, 25),  (50, 10, 60)),
    "news":          ((15, 5, 5),   (40, 10, 10)),
    "cooking":       ((25, 15, 5),  (60, 35, 5)),
}


def _gradient_bg(niche: str = "dark") -> Image.Image:
    """Fallback: niche-appropriate gradient background."""
    c1, c2 = NICHE_GRADIENT_COLORS.get(niche, NICHE_GRADIENT_COLORS["dark"])
    img = Image.new("RGB", (THUMB_W, THUMB_H))
    draw = ImageDraw.Draw(img)
    for y in range(THUMB_H):
        t = y / THUMB_H
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        draw.line([(0, y), (THUMB_W, y)], fill=(r, g, b))
    return img


def _dark_gradient_bg() -> Image.Image:
    return _gradient_bg("dark")


def _add_dark_overlay(img: Image.Image, alpha: int = 120) -> Image.Image:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, alpha))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    return img.convert("RGB")


def _load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_file = ASSETS / "fonts" / ("Anton.ttf" if bold else "Roboto-Regular.ttf")
    if font_file.exists():
        try:
            return ImageFont.truetype(str(font_file), size)
        except Exception:
            pass
    # Pillow built-in fallback
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def _draw_text_with_shadow(draw: ImageDraw.ImageDraw, text: str, position: tuple,
                            font: ImageFont.FreeTypeFont,
                            fill: tuple = (255, 255, 255),
                            shadow_offset: int = 4,
                            shadow_fill: tuple = (0, 0, 0, 200)) -> None:
    sx, sy = position[0] + shadow_offset, position[1] + shadow_offset
    draw.text((sx, sy), text, font=font, fill=shadow_fill[:3])
    draw.text(position, text, font=font, fill=fill)


def generate_thumbnail(
    script: dict,
    video_id: str,
    use_ai_bg: bool = True,
    niche: str = "dark",
) -> Path:
    """
    Generate a YouTube thumbnail for the video.
    Supports any niche with appropriate color scheme and background style.
    Returns path to saved JPEG.
    """
    thumb_text = script.get("thumbnail_text", script["titulo"][:40].upper())
    title      = script["titulo"]

    # Background
    bg = None
    if use_ai_bg:
        prompt = script["cenas"][0].get("prompt_visual", niche) if script.get("cenas") else niche
        bg = _generate_ai_background(prompt, niche=niche)

    if bg is None:
        bg = _gradient_bg(niche)

    bg = bg.resize((THUMB_W, THUMB_H), Image.LANCZOS)
    bg = bg.filter(ImageFilter.SHARPEN)
    overlay_alpha = NICHE_OVERLAY_ALPHA.get(niche, 100)
    bg = _add_dark_overlay(bg, alpha=overlay_alpha)

    draw = ImageDraw.Draw(bg)

    # Main headline (large, centered)
    headline_font = _load_font(90, bold=True)
    # Word-wrap manually
    words = thumb_text.split()
    lines = []
    line  = ""
    for w in words:
        test = (line + " " + w).strip()
        bbox = draw.textbbox((0, 0), test, font=headline_font)
        if bbox[2] > THUMB_W - 80:
            if line:
                lines.append(line)
            line = w
        else:
            line = test
    if line:
        lines.append(line)

    total_h = len(lines) * (headline_font.size + 10)
    y = (THUMB_H - total_h) // 2 - 40

    accent_color = NICHE_TEXT_COLORS.get(niche, (220, 30, 30))

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=headline_font)
        x = (THUMB_W - (bbox[2] - bbox[0])) // 2
        # Niche-colored stroke for visual identity
        draw.text((x - 2, y - 2), line, font=headline_font, fill=accent_color)
        draw.text((x + 2, y + 2), line, font=headline_font, fill=accent_color)
        draw.text((x, y), line, font=headline_font, fill=(255, 255, 255))
        y += headline_font.size + 10

    # Channel watermark bottom-left
    small_font = _load_font(28, bold=False)
    draw.text((30, THUMB_H - 50), "▶  WATCH UNTIL THE END", font=small_font, fill=(200, 200, 200))

    # Save
    out_dir = OUTPUT / "thumbnails"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{video_id}.jpg"
    bg.save(str(out_path), "JPEG", quality=95)
    log.info("Thumbnail saved: %s", out_path)
    return out_path


if __name__ == "__main__":
    import argparse, json

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    p = argparse.ArgumentParser(description="Generate thumbnail for a script")
    p.add_argument("script_json")
    p.add_argument("--video-id", default="test_video")
    p.add_argument("--no-ai", action="store_true")
    args = p.parse_args()

    script = json.loads(Path(args.script_json).read_text())
    path = generate_thumbnail(script, args.video_id, use_ai_bg=not args.no_ai)
    print(f"\n✅ Thumbnail: {path}")
