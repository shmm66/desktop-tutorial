from __future__ import annotations

from pathlib import Path
import tempfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont, PngImagePlugin

LOGO_REVISION = "3"
BG = (0, 0, 0, 0)
NAVY = (5, 13, 24, 255)
NAVY_MID = (9, 26, 39, 255)
TEAL = (53, 229, 196, 255)
GOLD = (247, 210, 121, 255)
WHITE = (242, 249, 252, 255)
RED = (255, 111, 126, 255)


def _font(size: int, bold: bool = False):
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            try:
                return ImageFont.truetype(candidate, max(8, size))
            except OSError:
                pass
    return ImageFont.load_default()


def create_logo_image(path: Path, size: int = 520):
    """Render the revisioned TP medallion once, with antialiasing for app and shortcut icons."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    size = max(96, int(size))
    try:
        with Image.open(path) as cached:
            if cached.size == (size, size) and cached.format == "PNG" and cached.info.get("tpp_logo_revision") == LOGO_REVISION:
                cached.verify()
                return path
    except Exception:
        pass

    # Render at 2x so rounded edges remain smooth at small Windows taskbar sizes.
    scale = 2
    n = size * scale
    img = Image.new("RGBA", (n, n), BG)
    pad = int(n * 0.105)
    box = (pad, pad, n - pad, n - pad)
    radius = (n - 2 * pad) // 2

    glow = Image.new("RGBA", (n, n), BG)
    gd = ImageDraw.Draw(glow)
    gd.ellipse((pad - n * .025, pad - n * .025, n - pad + n * .025, n - pad + n * .025),
               fill=(38, 222, 191, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(max(8, int(n * .035))))
    img.alpha_composite(glow)

    shadow = Image.new("RGBA", (n, n), BG)
    sd = ImageDraw.Draw(shadow)
    sd.ellipse((box[0] + n * .025, box[1] + n * .038, box[2] + n * .025, box[3] + n * .038),
               fill=(0, 0, 0, 205))
    shadow = shadow.filter(ImageFilter.GaussianBlur(max(6, int(n * .025))))
    img.alpha_composite(shadow)

    d = ImageDraw.Draw(img)
    # Layered metallic rim; the rim is a circle, not a square logo tile.
    for inset in range(int(n * .052), 0, -max(1, int(n * .003))):
        tone = max(0, min(255, 18 + inset * 2))
        d.ellipse((pad - inset, pad - inset, n - pad + inset, n - pad + inset),
                  fill=(tone, 67 + tone // 3, 78 + tone // 4, 255))
    d.ellipse(box, fill=NAVY, outline=TEAL, width=max(3, int(n * .012)))
    d.ellipse((pad + n * .028, pad + n * .028, n - pad - n * .028, n - pad - n * .028),
              outline=GOLD, width=max(2, int(n * .005)))

    # Subtle upper glass sheen clipped to the upper half of the medallion.
    sheen = Image.new("RGBA", (n, n), BG)
    sh = ImageDraw.Draw(sheen)
    sh.ellipse((pad + n * .08, pad + n * .035, n - pad - n * .08, n * .51),
               fill=(255, 255, 255, 17))
    mask = Image.new("L", (n, n), 0)
    ImageDraw.Draw(mask).ellipse(box, fill=255)
    sheen.putalpha(Image.composite(sheen.getchannel("A"), Image.new("L", (n, n), 0), mask))
    img.alpha_composite(sheen)

    d = ImageDraw.Draw(img)
    # The TP monogram is the primary mark. A small shadow gives a cut-metal depth.
    f = _font(int(n * .235), True)
    text = "TP"
    bb = d.textbbox((0, 0), text, font=f, stroke_width=0)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    tx = (n - tw) / 2 - bb[0]
    ty = n * .185 - bb[1]
    d.text((tx + n * .008, ty + n * .012), text, font=f, fill=(0, 0, 0, 165))
    d.text((tx, ty), text, font=f, fill=WHITE, stroke_width=max(1, int(n * .0015)),
           stroke_fill=(202, 220, 227, 255))

    # Clean candlesticks and a rising gold path form the market cue at the bottom.
    candle_specs = [
        (0.295, 0.655, 0.735, TEAL),
        (0.405, 0.585, 0.728, TEAL),
        (0.515, 0.625, 0.755, RED),
        (0.625, 0.545, 0.718, TEAL),
        (0.735, 0.505, 0.685, TEAL),
    ]
    candle_w = n * .036
    for x_ratio, y_top, y_bottom, color in candle_specs:
        x = n * x_ratio
        d.line((x, n * (y_top - .035), x, n * (y_bottom + .02)), fill=color, width=max(2, int(n * .006)))
        body_top = n * y_top
        body_bottom = n * y_bottom
        d.rounded_rectangle((x - candle_w / 2, body_top, x + candle_w / 2, body_bottom),
                            radius=max(2, int(n * .007)), fill=color)

    path_points = [
        (n * .235, n * .79), (n * .365, n * .75), (n * .475, n * .77),
        (n * .585, n * .715), (n * .695, n * .725), (n * .79, n * .635),
    ]
    d.line(path_points, fill=GOLD, width=max(3, int(n * .009)), joint="curve")
    ex, ey = path_points[-1]
    arrow = n * .045
    d.polygon([(ex, ey), (ex - arrow, ey + arrow * .38), (ex - arrow * .2, ey + arrow * .8)], fill=GOLD)

    # Small luminous signal point.
    dot = n * .82
    rr = n * .018
    d.ellipse((dot - rr, dot - rr, dot + rr, dot + rr), fill=TEAL, outline=WHITE, width=max(1, int(n * .003)))

    img = img.resize((size, size), Image.Resampling.LANCZOS)
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("tpp_logo_revision", LOGO_REVISION)
    img.save(path, "PNG", optimize=True, pnginfo=metadata)
    return path


if __name__ == "__main__":
    create_logo_image(Path(tempfile.gettempdir()) / "TraderPlannerPro_3D" / "logo.png", 520)
