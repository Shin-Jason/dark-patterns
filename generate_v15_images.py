"""
Generate v15 image sets by inserting a product description paragraph into v14/v12 images.

Each source image is split at the top of the blue "Add to Cart" button.
A description block is inserted, then the button is reattached.

Products:
  v14-vitamin  → v15-vitamin  (vague wellness copy; removes "no ingredient info" objection)
  v14-serum    → v15-serum    (vague skincare copy; same fix)
  v12-filter   → v15-filter   (explicit ISO 12312-2 / OD 5.0 safety copy; removes
                                "no safety certification" objection that suppressed baselines)
"""

import os
import textwrap
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/System/Library/Fonts/SFNS.ttf"

VITAMIN_DESC = (
    "Supports immune health, energy levels, and overall cellular function with a "
    "comprehensive blend of essential vitamins and minerals. Formulated for maximum "
    "daily wellness using high-quality, bioavailable ingredients. Manufactured in a "
    "GMP-certified facility."
)

SERUM_DESC = (
    "A lightweight, fast-absorbing formula that deeply hydrates and helps visibly "
    "improve skin texture and elasticity. Supports a healthy, radiant-looking "
    "complexion with a nourishing blend of botanical extracts and skin-conditioning "
    "agents. Suitable for all skin types."
)

# Directly addresses the three objections flagged in v12 CoT reasoning:
# ISO 12312-2 certification, optical density rating, and material/safety spec.
FILTER_DESC = (
    "ISO 12312-2 certified for safe direct solar observation. Features optical density "
    "OD 5.0 AstroSolar film that blocks 99.999% of sunlight, providing full protection "
    "against UV, infrared, and visible light. Adjustable aluminum housing fits telescope "
    "tubes with 70–92mm outer diameter. Meets international safety standards for "
    "unfiltered solar viewing through telescopes and binoculars."
)

CONFIGS = [
    {
        "src_dir": "v14-vitamin",
        "dst_dir": "v15-vitamin",
        "description": VITAMIN_DESC,
    },
    {
        "src_dir": "v14-serum",
        "dst_dir": "v15-serum",
        "description": SERUM_DESC,
    },
    {
        "src_dir": "v12-filter",
        "dst_dir": "v15-filter",
        "description": FILTER_DESC,
    },
]

PADDING_X = 32    # left/right margin for description text
FONT_SIZE = 15    # body text size (pt ≈ px at screen res)
LINE_SPACING = 6  # extra px between lines
TEXT_COLOR = (85, 85, 85)     # #555555 — muted gray
BG_COLOR = (255, 255, 255, 255)
GAP_ABOVE = 16   # px between price and description
GAP_BELOW = 16   # px between description and button


def find_button_top(arr: np.ndarray) -> int:
    """Return the y-coordinate of the first row that is >30% blue button pixels."""
    h, w = arr.shape[:2]
    for y in range(h):
        row = arr[y]
        blue = ((row[:, 2] > 150) & (row[:, 0] < 150) & (row[:, 1] < 150)).sum()
        if blue > w * 0.3:
            return y
    raise ValueError("Could not locate blue button in image")


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Word-wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current = ""
    dummy = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(dummy)
    for word in words:
        candidate = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def insert_description(src_path: Path, dst_path: Path, description: str) -> None:
    img = Image.open(src_path).convert("RGBA")
    arr = np.array(img)
    w = img.width

    button_top = find_button_top(arr)

    top_crop = img.crop((0, 0, w, button_top))
    button_crop = img.crop((0, button_top, w, img.height))

    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    max_text_width = w - 2 * PADDING_X
    lines = wrap_text(description, font, max_text_width)

    # Measure line height
    dummy = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(dummy)
    sample_bbox = draw.textbbox((0, 0), "Ag", font=font)
    line_h = sample_bbox[3] - sample_bbox[1]

    block_height = len(lines) * line_h + (len(lines) - 1) * LINE_SPACING
    insert_height = GAP_ABOVE + block_height + GAP_BELOW

    new_h = top_crop.height + insert_height + button_crop.height
    new_img = Image.new("RGBA", (w, new_h), BG_COLOR)

    new_img.paste(top_crop, (0, 0))

    draw = ImageDraw.Draw(new_img)
    text_y = top_crop.height + GAP_ABOVE
    for line in lines:
        draw.text((PADDING_X, text_y), line, font=font, fill=TEXT_COLOR)
        text_y += line_h + LINE_SPACING

    new_img.paste(button_crop, (0, top_crop.height + insert_height))

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    new_img.convert("RGB").save(dst_path, "PNG")
    print(f"  Saved: {dst_path.name}  ({w}x{new_h})")


def main():
    base = Path(__file__).parent
    for cfg in CONFIGS:
        src_dir = base / cfg["src_dir"]
        dst_dir = base / cfg["dst_dir"]
        dst_dir.mkdir(exist_ok=True)
        print(f"\n{cfg['src_dir']} → {cfg['dst_dir']}")
        for png in sorted(src_dir.glob("*.png")):
            insert_description(png, dst_dir / png.name, cfg["description"])


if __name__ == "__main__":
    main()
