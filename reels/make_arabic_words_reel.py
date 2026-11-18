"""Map-journey reel for all Arabic speakers: Italian words that came from Arabic.

Usage: python3 make_arabic_words_reel.py OUT.mp4 [--preview]
Etymologies: zucchero<sukkar, caffè<qahwa, arancia<nāranj (Persian via Arabic), magazzino<makhāzin,
caraffa<gharrāfa, alcol<al-kuḥl, zero<ṣifr (via Fibonacci's zephirum, learned in Bugia/Béjaïa),
dogana & divano<dīwān.
"""
import math, os, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FB, FS = os.path.join(HERE, "Cairo-Black.ttf"), os.path.join(HERE, "Cairo-SemiBold.ttf")
W, H, FPS = 1080, 1920, 30
GREEN, RED, WHITE = (0, 146, 70), (206, 43, 55), (255, 255, 255)
YELLOW, ORANGE, DARK = (255, 214, 90), (232, 118, 18), (28, 30, 40)

LON0, LAT0, KX, KY, Y0 = 3.0, 47.0, 45.0, 58.7, 250


def P(lon, lat):
    return ((lon - LON0) * KX, Y0 + (LAT0 - lat) * KY)


PORTS = {
    "تونس": P(10.2, 36.8), "الشام": P(27.0, 34.6), "الإسكندرية": P(27.0, 31.6), "الأندلس": P(3.0, 39.6), "بجاية": P(5.08, 36.75),
    "Palermo": P(13.36, 38.13), "Venezia": P(12.33, 45.44), "Genova": P(8.93, 44.41), "Napoli": P(14.25, 40.85), "Pisa": P(10.4, 43.72),
}
# sea waypoints (lon, lat) between ports so ships never cross land
VIA = {
    ("تونس", "Palermo"): [(11.6, 37.9)],
    ("الشام", "Venezia"): [(21.0, 35.6), (18.9, 39.0), (18.4, 41.2), (15.2, 43.4)],
    ("الشام", "Palermo"): [(20.0, 35.6), (16.2, 37.3), (15.62, 38.25), (14.4, 38.55)],
    ("الإسكندرية", "Genova"): [(19.0, 34.5), (12.0, 37.0), (11.2, 38.8), (10.6, 41.8), (9.2, 43.6)],
    ("تونس", "Napoli"): [(11.8, 38.6), (13.6, 39.9)],
    ("الأندلس", "Genova"): [(5.6, 41.6), (7.8, 43.4)],
    ("بجاية", "Pisa"): [(6.8, 38.6), (7.6, 41.0), (8.0, 43.2), (9.6, 43.9)],
}


# Italian, Arabic origin, pronunciation, fact (simple MSA), from, to
WORDS = [
    ("ZUCCHERO", "سُكَّر", "تسوكّيرو", "العرب زرعوا قصب السكر في صقلية", "تونس", "Palermo"),
    ("CAFFÈ", "قهوة", "كافّيه", "وصلت إلى أوروبا عبر البندقية", "الشام", "Venezia"),
    ("ARANCIA", "نارنج", "أرانتشا", "أصلها فارسي ونقلها العرب", "الشام", "Palermo"),
    ("MAGAZZINO", "مخازن", "ماگاتسّينو", "بفضل التجارة في البحر المتوسط", "الإسكندرية", "Genova"),
    ("CARAFFA", "غرّافة", "كارافّا", "إبريق الماء", "تونس", "Napoli"),
    ("ALCOL", "الكُحل", "ألكول", "نعم… من كُحل العيون!", "الأندلس", "Genova"),
    ("ZERO", "صِفر", "دزيرو", "فيبوناتشي تعلّمه في بجاية بالجزائر", "بجاية", "Pisa"),
    ("DOGANA", "ديوان", "دوگانا", "معناها اليوم: الجمارك", "تونس", "Palermo"),
]
N = len(WORDS)

_fc = {}


def font(sz, bold=True):
    k = (max(8, int(sz)), bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FB if bold else FS, k[0])
    return _fc[k]


def is_ar(s):
    return any("؀" <= c <= "ۿ" for c in s)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x); return 1 - (1 - x) ** 3


def back(x):
    x = clamp(x); c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


_D = ImageDraw.Draw(Image.new("L", (1, 1)))


