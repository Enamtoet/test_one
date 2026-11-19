"""Viral short: the Arab P/B problem in Italian (PASTA->BASTA, POLLO->BOLLO, PAPA->BABA).

Usage: python3 make_pb_reel.py OUT.mp4 [--preview]
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FB, FS = os.path.join(HERE, "Cairo-Black.ttf"), os.path.join(HERE, "Cairo-SemiBold.ttf")
W, H, FPS = 1080, 1920, 30
GREEN, RED, WHITE = (0, 150, 75), (215, 40, 50), (255, 255, 255)
YELLOW, DARK, CREAM = (255, 214, 90), (30, 32, 42), (250, 244, 230)

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



PAIRS = [
    dict(p="PASTA", b="BASTA", pm="معكرونة", bm="كفى!", icon_p="pasta", icon_b="stop",
         punch="طلبتَ معكرونة… فقلتَ للنادل: كفى!"),
    dict(p="POLLO", b="BOLLO", pm="دجاج", bm="طابع الضرائب", icon_p="chicken", icon_b="stamp",
         punch="طلبتَ دجاجاً… فطلبتَ طابعاً بـ16 يورو!"),
    dict(p="PAPÀ", b="BABÀ", pm="أبي", bm="حلوى نابولية", icon_p="dad", icon_b="baba",
         punch="ناديتَ أباك… فطلبتَ حلوى!"),
]
HOOK, PAIR = 3.2, 5.2
TIP0 = HOOK + len(PAIRS) * PAIR
OUT0 = TIP0 + 5.6
DUR = int(math.ceil(OUT0 + 3.8))
FLIP = 1.7   # when P flips to B (inside a pair)

LOGO = None
_lp = os.path.join(HERE, "logo", "ciao_khoya_watermark.png")
if os.path.exists(_lp):
    _L = Image.open(_lp).convert("RGBA")
    LOGO = _L.resize((140, int(_L.height * 140 / _L.width)), Image.LANCZOS)
    LOGO_BIG = _L.resize((320, int(_L.height * 320 / _L.width)), Image.LANCZOS)


# ------------------------------------------------------------------ background
def make_bg():
    img = Image.new("RGBA", (W, H), CREAM + (255,)); d = ImageDraw.Draw(img)
    f = font(150)
    for k in range(60):
        x = (k % 6) * 200 + (100 if (k // 6) % 2 else 0) - 40
        y = (k // 6) * 210 - 60
        d.text((x, y), "P" if (k + k // 6) % 2 == 0 else "B", font=f, fill=(240, 233, 216, 255))
    for i, c in enumerate(((0, 146, 70), WHITE, (206, 43, 55))):
        d.rectangle((i * W / 3, 0, (i + 1) * W / 3, 14), fill=c + (255,))
    return img


BG = make_bg()


# ------------------------------------------------------------------ icons (420x420)
def icon(kind):
    S = 420
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if kind == "pasta":
        d.ellipse((30, 170, 390, 370), fill=(255, 255, 255, 255), outline=(200, 200, 205, 255), width=8)
        d.ellipse((80, 200, 340, 330), fill=(245, 245, 245, 255))
        for k in range(14):
            cx, cy = 120 + (k % 7) * 30, 230 + (k // 7) * 40
            d.arc((cx - 40, cy - 30, cx + 40, cy + 30), 180 + 20 * k, 360 + 20 * k, fill=(240, 200, 90, 255), width=10)
        d.ellipse((160, 215, 260, 285), fill=(210, 50, 40, 255))
        d.ellipse((185, 225, 205, 245), fill=(80, 160, 70, 255))
        d.line((300, 120, 250, 250), fill=(170, 170, 180, 255), width=12)
    elif kind == "stop":
        sk = (240, 195, 160, 255)
        d.rounded_rectangle((120, 190, 300, 380), 60, fill=sk)
        for k, (x, h) in enumerate(((130, 120), (172, 150), (214, 150), (256, 125))):
            d.rounded_rectangle((x, 190 - h, x + 38, 230), 19, fill=sk)
        d.rounded_rectangle((40, 230, 150, 280), 25, fill=sk)
        for r in (40, 70):
            d.arc((210 - 150 - r, 60 - r, 210 + 150 + r, 60 + r * 2), 200, 340, fill=(215, 40, 50, 160), width=6)
    elif kind == "chicken":
        d.ellipse((60, 90, 300, 300), fill=(200, 120, 50, 255))
        d.ellipse((90, 110, 220, 200), fill=(230, 160, 80, 255))
        bone, ol = (250, 246, 236, 255), (150, 130, 110, 255)
        d.line((255, 255, 350, 350), fill=ol, width=44)
        d.ellipse((322, 312, 392, 382), fill=ol); d.ellipse((340, 292, 410, 362), fill=ol)
        d.line((255, 255, 350, 350), fill=bone, width=32)
        d.ellipse((328, 318, 386, 376), fill=bone); d.ellipse((346, 298, 404, 356), fill=bone)
    elif kind == "stamp":
        d.rectangle((70, 60, 350, 380), fill=(255, 255, 255, 255))
        for k in range(10):
            for x, y in ((70 + k * 31, 60), (70 + k * 31, 380)):
                d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(0, 0, 0, 0))
            for x, y in ((70, 60 + k * 35), (350, 60 + k * 35)):
                d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(0, 0, 0, 0))
        d.rectangle((95, 85, 325, 355), fill=(210, 230, 245, 255))
        d.text((210, 150), "MARCA DA", font=font(34), fill=(30, 60, 120, 255), anchor="mm")
        d.text((210, 195), "BOLLO", font=font(52), fill=(30, 60, 120, 255), anchor="mm")
        d.text((210, 290), "€16", font=font(96), fill=(200, 30, 40, 255), anchor="mm")
    elif kind == "dad":
        d.rounded_rectangle((80, 280, 340, 420), 70, fill=(40, 90, 160, 255))
        d.ellipse((120, 80, 300, 280), fill=(225, 175, 135, 255))
        d.chord((115, 60, 305, 190), 180, 360, fill=(60, 45, 40, 255))
        for x in (175, 245):
            d.ellipse((x - 10, 160, x + 10, 185), fill=(30, 25, 25, 255))
        d.chord((165, 205, 255, 245), 180, 360, fill=(60, 45, 40, 255))
        d.arc((175, 215, 245, 255), 20, 160, fill=(150, 40, 40, 255), width=6)
    elif kind == "baba":
        d.ellipse((60, 330, 360, 390), fill=(255, 255, 255, 255), outline=(200, 200, 205, 255), width=6)
        d.rounded_rectangle((140, 230, 280, 360), 30, fill=(200, 140, 60, 255))
        d.ellipse((100, 90, 320, 290), fill=(190, 120, 45, 255))
        d.ellipse((140, 115, 220, 175), fill=(235, 180, 100, 200))
        d.ellipse((190, 70, 230, 110), fill=(220, 40, 60, 255))
    return im


ICONS = {k: icon(k) for k in ("pasta", "stop", "chicken", "stamp", "dad", "baba")}


def flip_word(img, pword, bword, cx, cy, size, p, colp, colb):
    """Draw word; every letter that differs (P->B) flips like a card as p goes 0->1."""
    f = font(size)
    d = ImageDraw.Draw(img)
    cur = pword if p < 0.5 else bword
    col = colp if p < 0.5 else colb
    widths = [d.textlength(c, font=f) for c in cur]
    x = cx - sum(widths) / 2
    sx = abs(math.cos(math.pi * p))
    q = ease((p - 0.5) / 0.5) if p >= 0.5 else 0
    for k, c in enumerate(cur):
        wc = widths[k]
        if pword[k] != bword[k]:
            lay = Image.new("RGBA", (int(wc + 60), int(size * 1.6)), (0, 0, 0, 0))
            ImageDraw.Draw(lay).text((30, size * 0.8), c, font=f, fill=col + (255,), anchor="lm")
            if sx > 0.03:
                lw = max(1, int(lay.width * sx))
                lay2 = lay.resize((lw, lay.height), Image.BILINEAR)
                img.alpha_composite(lay2, (int(x + wc / 2 - lw / 2), int(cy - size * 0.8)))
            if q > 0:
                r = size * 0.58 * (0.6 + 0.4 * q)
                bx = x + wc / 2
                d.ellipse((bx - r, cy - r - 4, bx + r, cy + r - 4), outline=colb + (int(255 * q),), width=10)
        else:
            d.text((x, cy), c, font=f, fill=col + (255,), anchor="lm")
        x += wc


def pair_scene(i, tl):
    P_ = PAIRS[i]
    img = BG.copy()
    sl = (1 - ease(tl / 0.3)) * W - ease((tl - (PAIR - 0.3)) / 0.3) * W
    fp = ease((tl - FLIP) / 0.45)
    flipped = fp >= 0.5
    # label
    a, s = appear(tl, 0.1)
    lab = "تريد أن تقول:" if not flipped else "لكنك تقول:"
    txt(img, lab, W / 2 + sl, 330, 76, DARK if not flipped else RED, a, 1)
    # icon flips together with the letter
    ic = ICONS[P_["icon_p"] if not flipped else P_["icon_b"]]
    sx = abs(math.cos(math.pi * fp)) if 0 < fp < 1 else 1.0
    a, s = appear(tl, 0.2, 0.4)
    if sx > 0.03:
        ic2 = ic.resize((max(1, int(ic.width * sx)), ic.height), Image.BILINEAR)
        paste_c(img, ic2, W / 2 + sl, 640, s)
    # the word
    flip_word(img, P_["p"], P_["b"], W / 2 + sl, 980, 210, fp, GREEN, RED)
    # meaning
    if not flipped:
        a, s = appear(tl, 0.6)
        txt(img, P_["pm"], W / 2 + sl, 1170, 84, GREEN, a, s)
    else:
        a, s = appear(tl, FLIP + 0.3)
        txt(img, "الإيطالي يسمع: " + P_["bm"], W / 2 + sl, 1170, fit("الإيطالي يسمع: " + P_["bm"], 80, W - 120), RED, a, s)
        a, s = appear(tl, FLIP + 1.1)
        txt(img, P_["punch"], W / 2 + sl, 1360, fit(P_["punch"], 62, W - 120), DARK, a, s, shadow=False)
    # progress
    d = ImageDraw.Draw(img)
    for k in range(len(PAIRS)):
        cx = W / 2 + (k - 1) * 70
        d.ellipse((cx - 16, 1560 - 16, cx + 16, 1560 + 16), fill=((215, 40, 50) if k <= i else (200, 195, 185)) + (255,))
    return img


def hook(t):
    img = BG.copy()
    a, s = appear(t, 0.05, 0.35)
    xP = W / 2 - 230 - (1 - ease(t / 0.35)) * 700
    xB = W / 2 + 230 + (1 - ease((t - 0.15) / 0.35)) * 700
    wob = 6 * math.sin(t * 10) * max(0, 1 - t / 2)
    txt(img, "P", xP, 860 + wob, 380, GREEN, 1, 1)
    txt(img, "B", xB, 860 - wob, 380, RED, 1, 1)
    a2, s2 = appear(t, 0.5, 0.3)
    txt(img, "≠", W / 2, 860, 200, DARK, a2, s2, shadow=False)
    a, s = appear(t, 0.8)
    txt(img, "مشكلة كل العرب\nفي إيطاليا", W / 2, 400, 104, DARK, a, s, shadow=False)
    a, s = appear(t, 1.6)
    txt(img, "لأن العربية ليس فيها حرف P", W / 2, 1290, fit("لأن العربية ليس فيها حرف P", 70, W - 120), RED, a, s, shadow=False)
    return img


def tip(tl):
    img = BG.copy()
    a, s = appear(tl, 0.1)
    txt(img, "الحل؟", W / 2, 300, 140, GREEN, a, s, shadow=False)
    a, s = appear(tl, 0.6)
    txt(img, "ضع يدك على حلقك وقل:", W / 2, 520, fit("ضع يدك على حلقك وقل:", 72, W - 120), DARK, a, s, shadow=False)
    d = ImageDraw.Draw(img)
    rows = [("B", "تحس باهتزاز", RED, True, 1.3), ("P", "لا يوجد اهتزاز", GREEN, False, 2.1)]
    for k, (L, lab, col, vib, t0) in enumerate(rows):
        p = ease((tl - t0) / 0.35)
        if p <= 0.01:
            continue
        y = 780 + k * 260
        card = Image.new("RGBA", (920, 220), (0, 0, 0, 0)); dc = ImageDraw.Draw(card)
        dc.rounded_rectangle((0, 0, 919, 219), 40, fill=(255, 255, 255, 255), outline=col + (255,), width=6)
        dc.text((830, 110), L, font=font(150), fill=col + (255,), anchor="mm")
        dc.text((700, 110), lab, font=font(60), fill=DARK + (255,), anchor="rm", direction="rtl")
        # vibration line
        pts = []
        for x in range(60, 300, 6):
            amp = 30 * math.sin((x / 14) + tl * 25) if vib else 0
            pts.append((x, 110 + amp))
        dc.line(pts, fill=col + (255,), width=8)
        card.putalpha(Image.fromarray((np.asarray(card.getchannel("A"), np.float32) * p).astype(np.uint8)))
        paste_c(img, card, W / 2, y + 110, 0.9 + 0.1 * back((tl - t0) / 0.35))
    a, s = appear(tl, 3.0)
    txt(img, "P = B بدون صوت", W / 2, 1390, 100, DARK, a, s, shadow=False)
    return img


def outro(tl):
    img = BG.copy()
    a, s = appear(tl, 0.05)
    txt(img, "اكتب في التعليقات:", W / 2, 420, 80, DARK, a, s, shadow=False)
    a, s = appear(tl, 0.4)
    txt(img, "PASTA", W / 2, 580, 150, GREEN, a, s)
    a2, s2 = appear(tl, 0.6)
    txt(img, "أو", W / 2, 715, 80, DARK, a2, s2, shadow=False)
    a3, s3 = appear(tl, 0.8)
    txt(img, "BASTA?", W / 2, 850, 150, RED, a3, s3)
    a, s = appear(tl, 1.0, 0.45)
    if LOGO is not None:
        paste_c(img, LOGO_BIG, W / 2, 1120, s)
    txt(img, "تابعنا لتتعلم الإيطالية بالعربي", W / 2, 1360, fit("تابعنا لتتعلم الإيطالية بالعربي", 72, W - 120), DARK, a, s, shadow=False)
    return img


def frame(t):
    if t < HOOK:
        img = hook(t)
    elif t < TIP0:
        i = int((t - HOOK) // PAIR)
        img = pair_scene(i, t - HOOK - i * PAIR)
    elif t < OUT0:
        img = tip(t - TIP0)
    else:
        img = outro(t - OUT0)
    if LOGO is not None and t < OUT0:
        img.alpha_composite(LOGO, (W - LOGO.width - 36, 40))
    return img


if "--preview" in sys.argv:
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    ts = [2.6, HOOK + 1.2, HOOK + FLIP + 0.22, HOOK + 4.6, HOOK + PAIR + 1.2, HOOK + PAIR + 4.6,
          HOOK + 2 * PAIR + 1.2, HOOK + 2 * PAIR + 4.6, TIP0 + 4.5, OUT0 + 2.5]
    cols = 5
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

# ------------------------------------------------------------------ audio: playful pizzicato + comedy sfx
sr = 44100; n = sr * DUR; ta = np.arange(n) / sr
rng = np.random.default_rng(8)
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


beat = 0.25
mel = [67, 0, 72, 0, 71, 0, 67, 64, 65, 0, 69, 0, 67, 0, 0, 0]
bas = [48, 0, 55, 0, 53, 0, 55, 0]
k = 0; t0 = 0.0
while t0 < DUR:
    m = mel[k % 16]
    if m:
        tt, e = env(0.2, 18); add(mus, (np.sin(2 * np.pi * note(m) * tt) + 0.3 * np.sin(4 * np.pi * note(m) * tt)) * e * 0.08, t0)
    bm = bas[k % 8]
    if bm:
        tt, e = env(0.25, 12); add(mus, np.sin(2 * np.pi * note(bm) * tt) * e * 0.18, t0)
    if k % 4 == 0:
        tt, e = env(0.2, 20); add(mus, np.sin(2 * np.pi * np.cumsum(50 + 80 * np.exp(-tt * 35)) / sr) * e * 0.35, t0)
    if k % 4 == 2:
        tt, e = env(0.06, 60); add(mus, np.diff(rng.normal(0, 1, len(tt) + 1)) * e * 0.05, t0)
    k += 1; t0 += beat
mus = mus / np.abs(mus).max() * 0.45

tt, e = env(0.6, 4)
bwomp = np.where((np.cumsum(220 * np.exp(-tt * 1.5) + 60) / sr) % 1 < 0.5, 1.0, -1.0) * e * 0.12
tt, e = env(0.12, 35); pop = np.sin(2 * np.pi * (650 + 500 * np.exp(-tt * 40)) * tt) * e * 0.3
tt = np.arange(int(0.25 * sr)) / sr
swish = np.convolve(rng.normal(0, 1, len(tt)), np.ones(10) / 10, "same") * np.sin(np.pi * tt / 0.25) ** 2 * 0.3
tt, e = env(0.6, 6); ding = (np.sin(2 * np.pi * 1318.5 * tt) + 0.6 * np.sin(2 * np.pi * 1975.5 * tt)) * e * 0.18
tt, e = env(0.4, 10); thump = np.sin(2 * np.pi * np.cumsum(120 * np.exp(-tt * 10) + 50) / sr) * e * 0.6
add(sfx, thump, 0.1); add(sfx, thump, 0.25); add(sfx, pop, 0.8)
for i in range(len(PAIRS)):
    s0 = HOOK + i * PAIR
    add(sfx, swish, s0); add(sfx, ding, s0 + 0.6)
    add(sfx, swish, s0 + FLIP); add(sfx, bwomp, s0 + FLIP + 0.25)
    add(sfx, pop, s0 + FLIP + 1.1)
add(sfx, ding, TIP0 + 0.1); add(sfx, pop, TIP0 + 1.3); add(sfx, pop, TIP0 + 2.1); add(sfx, ding, OUT0 + 1.0)


def write(path, sig):
    sig = sig * np.clip(ta / 0.05, 0, 1) * np.clip((DUR - ta) / 0.8, 0, 1)
    pcm = (np.repeat(np.clip(sig, -0.95, 0.95)[:, None], 2, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())


for path_out, sig in ((OUT, mus * 0.7 + sfx), (OUT.replace(".mp4", "_no_music.mp4"), sfx)):
    write(TMPA, sig)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", TMPV, "-i", TMPA, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "160k", "-shortest", "-movflags", "+faststart", path_out], check=True)
os.remove(TMPV); os.remove(TMPA)
print("done", DUR, "s")
