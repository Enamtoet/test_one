"""Ciao Khoya logo generator. Usage: python3 make_logo.py OUT_DIR"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FB = os.path.join(HERE, "Cairo-Black.ttf")
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

S = 2160  # draw at 2x, downscale for smooth edges
GREEN, RED, WHITE = (0, 146, 70), (206, 43, 55), (255, 255, 255)
MA_RED, MA_GREEN = (193, 39, 45), (0, 98, 51)
DARK = (22, 26, 38)


def star_pts(cx, cy, r, inner=0.38, rot=-math.pi / 2):
    pts = []
    for k in range(10):
        rr = r if k % 2 == 0 else r * inner
        a = rot + k * math.pi / 5
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def bubble(w, h):
    """White speech bubble with Italian stripe, 'Ciao' + 'خويا'. Returns RGBA."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bw, bh = int(w * 0.92), int(h * 0.80)
    x0, y0 = (w - bw) // 2, int(h * 0.02)
    m = Image.new("L", (w, h), 0)
    dm = ImageDraw.Draw(m)
    dm.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), int(bh * 0.22), fill=255)
    # tail (bottom-right, like a reply in a chat)
    tx = x0 + bw * 0.72
    dm.polygon([(tx, y0 + bh - 5), (tx + bw * 0.17, y0 + bh - 5), (tx + bw * 0.20, y0 + bh + h * 0.15)], fill=255)
    # shadow
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 110), (0, int(h * 0.025)), m)
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(w * 0.02)))
    body = Image.new("RGBA", (w, h), (250, 247, 240, 255))
    # tricolor band along the bottom of the bubble
    db = ImageDraw.Draw(body)
    band_y = y0 + bh - int(bh * 0.13)
    for i, c in enumerate((GREEN, WHITE, RED)):
        db.rectangle((x0 + i * bw / 3, band_y, x0 + (i + 1) * bw / 3, y0 + bh), fill=c + (255,))
    db.rectangle((x0, band_y, x0 + bw, band_y + max(2, int(bh * 0.008))), fill=(225, 220, 210, 255))
    im.paste(body, (0, 0), m)

    d = ImageDraw.Draw(im)
    # "Cıao" with a Moroccan star as the dot on the i
    f1 = ImageFont.truetype(FB, int(bh * 0.40))
    word = "Cıao"
    tw = d.textlength(word, font=f1)
    cy1 = y0 + bh * 0.30
    xs = w / 2 - tw / 2
    d.text((xs, cy1), word, font=f1, fill=DARK + (255,), anchor="lm")
    xi = xs + d.textlength("C", font=f1) + d.textlength("ı", font=f1) / 2
    asc = f1.getbbox("ı", anchor="lm")
    r = bh * 0.075
    sy = cy1 + asc[1] - r * 1.25
    d.polygon(star_pts(xi, sy, r), fill=MA_GREEN + (255,))
    # Arabic line
    f2 = ImageFont.truetype(FB, int(bh * 0.34))
    d.text((w / 2, y0 + bh * 0.635), "خويا", font=f2, fill=MA_RED + (255,), anchor="mm", direction="rtl")
    return im


def background(size):
    yy = np.linspace(0, 1, size)[:, None, None]
    g = np.array((10, 66, 70)) * (1 - yy) + np.array((12, 20, 40)) * yy
    g = np.broadcast_to(g, (size, size, 3)).copy()
    xx = np.linspace(-1, 1, size)[None, :]; y2 = np.linspace(-1, 1, size)[:, None]
    g *= (1 - 0.35 * (xx ** 2 + y2 ** 2))[..., None].clip(0.5, 1)
    img = Image.fromarray(g.clip(0, 255).astype(np.uint8)).convert("RGBA")
    pat = Image.new("RGBA", (size, size), (0, 0, 0, 0)); dp = ImageDraw.Draw(pat)
    T = size // 7
    for ty in range(-T, size + T, T):
        for tx in range(-T, size + T, T):
            cx, cy, r = tx + T / 2, ty + T / 2, T * 0.36
            for off in (0, math.pi / 4):
                dp.polygon([(cx + r * math.cos(a + off), cy + r * math.sin(a + off))
                            for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2)],
                           outline=(255, 255, 255, 22), width=max(2, size // 400))
    img.alpha_composite(pat)
    return img


def down(im, s):
    return im.resize((s, s) if im.width == im.height else (s, int(im.height * s / im.width)), Image.LANCZOS)


# 1) profile picture (content kept inside the circle crop)
prof = background(S)
b = bubble(int(S * 0.70), int(S * 0.62))
prof.alpha_composite(b, ((S - b.width) // 2, int(S * 0.17)))
dd = ImageDraw.Draw(prof)
fr = int(S * 0.012)
dd.ellipse((fr, fr, S - fr, S - fr), outline=(255, 214, 90, 255), width=fr)  # gold ring (visible in circle crop)
down(prof.convert("RGB"), 1080).save(os.path.join(OUT, "ciao_khoya_profile.png"))

# 2) watermark / sticker with transparent background
wm = bubble(1600, 1400)
bbox = wm.getbbox(); wm = wm.crop(bbox)
down(wm, 600).save(os.path.join(OUT, "ciao_khoya_watermark.png"))

# 3) preview: how it looks in the round profile frame, plus watermark on a dark card
pv = Image.new("RGB", (1500, 800), (240, 240, 240))
circ = down(prof, 640)
mask = Image.new("L", (640, 640), 0); ImageDraw.Draw(mask).ellipse((0, 0, 639, 639), fill=255)
pv.paste(circ.convert("RGB"), (60, 80), mask)
card = Image.new("RGBA", (700, 640), (30, 40, 55, 255))
w2 = down(wm, 420); card.alpha_composite(w2, ((700 - w2.width) // 2, (640 - w2.height) // 2))
pv.paste(card.convert("RGB"), (760, 80))
pv.save(os.path.join(OUT, "preview.png"))
print("ok")