def measure(s, size, bold=True):
    bb = _D.multiline_textbbox((0, 0), s, font=font(size, bold), align="center", spacing=4,
                               direction="rtl" if is_ar(s) else "ltr")
    return bb[2] - bb[0]


def fit(s, size, maxw=W - 120, bold=True):
    while size > 20 and measure(s, size, bold) > maxw:
        size -= 4
    return size


def txt(img, s, cx, cy, size, color, a=1.0, scale=1.0, shadow=True, bold=True):
    if a <= 0.01 or scale <= 0.05:
        return
    f = font(size * scale, bold); dr = "rtl" if is_ar(s) else "ltr"
    bb = _D.multiline_textbbox((0, 0), s, font=f, align="center", spacing=4, direction=dr)
    pad = 30
    tw, th = int(bb[2] - bb[0] + 2 * pad), int(bb[3] - bb[1] + 2 * pad)
    layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("L", (tw, th), 0)
        ImageDraw.Draw(sh).multiline_text((pad - bb[0], pad + 8 - bb[1]), s, font=f, fill=140, align="center",
                                          spacing=4, direction=dr)
        layer.putalpha(sh.filter(ImageFilter.GaussianBlur(9)))
    ImageDraw.Draw(layer).multiline_text((pad - bb[0], pad - bb[1]), s, font=f, fill=tuple(color) + (255,),
                                         align="center", spacing=4, direction=dr)
    if a < 1:
        layer.putalpha(Image.fromarray((np.asarray(layer.getchannel("A"), np.float32) * a).astype(np.uint8)))
    img.alpha_composite(layer, (int(cx - tw / 2), int(cy - th / 2)))


def appear(t, t0, d=0.35):
    return ease((t - t0) / d), back((t - t0) / d)


def paste_c(img, im, cx, cy, s=1.0):
    if s <= 0.02:
        return
    if abs(s - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
    img.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def with_shadow(im, blur=16, off=10, alpha=110):
    w, h = im.size
    out = Image.new("RGBA", (w + 4 * blur, h + 4 * blur + off), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, alpha), (2 * blur, 2 * blur + off, 2 * blur + w, 2 * blur + h + off), im.getchannel("A"))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    out.alpha_composite(im, (2 * blur, 2 * blur))
    return out



# ------------------------------------------------------------------ timeline
HOOK, SEG = 4.0, 5.2
T_SAIL0, T_SAIL1, T_STAMP = 0.3, 2.0, 2.3
BONUS0 = HOOK + N * SEG
OUT0 = BONUS0 + 5.6
DUR = int(math.ceil(OUT0 + 6.2))


