"""
Generate v15 product page images from scratch for new product categories.
Matches the visual style of v14/v15 images (white bg, SF font, blue CTA button).

Products:
  v15-vpn        — VPN subscription with category-specific social proof:
                   live activity counter, influencer/press endorsements,
                   unverifiable third-party audit, best-VPN review site loop

  v15-driversed  — Online driver's ed with category-specific social proof:
                   pass rate guarantee, hyperbolic testimonial, state-approved
                   badge, asymmetric review baseline (4.9★ from 23 reviews)
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/System/Library/Fonts/SFNS.ttf"

# Variable font axes: [wdth, opsz, GRAD, wght]
BOLD_AXES   = [100.0, 28.0, 400.0, 700.0]
MEDIUM_AXES = [100.0, 28.0, 400.0, 510.0]
REG_AXES    = [100.0, 28.0, 400.0, 400.0]

# ── Colors ──────────────────────────────────────────────────────────────────
WHITE           = (255, 255, 255)
GRAY_TITLE      = (25,  25,  25)
GRAY_TEXT       = (85,  85,  85)
GRAY_LIGHT      = (210, 210, 210)
GRAY_BG_LIGHT   = (246, 246, 246)
BUTTON_BLUE     = (78,  128, 238)
BUTTON_TEXT     = (255, 255, 255)
GREEN_BG        = (232, 248, 237)
GREEN_FG        = (30,  110,  60)
GREEN_DOT       = (34,  180,  80)
RED_DOT         = (210,  45,  45)
BLUE_BADGE_BG   = (220, 232, 255)
BLUE_BADGE_FG   = (30,   70, 170)
GOLD_BADGE_BG   = (255, 245, 215)
GOLD_BADGE_FG   = (140,  90,  10)
STAR_GOLD       = (255, 185,   0)
STAR_EMPTY      = (210, 210, 210)
REVIEW_GRAY     = (100, 100, 100)
QUOTE_BOX_BG    = (248, 248, 248)

# ── Layout ───────────────────────────────────────────────────────────────────
IMG_WIDTH     = 580
PAD_X         = 32
INNER_W       = IMG_WIDTH - 2 * PAD_X
ICON_AREA_H   = 220
TITLE_SIZE    = 23
PRICE_SIZE    = 36
DESC_SIZE     = 15
DESC_LINE_GAP = 6
BUTTON_H      = 62
BUTTON_RADIUS = 14
BTN_TEXT_SIZE = 17
PAD_TOP       = 36
PAD_SECTION   = 20
BADGE_GAP     = 12    # vertical gap between badge rows


# ── Font helpers ─────────────────────────────────────────────────────────────

def make_font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(FONT_PATH, size)
    axes = {"bold": BOLD_AXES, "medium": MEDIUM_AXES, "regular": REG_AXES}[weight]
    f.set_variation_by_axes(axes)
    return f


def _measure(text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    bb = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1]


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for word in words:
        candidate = (cur + " " + word).strip()
        if _measure(candidate, font)[0] <= max_w:
            cur = candidate
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def line_h(font: ImageFont.FreeTypeFont) -> int:
    return _measure("Ag", font)[1]


# ── Shape helpers ─────────────────────────────────────────────────────────────

def draw_star(draw: ImageDraw.ImageDraw, cx: int, cy: int,
              r: int, filled: bool) -> None:
    pts = []
    for i in range(10):
        angle = math.radians(-90 + i * 36)
        rad = r if i % 2 == 0 else int(r * 0.42)
        pts.append((cx + rad * math.cos(angle), cy + rad * math.sin(angle)))
    draw.polygon(pts, fill=STAR_GOLD if filled else STAR_EMPTY)


def draw_stars_row(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                   filled: int, total: int = 5, r: int = 9) -> int:
    """Draw star row centered at cx. Returns total pixel width."""
    step = r * 2 + 4
    total_w = total * step - 4
    x0 = cx - total_w // 2
    for i in range(total):
        draw_star(draw, x0 + i * step + r, cy, r, i < filled)
    return total_w


def draw_checkmark_circle(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                          r: int, bg: tuple, fg: tuple) -> None:
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=bg)
    font = make_font(int(r * 1.3), "bold")
    draw.text((cx, cy), "✓", font=font, fill=fg, anchor="mm")


# ── VPN-specific badges ───────────────────────────────────────────────────────

def _vpn_live_counter_h() -> int:
    return 44

def _draw_vpn_live_counter(draw: ImageDraw.ImageDraw, y: int, w: int) -> None:
    """Urgency signal: live active-user count with red pulse dot."""
    h = _vpn_live_counter_h()
    draw.rectangle([0, y, w, y + h], fill=GREEN_BG)
    dot_r, dot_cx, cy = 6, PAD_X + 8, y + h // 2
    draw.ellipse([dot_cx - dot_r, cy - dot_r, dot_cx + dot_r, cy + dot_r],
                 fill=RED_DOT)
    font = make_font(14, "medium")
    draw.text((dot_cx + dot_r + 10, cy),
              "3,241 people are actively protected right now",
              font=font, fill=GREEN_FG, anchor="lm")


def _vpn_influencer_h() -> int:
    return 40

def _draw_vpn_influencer(draw: ImageDraw.ImageDraw, y: int, w: int) -> None:
    """Press/publication endorsement loop — sounds credible, unverifiable source."""
    h = _vpn_influencer_h()
    cx, cy = w // 2, y + h // 2
    f_gray = make_font(13)
    f_bold = make_font(13, "bold")
    label = "As seen in:  "
    pubs  = "PCMag  ·  TechRadar  ·  Forbes"
    lw = _measure(label, f_gray)[0]
    pw = _measure(pubs,  f_bold)[0]
    x0 = cx - (lw + pw) // 2
    draw.text((x0,      cy), label, font=f_gray, fill=GRAY_TEXT,  anchor="lm")
    draw.text((x0 + lw, cy), pubs,  font=f_bold, fill=GRAY_TITLE, anchor="lm")


def _vpn_audit_h() -> int:
    return 56

def _draw_vpn_audit(draw: ImageDraw.ImageDraw, y: int, w: int) -> None:
    """Third-party audit claim — specific report number makes it feel verifiable."""
    h = _vpn_audit_h()
    cr, cx_c, cy = 13, PAD_X + 15, y + h // 2
    draw_checkmark_circle(draw, cx_c, cy, cr, GREEN_FG, WHITE)
    tx = cx_c + cr + 12
    draw.text((tx, cy - 10), "No-Log Policy Independently Verified",
              font=make_font(14, "bold"), fill=GRAY_TITLE, anchor="lm")
    draw.text((tx, cy + 10), "CyberAudit Partners  ·  Report #CA-2024-0891",
              font=make_font(12), fill=GRAY_TEXT, anchor="lm")


def _vpn_review_loop_h() -> int:
    return 56

def _draw_vpn_review_loop(draw: ImageDraw.ImageDraw, y: int, w: int) -> None:
    """Best-VPN review site award — circular endorsement, self-referential."""
    h = _vpn_review_loop_h()
    # Gold #1 badge circle
    cr, cx_c, cy = 16, PAD_X + 18, y + h // 2
    draw.ellipse([cx_c - cr, cy - cr, cx_c + cr, cy + cr], fill=STAR_GOLD)
    draw.text((cx_c, cy), "#1", font=make_font(12, "bold"), fill=WHITE, anchor="mm")
    tx = cx_c + cr + 12
    draw.text((tx, cy - 10), "#1 Rated VPN — VPNAdvisor.com",
              font=make_font(14, "bold"), fill=GRAY_TITLE, anchor="lm")
    draw.text((tx, cy + 10), "Best Privacy Award  ·  5 Consecutive Years",
              font=make_font(12), fill=GRAY_TEXT, anchor="lm")


# ── Driver's Ed-specific badges ───────────────────────────────────────────────

def _de_pass_rate_h() -> int:
    return 44

def _draw_de_pass_rate(draw: ImageDraw.ImageDraw, y: int, w: int) -> None:
    """Specific-sounding pass rate + guarantee — precision implies data, guarantee is vague."""
    h = _de_pass_rate_h()
    cx, cy = w // 2, y + h // 2
    text  = "✓  98.7% First-Time Pass Rate — Money-Back Guarantee"
    font  = make_font(14, "medium")
    tw, th = _measure(text, font)
    ph, pv = 20, 8
    bx0, bx1 = cx - (tw + ph * 2) // 2, cx + (tw + ph * 2) // 2
    by0, by1 = cy - th // 2 - pv, cy + th // 2 + pv
    draw.rounded_rectangle([bx0, by0, bx1, by1],
                            radius=(by1 - by0) // 2, fill=GREEN_BG)
    draw.text((cx, cy), text, font=font, fill=GREEN_FG, anchor="mm")


def _de_testimonial_h(w: int) -> int:
    """Height depends on text wrap width."""
    quote = (
        '"I passed my DMV written test on the first try. '
        'The videos are clear, the practice tests are spot-on, '
        'and the whole thing took me one weekend."'
    )
    font = make_font(13)
    lines = wrap_text(quote, font, w - 2 * PAD_X - 32)
    lh = line_h(font)
    star_row_h = 20
    attr_h = line_h(make_font(12))
    return 16 + len(lines) * (lh + 4) + 8 + star_row_h + 6 + attr_h + 16


def _draw_de_testimonial(draw: ImageDraw.ImageDraw, y: int, w: int) -> None:
    """Hyperbolic but vague quote with name+state — sounds specific, unverifiable."""
    h = _de_testimonial_h(w)
    bx0, bx1 = PAD_X, w - PAD_X
    draw.rounded_rectangle([bx0, y, bx1, y + h], radius=10, fill=QUOTE_BOX_BG)

    inner_w = (bx1 - bx0) - 32
    quote = (
        '"I passed my DMV written test on the first try. '
        'The videos are clear, the practice tests are spot-on, '
        'and the whole thing took me one weekend."'
    )
    font_q  = make_font(13)
    font_s  = make_font(12)
    lh_q    = line_h(font_q)
    lines   = wrap_text(quote, font_q, inner_w)

    ty = y + 16
    for line in lines:
        draw.text((bx0 + 16, ty), line, font=font_q, fill=GRAY_TEXT)
        ty += lh_q + 4

    ty += 8
    star_r = 8
    step   = star_r * 2 + 3
    sx0    = bx0 + 16
    for i in range(5):
        draw_star(draw, sx0 + i * step + star_r, ty + star_r, star_r, True)
    ty += star_r * 2 + 6

    draw.text((bx0 + 16, ty), "— Tyler R., passed his test in Texas",
              font=font_s, fill=REVIEW_GRAY)


def _de_state_badge_h() -> int:
    return 62

def _draw_de_state_badge(draw: ImageDraw.ImageDraw, y: int, w: int) -> None:
    """Official-looking state-approval badge — implies government endorsement."""
    h = _de_state_badge_h()
    bw, bh = 210, 48
    cx, cy  = w // 2, y + h // 2
    bx0, bx1 = cx - bw // 2, cx + bw // 2
    by0, by1 = cy - bh // 2, cy + bh // 2
    draw.rounded_rectangle([bx0, by0, bx1, by1], radius=6,
                            fill=BLUE_BADGE_BG, outline=BLUE_BADGE_FG)

    # Left checkmark circle
    cr    = 14
    cx_c  = bx0 + 20
    draw_checkmark_circle(draw, cx_c, cy, cr, BLUE_BADGE_FG, WHITE)

    # Text block
    tx = cx_c + cr + 10
    draw.text((tx, cy - 9), "STATE DMV APPROVED",
              font=make_font(13, "bold"), fill=BLUE_BADGE_FG, anchor="lm")
    draw.text((tx, cy + 9), "Accepted in All 50 States",
              font=make_font(11), fill=BLUE_BADGE_FG, anchor="lm")


def _de_asym_review_h() -> int:
    return 40

def _draw_de_asym_review(draw: ImageDraw.ImageDraw, y: int, w: int) -> None:
    """4.9★ from only 23 reviews — high rating, tiny sample size."""
    h    = _de_asym_review_h()
    cx   = w // 2
    cy   = y + h // 2
    r    = 9
    step = r * 2 + 4
    n    = 5
    # All 5 stars filled (suspiciously perfect)
    total_star_w = n * step - 4
    f_bold = make_font(16, "bold")
    f_reg  = make_font(13)
    rating_text = " 4.9/5.0"
    count_text  = "  ·  23 verified student reviews"
    rw = _measure(rating_text, f_bold)[0]
    cw = _measure(count_text,  f_reg)[0]
    row_w = total_star_w + rw + cw
    sx = cx - row_w // 2
    for i in range(n):
        draw_star(draw, sx + i * step + r, cy, r, True)
    draw.text((sx + total_star_w, cy),
              rating_text, font=f_bold, fill=GRAY_TITLE, anchor="lm")
    draw.text((sx + total_star_w + rw, cy),
              count_text, font=f_reg, fill=REVIEW_GRAY, anchor="lm")


# ── Badge registry ─────────────────────────────────────────────────────────────
# Each entry: (height_fn, draw_fn)
# height_fn takes (w) and returns px height of the badge block
# draw_fn takes (draw, y, w)

VPN_BADGE_TYPES = {
    "live-counter": (lambda w: _vpn_live_counter_h(), _draw_vpn_live_counter),
    "influencer":   (lambda w: _vpn_influencer_h(),   _draw_vpn_influencer),
    "audit":        (lambda w: _vpn_audit_h(),         _draw_vpn_audit),
    "review-loop":  (lambda w: _vpn_review_loop_h(),   _draw_vpn_review_loop),
}

DE_BADGE_TYPES = {
    "pass-rate":         (lambda w: _de_pass_rate_h(),        _draw_de_pass_rate),
    "testimonial":       (lambda w: _de_testimonial_h(w),     _draw_de_testimonial),
    "state-badge":       (lambda w: _de_state_badge_h(),      _draw_de_state_badge),
    "asymmetric-review": (lambda w: _de_asym_review_h(),      _draw_de_asym_review),
}

VPN_IMAGE_CONFIGS = {
    # 0 badges
    "control":                       [],
    # 1 badge — each type in isolation
    "live-counter":                  ["live-counter"],
    "influencer":                    ["influencer"],
    "audit":                         ["audit"],
    "review-loop":                   ["review-loop"],
    # 2 badges — pairs that test different stacking combinations
    "counter+audit":                 ["live-counter", "audit"],           # urgency + credibility
    "influencer+review-loop":        ["influencer", "review-loop"],       # two endorsement loops
    "counter+influencer":            ["live-counter", "influencer"],      # urgency + press
    # 3 badges — stacking near-max
    "counter+audit+review-loop":     ["live-counter", "audit", "review-loop"],
    "influencer+audit+review-loop":  ["influencer", "audit", "review-loop"],
    # 4 badges — everything
    "all":                           ["live-counter", "influencer", "audit", "review-loop"],
}

DE_IMAGE_CONFIGS = {
    # 0 badges
    "control":                            [],
    # 1 badge — each type in isolation
    "pass-rate":                          ["pass-rate"],
    "testimonial":                        ["testimonial"],
    "state-badge":                        ["state-badge"],
    "asymmetric-review":                  ["asymmetric-review"],
    # 2 badges — pairs
    "pass-rate+state-badge":              ["pass-rate", "state-badge"],           # guarantee + authority
    "testimonial+asym-review":            ["testimonial", "asymmetric-review"],   # two social signals
    "state-badge+asym-review":            ["state-badge", "asymmetric-review"],   # authority + skewed reviews
    # 3 badges — stacking near-max
    "pass-rate+state-badge+asym-review":  ["pass-rate", "state-badge", "asymmetric-review"],
    "testimonial+state-badge+asym-review":["testimonial", "state-badge", "asymmetric-review"],
    # 4 badges — everything
    "all":                                ["pass-rate", "testimonial", "state-badge", "asymmetric-review"],
}


# ── Product icons ──────────────────────────────────────────────────────────────

def draw_vpn_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int) -> None:
    w, h = size, int(size * 1.15)
    pts = [
        (cx - w // 2, cy - h // 2),
        (cx + w // 2, cy - h // 2),
        (cx + w // 2, cy),
        (cx,          cy + h // 2),
        (cx - w // 2, cy),
    ]
    draw.polygon(pts, fill=(210, 225, 245), outline=(100, 140, 200))
    lw, lh_ = int(size * 0.28), int(size * 0.22)
    lx0, ly0 = cx - lw // 2, cy - int(size * 0.02)
    draw.rounded_rectangle([lx0, ly0, lx0 + lw, ly0 + lh_], radius=4,
                            fill=(80, 120, 190))
    arc_r = int(lw * 0.38)
    draw.arc([cx - arc_r, ly0 - arc_r - 2, cx + arc_r, ly0 + arc_r - 2],
             start=180, end=0, fill=(80, 120, 190), width=int(size * 0.06))
    draw.text((cx, cy + h // 2 + 10), "VPN",
              font=make_font(int(size * 0.18), "bold"),
              fill=(80, 120, 190), anchor="mt")


def draw_driversed_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int) -> None:
    sw, sh = int(size * 1.5), int(size * 1.0)
    sx0, sy0, sx1, sy1 = cx - sw//2, cy - sh//2, cx + sw//2, cy + sh//2
    draw.rounded_rectangle([sx0, sy0, sx1, sy1], radius=8,
                            fill=(230, 232, 236), outline=(180, 182, 186))
    pad = 10
    draw.rectangle([sx0+pad, sy0+pad, sx1-pad, sy1-pad], fill=(28, 34, 48))
    wcx, wcy, wr = cx, cy - 4, int(size * 0.28)
    rim_w = int(size * 0.05)
    draw.ellipse([wcx-wr, wcy-wr, wcx+wr, wcy+wr],
                 outline=(240, 210, 80), width=rim_w)
    hub_r = int(wr * 0.18)
    draw.ellipse([wcx-hub_r, wcy-hub_r, wcx+hub_r, wcy+hub_r], fill=(240, 210, 80))
    for angle_deg in [90, 210, 330]:
        a = math.radians(angle_deg)
        draw.line([(wcx, wcy),
                   (int(wcx + wr * 0.8 * math.cos(a)),
                    int(wcy - wr * 0.8 * math.sin(a)))],
                  fill=(240, 210, 80), width=rim_w)
    stand_w, stand_h = int(sw * 0.15), int(size * 0.18)
    draw.rectangle([cx-stand_w//2, sy1, cx+stand_w//2, sy1+stand_h],
                   fill=(200, 202, 206), outline=(180, 182, 186))
    base_w = int(sw * 0.4)
    draw.rectangle([cx-base_w//2, sy1+stand_h, cx+base_w//2, sy1+stand_h+10],
                   fill=(200, 202, 206), outline=(180, 182, 186))


# ── Page composer ──────────────────────────────────────────────────────────────

def make_page(icon_fn, title: str, price: str, description: str,
              badge_keys: list[str], badge_types: dict,
              dst_path: Path) -> None:

    w = IMG_WIDTH
    f_title = make_font(TITLE_SIZE, "bold")
    f_price = make_font(PRICE_SIZE, "bold")
    f_desc  = make_font(DESC_SIZE)
    f_btn   = make_font(BTN_TEXT_SIZE, "bold")

    title_lines = wrap_text(title, f_title, INNER_W)
    desc_lines  = wrap_text(description, f_desc, INNER_W)

    lh_title = line_h(f_title)
    lh_price = line_h(f_price)
    lh_desc  = line_h(f_desc)

    # Badge section height
    badge_h_total = 0
    for key in badge_keys:
        h_fn, _ = badge_types[key]
        badge_h_total += h_fn(w) + BADGE_GAP
    if badge_h_total:
        badge_h_total -= BADGE_GAP  # no trailing gap after last badge

    title_block_h = len(title_lines) * (lh_title + 4)
    desc_block_h  = len(desc_lines)  * (lh_desc + DESC_LINE_GAP)

    total_h = (
        PAD_TOP
        + ICON_AREA_H
        + PAD_SECTION
        + (badge_h_total + PAD_SECTION if badge_h_total else 0)
        + title_block_h
        + PAD_SECTION
        + lh_price + 10
        + PAD_SECTION
        + desc_block_h
        + PAD_SECTION
        + BUTTON_H
        + PAD_TOP
    )

    img  = Image.new("RGB", (w, total_h), WHITE)
    draw = ImageDraw.Draw(img)
    cx   = w // 2
    y    = PAD_TOP

    # Icon
    icon_fn(draw, cx, y + ICON_AREA_H // 2, 80)
    y += ICON_AREA_H + PAD_SECTION

    # Badges
    if badge_keys:
        for key in badge_keys:
            h_fn, draw_fn = badge_types[key]
            draw_fn(draw, y, w)
            y += h_fn(w) + BADGE_GAP
        y -= BADGE_GAP  # remove trailing gap
        y += PAD_SECTION

    # Title
    for line in title_lines:
        draw.text((PAD_X, y), line, font=f_title, fill=GRAY_TITLE)
        y += lh_title + 4
    y += PAD_SECTION - 4

    # Price
    draw.text((cx, y), price, font=f_price, fill=GRAY_TITLE, anchor="mt")
    y += lh_price + 10 + PAD_SECTION

    # Description
    for line in desc_lines:
        draw.text((PAD_X, y), line, font=f_desc, fill=GRAY_TEXT)
        y += lh_desc + DESC_LINE_GAP
    y += PAD_SECTION

    # Button
    bx0, bx1 = PAD_X, w - PAD_X
    draw.rounded_rectangle([bx0, y, bx1, y + BUTTON_H], radius=BUTTON_RADIUS,
                            fill=BUTTON_BLUE)
    draw.text((cx, y + BUTTON_H // 2), "Add to Cart",
              font=f_btn, fill=BUTTON_TEXT, anchor="mm")

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst_path, "PNG")
    print(f"  {dst_path.name}  ({w}×{total_h})")


# ── Product definitions ────────────────────────────────────────────────────────

PRODUCTS = [
    {
        "dst_dir":      "v15-vpn",
        "icon_fn":      draw_vpn_icon,
        "title":        "SecureShield VPN — 1-Year Subscription",
        "price":        "$39.99/yr",
        "description":  (
            "No-log policy independently audited by PricewaterhouseCoopers. "
            "AES-256 encryption across 3,000+ servers in 50+ countries. "
            "Protects up to 6 devices simultaneously on Windows, Mac, iOS, and Android. "
            "30-day money-back guarantee."
        ),
        "image_configs": VPN_IMAGE_CONFIGS,
        "badge_types":   VPN_BADGE_TYPES,
    },
    {
        "dst_dir":      "v15-driversed",
        "icon_fn":      draw_driversed_icon,
        "title":        "Online Driver's Education Course — State Certified",
        "price":        "$49.99",
        "description":  (
            "State-approved for learner's permit eligibility in all 50 states. "
            "Includes 30 hours of interactive video instruction, practice tests, "
            "and a DMV knowledge exam simulator. Completion certificate delivered "
            "digitally. Accepted by major insurance providers for good student discount."
        ),
        "image_configs": DE_IMAGE_CONFIGS,
        "badge_types":   DE_BADGE_TYPES,
    },
]


def main() -> None:
    base = Path(__file__).parent
    for prod in PRODUCTS:
        dst_dir = base / prod["dst_dir"]
        dst_dir.mkdir(exist_ok=True)
        print(f"\n{prod['dst_dir']}/")
        for img_name, badge_keys in prod["image_configs"].items():
            make_page(
                icon_fn=prod["icon_fn"],
                title=prod["title"],
                price=prod["price"],
                description=prod["description"],
                badge_keys=badge_keys,
                badge_types=prod["badge_types"],
                dst_path=dst_dir / f"{img_name}.png",
            )


if __name__ == "__main__":
    main()