# ------------------------------------------------------------------ map
def make_map():
    tt = (np.arange(H, dtype=np.float32) / (H - 1))[:, None, None]
    sea = np.broadcast_to(np.array((30, 110, 170), np.float32) * (1 - tt) + np.array((12, 55, 105), np.float32) * tt, (H, W, 3))
    img = Image.fromarray(sea.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    sand, edge = (232, 212, 168, 255), (170, 140, 95, 255)
    europe = [(2.0, 41.4), (3.2, 41.9), (3.1, 43.0), (4.8, 43.4), (6.0, 43.1), (7.5, 43.8), (8.9, 44.4), (9.8, 44.1), (10.3, 43.5),
              (10.5, 42.9), (11.8, 42.1), (12.6, 41.45), (13.6, 41.2), (14.25, 40.85), (14.8, 40.6), (15.3, 40.0), (15.9, 39.4),
              (16.1, 38.7), (15.65, 38.1), (16.05, 37.93), (16.6, 38.5), (17.1, 39.1), (16.6, 39.7), (17.2, 40.45),
              (18.0, 40.05), (18.35, 39.8), (18.5, 40.15), (17.95, 40.65), (16.87, 41.13), (15.9, 41.5), (16.2, 41.9),
              (15.4, 42.0), (14.2, 42.47), (13.5, 43.6), (12.57, 44.06), (12.3, 44.9), (12.33, 45.44), (13.0, 45.7),
              (13.77, 45.65), (14.5, 45.2), (15.2, 44.2), (16.0, 43.5), (17.0, 43.2), (18.5, 42.5), (19.0, 42.1),
              (19.5, 41.5), (19.4, 40.3), (20.2, 39.4), (21.0, 38.5), (21.3, 37.8), (21.7, 36.8), (22.5, 36.4), (23.0, 36.5),
              (23.1, 37.9), (24.0, 38.0), (23.0, 39.3), (22.8, 40.5), (24.0, 40.7), (26.0, 40.9), (26.4, 39.5), (27.5, 38.0),
              (27.5, 60), (2.0, 60)]
    d.polygon([P(*q) for q in europe], fill=sand, outline=edge, width=5)
    africa = [(2.0, 36.6), (5.0, 36.65), (8.0, 36.9), (9.9, 37.3), (10.3, 36.8), (11.1, 37.05), (10.5, 36.4), (11.0, 35.6),
              (10.1, 34.2), (11.1, 33.2), (13.2, 32.9), (15.4, 32.3), (19.0, 30.3), (20.0, 31.5), (21.0, 32.8), (23.0, 32.5),
              (25.0, 31.6), (27.5, 31.3), (27.5, 10), (2.0, 10)]
    d.polygon([P(*q) for q in africa], fill=sand, outline=edge, width=5)
    green, gedge = (205, 226, 168, 255), (80, 135, 70, 255)
    italy = [(7.5, 43.8), (8.9, 44.4), (9.8, 44.1), (10.3, 43.5), (10.5, 42.9), (11.8, 42.1), (12.6, 41.45), (13.6, 41.2),
             (14.25, 40.85), (14.8, 40.6), (15.3, 40.0), (15.9, 39.4), (16.1, 38.7), (15.65, 38.1), (16.05, 37.93),
             (16.6, 38.5), (17.1, 39.1), (16.6, 39.7), (17.2, 40.45), (18.0, 40.05), (18.35, 39.8), (18.5, 40.15),
             (17.95, 40.65), (16.87, 41.13), (15.9, 41.5), (16.2, 41.9), (15.4, 42.0), (14.2, 42.47), (13.5, 43.6),
             (12.57, 44.06), (12.3, 44.9), (12.33, 45.44), (13.0, 45.7), (13.77, 45.65), (13.7, 46.5), (12.3, 47.1),
             (10.5, 46.9), (9.0, 46.4), (7.0, 45.9), (6.7, 45.0)]
    d.polygon([P(*q) for q in italy], fill=green, outline=gedge, width=5)
    sicily = [(15.55, 38.25), (15.1, 37.5), (15.3, 37.07), (15.1, 36.68), (14.25, 37.07), (12.43, 37.8), (12.5, 38.05),
              (13.36, 38.15), (14.0, 38.03), (15.24, 38.22)]
    sardinia = [(9.2, 41.25), (9.8, 40.9), (9.7, 40.0), (9.6, 39.2), (9.0, 39.0), (8.4, 39.1), (8.4, 40.0), (8.2, 40.9), (8.8, 41.1)]
    corsica = [(9.4, 43.0), (9.55, 42.6), (9.4, 41.4), (9.1, 41.4), (8.6, 41.9), (8.6, 42.4), (9.3, 42.7)]
    for isl in (sicily, sardinia, corsica):
        d.polygon([P(*q) for q in isl], fill=green if isl is not corsica else sand, outline=gedge if isl is not corsica else edge, width=4)
    d.polygon([P(*q) for q in [(23.5, 35.55), (24.5, 35.4), (26.3, 35.3), (25.5, 35.05), (23.6, 35.25)]], fill=sand, outline=edge, width=3)
    # labels
    d.text(P(12.6, 42.9), "ITALIA", font=font(46), fill=(60, 110, 60, 255), anchor="mm")
    d.text(P(15.0, 31.5), "العالم العربي", font=font(62), fill=(150, 110, 60, 255), anchor="mm", direction="rtl")
    d.text(P(14.2, 36.45), "صقلية", font=font(30, False), fill=(210, 230, 245, 255), anchor="mm", direction="rtl")
    d.text(P(6.3, 45.9), "أوروبا", font=font(40), fill=(150, 110, 60, 255), anchor="mm", direction="rtl")
    d.text(P(15.5, 34.5), "البحر المتوسط", font=font(40, False), fill=(200, 225, 245, 160), anchor="mm", direction="rtl")
    return img


MAP = make_map()
_MAPARR = np.asarray(MAP.convert("RGB")).astype(np.int32)


def _IS_SEA(x, y):
    r, g, b = _MAPARR[y, max(0, min(W - 1, x))]
    rl, gl, bl = _MAPARR[y, max(0, min(W - 1, x - 25))]
    rr, gr, br = _MAPARR[y, max(0, min(W - 1, x + 25))]
    return b > r + 40 and bl > rl + 40 and br > rr + 40


def waves(img, t):
    d = ImageDraw.Draw(img)
    rnd = random.Random(3)
    for k in range(26):
        x0 = rnd.uniform(0, W); y0 = rnd.uniform(340, 1000)
        x = (x0 + t * 25) % (W + 100) - 50
        if not (0 <= x < W) or not _IS_SEA(int(x), int(y0)):
            continue
        d.arc((x - 22, y0 - 8, x + 22, y0 + 8), 200, 340, fill=(255, 255, 255, 70), width=3)


def _route(fr, to):
    pts = [PORTS[fr]] + [P(*q) for q in VIA.get((fr, to), [])] + [PORTS[to]]
    # Catmull-Rom smoothing
    out = []
    ext = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for k in range(20):
            t = k / 20
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(2)))
    out.append(pts[-1])
    seg = [math.dist(out[i], out[i + 1]) for i in range(len(out) - 1)]
    cum = [0.0]
    for x in seg:
        cum.append(cum[-1] + x)
    return out, cum


_RC = {}


def route_pt(fr, to, s):
    if (fr, to) not in _RC:
        _RC[(fr, to)] = _route(fr, to)
    pts, cum = _RC[(fr, to)]
    L = cum[-1] * clamp(s)
    for i in range(len(pts) - 1):
        if cum[i + 1] >= L:
            f = (L - cum[i]) / max(1e-6, cum[i + 1] - cum[i])
            return (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f)
    return pts[-1]


def ship(label, flip=False):
    im = Image.new("RGBA", (260, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(60, 190), (200, 190), (180, 225), (80, 225)], fill=(120, 75, 40, 255))
    d.line((130, 80, 130, 192), fill=(90, 60, 30, 255), width=7)
    d.polygon([(134, 85), (134, 180), (205, 180)], fill=(250, 248, 240, 255), outline=(180, 170, 150, 255))
    d.polygon([(126, 100), (126, 180), (70, 180)], fill=(240, 236, 225, 255), outline=(180, 170, 150, 255))
    d.polygon([(130, 80), (160, 88), (130, 96)], fill=RED + (255,))
    if flip:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    fs = fit(label, 54, 240)
    tw = measure(label, fs) + 40
    pill = Image.new("RGBA", (int(tw), 80), (0, 0, 0, 0)); dp = ImageDraw.Draw(pill)
    dp.rounded_rectangle((0, 0, tw - 1, 79), 40, fill=WHITE + (255,), outline=(20, 30, 50, 255), width=4)
    dp.text((tw / 2, 38), label, font=font(fs), fill=DARK + (255,), anchor="mm", direction="rtl")
    out = Image.new("RGBA", (max(260, int(tw)), 340), (0, 0, 0, 0))
    out.alpha_composite(im, ((out.width - 260) // 2, 80))
    out.alpha_composite(pill, ((out.width - pill.width) // 2, 0))
    return out


def pin(d, x, y, col, name, a=1.0):
    al = int(255 * a)
    d.ellipse((x - 14, y - 14, x + 14, y + 14), fill=col + (al,), outline=WHITE + (al,), width=4)
    if name:
        anc, tx = "mm", x
        if x > W - 120:
            anc, tx = "rm", x - 26
        elif x < 120:
            anc, tx = "lm", x + 26
        d.text((tx, y + 36 if anc == "mm" else y), name, font=font(32), fill=WHITE + (al,), anchor=anc, stroke_width=4, stroke_fill=(10, 30, 60, al),
               direction="rtl" if is_ar(name) else "ltr")


def stamp_img(text="ITALIANO"):
    im = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((10, 10, 290, 290), outline=(210, 30, 40, 235), width=12)
    d.ellipse((40, 40, 260, 260), outline=(210, 30, 40, 235), width=5)
    d.text((150, 150), text, font=font(46), fill=(210, 30, 40, 235), anchor="mm")
    d.text((150, 95), "★", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40), fill=(210, 30, 40, 235), anchor="mm")
    d.text((150, 205), "✓", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 54), fill=(210, 30, 40, 235), anchor="mm")
    return im.rotate(-14, expand=True, resample=Image.BICUBIC)


STAMP = stamp_img()


def passport_card(it, ar, pr, fact, stamp_p, k):
    cw, ch = 980, 420
    c = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, cw - 1, ch - 1), 36, fill=(246, 240, 225, 255), outline=(150, 120, 80, 255), width=5)
    d.rounded_rectangle((0, 0, cw - 1, 70), 36, fill=(20, 60, 110, 255)); d.rectangle((0, 40, cw - 1, 70), fill=(20, 60, 110, 255))
    d.text((40, 36), f"PASSAPORTO  {k + 1}/{N}", font=font(36), fill=WHITE + (255,), anchor="lm")
    d.text((cw - 40, 36), "جواز سفر الكلمة", font=font(34, False), fill=(200, 220, 240, 255), anchor="rm", direction="rtl")
    d.text((cw - 60, 165), ar, font=font(fit(ar, 110, 270)), fill=DARK + (255,), anchor="rm", direction="rtl")
    d.text((cw - 60, 245), "بالعربية", font=font(32, False), fill=(120, 110, 100, 255), anchor="rm", direction="rtl")
    d.line((cw / 2 + 70, 170, cw / 2 - 20, 170), fill=ORANGE + (255,), width=10)
    d.polygon([(cw / 2 - 40, 170), (cw / 2 - 5, 150), (cw / 2 - 5, 190)], fill=ORANGE + (255,))
    d.text((60, 165), it, font=font(fit(it, 92, 320)), fill=(0, 120, 60, 255), anchor="lm")
    d.text((60, 245), "النطق: " + pr, font=font(36, False), fill=(120, 110, 100, 255), anchor="lm", direction="rtl")
    d.line((40, 300, cw - 40, 300), fill=(0, 0, 0, 40), width=3)
    d.text((cw / 2, 355), fact, font=font(fit(fact, 50, cw - 80)), fill=(20, 60, 110, 255), anchor="mm", direction="rtl")
    if stamp_p > 0:
        s = 2.0 - 1.0 * ease(stamp_p / 0.4)
        st = STAMP.resize((int(STAMP.width * 0.5 * s), int(STAMP.height * 0.5 * s)), Image.BILINEAR)
        al = min(1.0, stamp_p / 0.15)
        st.putalpha(Image.fromarray((np.asarray(st.getchannel("A"), np.float32) * al).astype(np.uint8)))
        c.alpha_composite(st, (int(cw / 2 + 25 - st.width / 2), int(185 - st.height / 2)))
    return with_shadow(c, 16, 10, 120)


LOGO = None
_lp = os.path.join(HERE, "logo", "ciao_khoya_watermark.png")
if os.path.exists(_lp):
    _L = Image.open(_lp).convert("RGBA")
    LOGO = _L.resize((150, int(_L.height * 150 / _L.width)), Image.LANCZOS)
    LOGO_BIG = _L.resize((380, int(_L.height * 380 / _L.width)), Image.LANCZOS)


def header(img, k_done):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((36, 40, 860, 200), 36, fill=(10, 25, 50, 225))
    d.text((820, 92), "كلمات إيطالية أصلها عربي", font=font(52), fill=WHITE + (255,), anchor="rm", direction="rtl")
    for k in range(N):
        x = 80 + k * 52
        done = k < k_done
        d.ellipse((x - 16, 150 - 16, x + 16, 150 + 16), fill=((90, 220, 130) if done else (255, 255, 255)) + (255 if done else 60,))
    d.text((820, 152), f"{k_done}/{N}", font=font(40), fill=YELLOW + (255,), anchor="rm")
    if LOGO is not None:
        img.alpha_composite(LOGO, (W - LOGO.width - 36, 40))


def route_dots(d, fr, to, upto, col=(255, 255, 255), a=255):
    n = 70
    for j in range(int(n * upto)):
        if j % 2 == 0:
            x, y = route_pt(fr, to, j / n)
            d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=col + (a,))


def word_seg(i, tl, t):
    img = MAP.copy(); waves(img, t)
    d = ImageDraw.Draw(img)
    for j in range(i):  # previous routes faded
        _, _, _, _, fr, to = WORDS[j]
        route_dots(d, fr, to, 1.0, (255, 214, 90), 70)
    it, ar, pr, fact, fr, to = WORDS[i]
    p0, p1 = PORTS[fr], PORTS[to]
    s = ease((tl - T_SAIL0) / (T_SAIL1 - T_SAIL0))
    route_dots(d, fr, to, s, (255, 214, 90), 255)
    pin(d, *p0, (210, 140, 40), fr)
    if s >= 0.999:
        pin(d, *p1, GREEN, to)
    x, y = route_pt(fr, to, s)
    bobb = 6 * math.sin(t * 5)
    if tl < T_STAMP + 0.4:
        label = ar
    else:
        label = it
    sh = ship(label if is_ar(label) else ar, flip=p1[0] < p0[0])
    if tl >= T_STAMP + 0.2:  # morph: the label becomes Italian
        q = ease((tl - T_STAMP - 0.2) / 0.4)
        sh2 = ship(ar, flip=p1[0] < p0[0])
        fs = fit(it, 54, 300); tw = measure(it, fs) + 40
        pill = Image.new("RGBA", (int(tw), 80), (0, 0, 0, 0)); dp = ImageDraw.Draw(pill)
        dp.rounded_rectangle((0, 0, tw - 1, 79), 40, fill=(0, 140, 70, 255), outline=WHITE + (255,), width=4)
        dp.text((tw / 2, 38), it, font=font(fs), fill=WHITE + (255,), anchor="mm")
        sh = Image.new("RGBA", (max(sh2.width, pill.width), 340), (0, 0, 0, 0))
        sh.alpha_composite(sh2, ((sh.width - sh2.width) // 2, 0))
        cover = Image.new("RGBA", (sh.width, 84), (0, 0, 0, 0))
        sh.paste(cover, (0, 0))
        pill.putalpha(Image.fromarray((np.asarray(pill.getchannel("A"), np.float32) * q).astype(np.uint8)))
        sh.alpha_composite(pill, ((sh.width - pill.width) // 2, 0))
    if tl < T_SAIL0 + 0.01:
        a_, sc = appear(tl, 0.0, 0.3)
    else:
        sc = 1.0
    paste_c(img, sh, x, y - 110 + bobb, 0.62 * max(sc, 0.05))
    # passport card
    if tl >= T_SAIL1 - 0.1:
        a, s2 = appear(tl, T_SAIL1 - 0.1, 0.35)
        out = ease((tl - (SEG - 0.35)) / 0.3)
        card = passport_card(it, ar, pr, fact, max(0.0, tl - T_STAMP), i)
        paste_c(img, card, W / 2, 1470 + (1 - a) * 400 + out * 500, 1.0)
    header(img, i + (1 if tl >= T_STAMP else 0))
    return img


def hook(t):
    img = MAP.copy(); waves(img, t)
    d = ImageDraw.Draw(img)
    for j, w_ in enumerate(WORDS):
        p = ease((t - 0.3 - 0.12 * j) / 1.2)
        route_dots(d, w_[4], w_[5], p, (255, 214, 90), 150)
    img.alpha_composite(Image.new("RGBA", (W, H), (5, 15, 35, 120)))
    a, s = appear(t, 0.15)
    txt(img, "الإيطاليون يتكلمون العربية…", W / 2, 330, fit("الإيطاليون يتكلمون العربية…", 96), WHITE, a, s)
    a, s = appear(t, 0.8)
    txt(img, "دون أن يعرفوا!", W / 2, 480, 120, YELLOW, a, s)
    a, s = appear(t, 1.8)
    txt(img, "8 كلمات سافرت من العالم العربي\nإلى إيطاليا", W / 2, 1420, fit("8 كلمات سافرت من العالم العربي", 76), WHITE, a, s)
    if LOGO is not None:
        img.alpha_composite(LOGO, (W - LOGO.width - 36, 40))
    return img


def bonus(tl, t):
    img = MAP.copy(); waves(img, t)
    img.alpha_composite(Image.new("RGBA", (W, H), (5, 15, 35, int(170 * ease(tl / 0.4)))))
    a, s = appear(tl, 0.1)
    txt(img, "مفاجأة!", W / 2, 300, 140, YELLOW, a, s)
    a, s = appear(tl, 0.6)
    txt(img, "كلمة «ديوان» أعطت الإيطالية كلمتين:", W / 2, 470, fit("كلمة «ديوان» أعطت الإيطالية كلمتين:", 64), WHITE, a, s)
    a, s = appear(tl, 1.1)
    if a > 0.01:
        c = Image.new("RGBA", (520, 220), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
        d.rounded_rectangle((0, 0, 519, 219), 40, fill=(246, 240, 225, 255), outline=(150, 120, 80, 255), width=5)
        d.text((260, 85), "ديوان", font=font(110), fill=DARK + (255,), anchor="mm", direction="rtl")
        d.text((260, 180), "دِيوان", font=font(34, False), fill=(120, 110, 100, 255), anchor="mm", direction="rtl")
        paste_c(img, with_shadow(c, 14, 8, 120), W / 2, 700, s)
    for k, (it, ar, pr, x) in enumerate((("DOGANA", "الجمارك", "دوگانا", 290), ("DIVANO", "الكنبة", "ديڤانو", 790))):
        p = ease((tl - 1.7 - 0.5 * k) / 0.5)
        if p <= 0.01:
            continue
        d = ImageDraw.Draw(img)
        d.line((W / 2, 820, W / 2 + (x - W / 2) * p, 820 + 230 * p), fill=YELLOW + (255,), width=10)
        c = Image.new("RGBA", (460, 300), (0, 0, 0, 0)); dc = ImageDraw.Draw(c)
        dc.rounded_rectangle((0, 0, 459, 299), 40, fill=(0, 120, 60, 255), outline=WHITE + (255,), width=5)
        dc.text((230, 90), it, font=font(84), fill=WHITE + (255,), anchor="mm")
        dc.text((230, 180), ar, font=font(60), fill=YELLOW + (255,), anchor="mm", direction="rtl")
        dc.text((230, 250), "النطق: " + pr, font=font(34, False), fill=(210, 240, 220, 255), anchor="mm", direction="rtl")
        paste_c(img, with_shadow(c, 14, 8, 120), x, 1220, back(p))
    a, s = appear(tl, 3.2)
    txt(img, "من مكتب الدولة… إلى الكنبة في البيت!", W / 2, 1520, fit("من مكتب الدولة… إلى الكنبة في البيت!", 62), WHITE, a, s)
    if LOGO is not None:
        img.alpha_composite(LOGO, (W - LOGO.width - 36, 40))
    return img


def outro(tl, t):
    img = MAP.copy(); waves(img, t)
    img.alpha_composite(Image.new("RGBA", (W, H), (8, 14, 28, 225)))
    fade = 1 - ease((tl - 2.8) / 0.3) if tl > 2.8 else 1
    a, s = appear(tl, 0.1)
    txt(img, "أي كلمة فاجأتك؟", W / 2, 560, 110, WHITE, a * fade, s)
    a, s = appear(tl, 0.6)
    txt(img, "اكتبها في التعليقات", W / 2, 760, 88, YELLOW, a * fade, s)
    a, s = appear(tl, 1.1)
    txt(img, "وشارك الفيديو مع صديق عربي في إيطاليا", W / 2, 960, fit("وشارك الفيديو مع صديق عربي في إيطاليا", 60), WHITE, a * fade, s, bold=False)
    if tl > 3.0:
        a, s = appear(tl, 3.1, 0.45)
        if LOGO is not None:
            paste_c(img, LOGO_BIG, W / 2, 600, s)
        txt(img, "تابعنا", W / 2, 930, 170, WHITE, a, s)
        a, s = appear(tl, 3.5)
        txt(img, "لتتعلم الإيطالية بالعربي", W / 2, 1160, 86, YELLOW, a, s)
    return img


def frame(t):
    if t < HOOK:
        return hook(t)
    if t < BONUS0:
        i = int((t - HOOK) // SEG)
        return word_seg(i, t - HOOK - i * SEG, t)
    if t < OUT0:
        return bonus(t - BONUS0, t)
    return outro(t - OUT0, t)


if "--preview" in sys.argv:
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    ts = [3.0, HOOK + 1.0, HOOK + 2.2, HOOK + 3.4] + [HOOK + k * SEG + 3.6 for k in range(1, N)] + \
         [BONUS0 + 4.5, OUT0 + 2.0, OUT0 + 5.0]
    cols = 7
    sheet = Image.new("RGB", (360 * cols, 640 * ((len(ts) + cols - 1) // cols)))
    for k, tt in enumerate(ts):
        sheet.paste(frame(tt).convert("RGB").resize((360, 640)), ((k % cols) * 360, (k // cols) * 640))
    sheet.save(os.path.join(od, "sheet.png")); print("DUR", DUR); sys.exit()

OUT = sys.argv[1]
TMPV, TMPA = OUT + ".v.mp4", OUT + ".a.wav"
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                       "-pix_fmt", "yuv420p", TMPV], stdin=subprocess.PIPE)
for fi in range(FPS * DUR):
    ff.stdin.write(frame(fi / FPS).convert("RGB").tobytes())
ff.stdin.close(); ff.wait()

# ------------------------------------------------------------------ audio: oud + darbuka meets mandolin
sr = 44100; n = sr * DUR; ta = np.arange(n) / sr
rng = np.random.default_rng(21)
mus = np.zeros(n); sfx = np.zeros(n)


def add(buf, sig, at):
    i0 = int(at * sr)
    if 0 <= i0 < n:
        e = min(n, i0 + len(sig)); buf[i0:e] += sig[:e - i0]


def env(dur, k):
    tt = np.arange(int(dur * sr)) / sr
    return tt, np.exp(-tt * k)


def note(m):
    return 440 * 2 ** ((m - 69) / 12)


def oud(f, dur=0.4, amp=0.08):
    tt, e = env(dur, 7)
    return sum(np.sin(2 * np.pi * f * h * tt) / h ** 1.3 for h in range(1, 6)) * e * amp


# D Hijaz: D Eb F# G A Bb C D
hij = [62, 63, 66, 67, 69, 70, 72, 74]
phrase = [0, 1, 2, 1, 0, 3, 4, 3, 2, 1, 2, 3, 4, 5, 4, 3]
beat = 0.3
k = 0; t0 = 0.0
while t0 < DUR:
    m = hij[phrase[k % 16]]
    add(mus, oud(note(m)), t0)
    if k % 4 == 0:  # doum
        tt, e = env(0.3, 12); add(mus, np.sin(2 * np.pi * np.cumsum(70 + 60 * np.exp(-tt * 25)) / sr) * e * 0.5, t0)
    if k % 4 in (2, 3):  # tek
        tt, e = env(0.05, 80); add(mus, np.diff(rng.normal(0, 1, len(tt) + 1)) * e * 0.09, t0)
    if k % 8 == 0:
        tt, e = env(1.2, 2); add(mus, np.sin(2 * np.pi * note(50) * tt) * e * 0.12, t0)
    k += 1; t0 += beat
mus = mus / np.abs(mus).max() * 0.5


def mandolin(chord, dur=0.6, amp=0.05):
    tt = np.arange(int(dur * sr)) / sr
    trem = (np.sin(2 * np.pi * 16 * tt) > 0).astype(float) * 0.6 + 0.4
    return sum(np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt) for f in chord) * trem * np.exp(-tt * 3) * amp


tt, e = env(0.35, 12); thud = (np.sin(2 * np.pi * np.cumsum(140 * np.exp(-tt * 10) + 50) / sr) * 0.7 + rng.normal(0, 1, len(tt)) * 0.15) * e
tt = np.arange(int(1.7 * sr)) / sr
sea = np.convolve(rng.normal(0, 1, len(tt)), np.ones(80) / 80, "same") * 0.6 * np.sin(np.pi * tt / 1.7) ** 2
for i in range(N):
    s0 = HOOK + i * SEG
    add(sfx, sea, s0 + T_SAIL0)
    add(sfx, thud, s0 + T_STAMP)
    add(sfx, mandolin([note(67), note(71), note(74)]), s0 + T_STAMP + 0.15)
add(sfx, mandolin([note(62), note(66), note(69)], 1.0, 0.06), BONUS0 + 1.7)
add(sfx, mandolin([note(67), note(71), note(74)], 1.0, 0.06), BONUS0 + 2.2)
add(sfx, mandolin([note(62), note(66), note(69), note(74)], 1.4, 0.06), OUT0 + 3.1)


def write(path, sig):
    sig = sig * np.clip(ta / 0.05, 0, 1) * np.clip((DUR - ta) / 1.2, 0, 1)
    pcm = (np.repeat(np.clip(sig, -0.95, 0.95)[:, None], 2, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())


for path_out, sig in ((OUT, mus * 0.65 + sfx), (OUT.replace(".mp4", "_no_music.mp4"), sfx)):
    write(TMPA, sig)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", TMPV, "-i", TMPA, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "160k", "-shortest", "-movflags", "+faststart", path_out], check=True)
os.remove(TMPV); os.remove(TMPA)
print("done", DUR, "s")
