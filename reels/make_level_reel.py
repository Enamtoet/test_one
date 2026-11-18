"""Game-style story reel: 'A new Moroccan in Italy - LEVEL 1: La Stazione' (cliffhanger).

Usage: python3 make_level_reel.py OUT.mp4 [--preview]
"""
import math, os, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FB, FS = os.path.join(HERE, "Cairo-Black.ttf"), os.path.join(HERE, "Cairo-SemiBold.ttf")
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
W, H, FPS = 1080, 1920, 30
GREEN, RED, WHITE = (0, 146, 70), (206, 43, 55), (255, 255, 255)
YELLOW, ORANGE, DARK = (255, 214, 90), (232, 118, 18), (28, 30, 40)
SKIN_K, SKIN_I = (200, 150, 110), (240, 200, 168)

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
T_S1, T_S2, T_S3, T_S4, T_CL, T_END = 3.5, 12.0, 24.0, 33.0, 47.0, 56.0
DUR = int(T_END)
UNLOCKS = [  # (start, italian, darija, pronunciation)
    (8.6, "BIGLIETTO", "التيكي", "بيلْييتّو"),
    (20.6, "ANDATA E RITORNO", "مشية وجية", "أنداتا إي ريتورنو"),
    (28.4, "BINARIO", "الكاي", "بيناريو"),
    (42.6, "CONVALIDARE", "تختم التيكي فالماكينة\nقبل ما تطلع للترينو", "كونڤاليداري"),
]
UNLOCK_DUR = 3.2
ZOOM_T = 38.6


# ------------------------------------------------------------------ drawing helpers
def grad_img(w, h, top, bot):
    tt = (np.arange(h, dtype=np.float32) / (h - 1))[:, None, None]
    a = np.broadcast_to(np.array(top, np.float32) * (1 - tt) + np.array(bot, np.float32) * tt, (h, w, 3))
    return Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")


def face(d, cx, cy, skin, talk=0.0, angry=0.0, shock=False, blink=False, lip=(150, 40, 40), r=80):
    d.ellipse((cx - r - 10, cy - 15, cx - r + 14, cy + 25), fill=skin + (255,))
    d.ellipse((cx + r - 14, cy - 15, cx + r + 10, cy + 25), fill=skin + (255,))
    d.ellipse((cx - r, cy - r * 1.05, cx + r, cy + r * 1.05), fill=skin + (255,))
    for k, ex in enumerate((cx - 32, cx + 32)):
        s = -1 if k == 0 else 1
        if shock:
            d.ellipse((ex - 17, cy - 22, ex + 17, cy + 12), fill=WHITE + (255,), outline=(30, 25, 25, 255), width=3)
            d.ellipse((ex - 5, cy - 9, ex + 5, cy + 1), fill=(30, 25, 25, 255))
        else:
            h = 3 if blink else 15
            d.ellipse((ex - 10, cy - 5 - h, ex + 10, cy - 5 + h), fill=(35, 25, 25, 255))
            if not blink:
                d.ellipse((ex - 3, cy - 14, ex + 4, cy - 7), fill=(255, 255, 255, 255))
        if angry > 0.05:
            d.line((ex - 22 * s, cy - 44 + 12 * angry, ex + 20 * s, cy - 34), fill=(50, 35, 30, 255), width=8)
        else:
            d.line((ex - 20, cy - 42 - (8 if shock else 0), ex + 20, cy - 42 - (8 if shock else 0)), fill=(50, 35, 30, 255), width=8)
    my = cy + 45
    if shock:
        d.ellipse((cx - 16, my - 18, cx + 16, my + 18), fill=(90, 20, 25, 255))
    elif talk > 0.05:
        h = 6 + 26 * talk
        d.ellipse((cx - 24, my - h / 2, cx + 24, my + h / 2), fill=(90, 20, 25, 255), outline=lip + (255,), width=4)
    else:
        d.arc((cx - 24, my - 20, cx + 24, my + 8), 20, 160, fill=lip + (255,), width=6)


def star(d, cx, cy, r, col, w=4):
    pts = [(cx + r * math.sin(2 * math.pi * k / 5), cy - r * math.cos(2 * math.pi * k / 5)) for k in range(5)]
    d.line([pts[(2 * k) % 5] for k in range(6)], fill=col, width=w)


def khoya(talk=0.0, shock=False, walk=None, ticket=False, blink=False, sit=False):
    im = Image.new("RGBA", (440, 620), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sw = math.sin(walk) if walk is not None else 0
    for k, s in ((0, 1), (1, -1)):
        x = 175 + 70 * k + s * 26 * sw
        d.rounded_rectangle((x - 26, 440, x + 26, 590), 16, fill=(40, 60, 110, 255))
        d.ellipse((x - 36, 570, x + 40, 612), fill=WHITE + (255,))
    d.rounded_rectangle((115, 290, 325, 470), 60, fill=(193, 39, 45, 255))   # hoodie
    d.line((200, 300, 196, 360), fill=WHITE + (255,), width=5); d.line((240, 300, 244, 360), fill=WHITE + (255,), width=5)
    star(d, 220, 410, 26, (0, 98, 51, 255), 6)
    for k, (sx, s) in enumerate(((135, -1), (305, 1))):
        if ticket and k == 1:
            hx, hy = 380, 250
        else:
            hx, hy = sx + s * 20 - (s * 30 * sw if walk is not None else 0) * (1 if k == 0 else -1), 450
        d.line((sx, 320, hx, hy), fill=(193, 39, 45, 255), width=44)
        d.ellipse((hx - 24, hy - 24, hx + 24, hy + 24), fill=SKIN_K + (255,))
        if ticket and k == 1:
            d.rounded_rectangle((hx - 10, hy - 95, hx + 60, hy - 15), 8, fill=(245, 245, 235, 255), outline=(120, 120, 120, 255), width=3)
            d.line((hx, hy - 70, hx + 50, hy - 70), fill=(120, 120, 120, 255), width=4)
            d.line((hx, hy - 50, hx + 35, hy - 50), fill=(120, 120, 120, 255), width=4)
    face(d, 220, 190, SKIN_K, talk, shock=shock, blink=blink)
    d.chord((132, 85, 308, 215), 180, 360, fill=(25, 20, 20, 255))                 # hair
    d.polygon([(140, 160), (160, 110), (190, 140)], fill=(25, 20, 20, 255))
    d.chord((150, 200, 290, 290), 20, 160, fill=(60, 45, 40, 70))                  # stubble
    if shock:
        d.ellipse((300, 100, 326, 140), fill=(120, 190, 255, 230))
    return im


def clerk(talk=0.0, blink=False):
    im = Image.new("RGBA", (440, 440), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((90, 290, 350, 460), 70, fill=(245, 245, 245, 255))
    d.polygon([(150, 290), (220, 380), (290, 290), (330, 300), (330, 460), (110, 460), (110, 300)], fill=(60, 70, 90, 255))
    d.polygon([(205, 300), (235, 300), (228, 400), (212, 400)], fill=RED + (255,))
    face(d, 220, 190, SKIN_I, talk, blink=blink)
    d.chord((135, 90, 305, 200), 180, 360, fill=(140, 140, 145, 255))
    d.chord((185, 215, 255, 250), 180, 360, fill=(110, 80, 60, 255))               # moustache
    for x in (188, 252):
        d.ellipse((x - 28, 160, x + 28, 210), outline=(40, 40, 50, 255), width=5)
    return im


def controller(talk=0.0, angry=0.0, blink=False, point=False):
    im = Image.new("RGBA", (440, 620), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for x in (180, 260):
        d.rounded_rectangle((x - 28, 440, x + 28, 590), 14, fill=(25, 35, 70, 255))
        d.ellipse((x - 38, 570, x + 38, 612), fill=(20, 20, 20, 255))
    d.rounded_rectangle((105, 290, 335, 480), 60, fill=(30, 45, 90, 255))
    d.polygon([(205, 300), (235, 300), (228, 400), (212, 400)], fill=RED + (255,))
    for y in (340, 380, 420):
        d.ellipse((246, y, 258, y + 12), fill=(230, 190, 60, 255))
    if point:
        d.line((115, 320, 20, 250), fill=(30, 45, 90, 255), width=44)
        d.ellipse((-4, 226, 44, 274), fill=SKIN_I + (255,))
    else:
        d.rounded_rectangle((120, 380, 320, 430), 25, fill=(40, 58, 110, 255))      # crossed arms
    face(d, 220, 195, SKIN_I, talk, angry=angry, blink=blink)
    d.chord((185, 220, 255, 255), 180, 360, fill=(70, 50, 40, 255))
    d.rounded_rectangle((135, 70, 305, 135), 20, fill=(25, 35, 70, 255))            # cap
    d.rectangle((135, 115, 305, 132), fill=RED + (255,))
    d.chord((120, 115, 320, 165), 0, 180, fill=(15, 20, 40, 255))
    d.ellipse((205, 80, 235, 108), fill=(230, 190, 60, 255))
    return im


# ------------------------------------------------------------------ bubbles
def wrap(s, size, bold, maxw):
    out = []
    for para in s.split("\n"):
        cur = ""
        for wd in para.split(" "):
            trial = (cur + " " + wd).strip()
            if measure(trial, size, bold) <= maxw or not cur:
                cur = trial
            else:
                out.append(cur); cur = wd
        out.append(cur)
    return out


def bubble(main, sub=None, tail="left", maxw=560):
    ar = is_ar(main)
    pad, ms = 32, (64 if ar else 56)
    lm = wrap(main, ms, True, maxw)
    ls = wrap(sub, 40, False, maxw) if sub else []
    wmax = max([measure(x, ms) for x in lm] + [measure(x, 40, False) for x in ls])
    bw = int(wmax + 2 * pad); lhm, lhs = int(ms * 1.35), 54
    bh = int(pad + len(lm) * lhm + (20 + len(ls) * lhs if ls else 0) + pad * 0.6)
    im = Image.new("RGBA", (bw, bh + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, bw - 1, bh), 38, fill=(252, 250, 245, 255))
    tx = 70 if tail == "left" else bw - 70
    d.polygon([(tx - 25, bh - 2), (tx + 25, bh - 2), (tx + (-30 if tail == "left" else 30), bh + 38)], fill=(252, 250, 245, 255))
    y = pad * 0.7
    for ln in lm:
        if ar:
            d.text((bw - pad, y + lhm / 2), ln, font=font(ms), fill=DARK + (255,), anchor="rm", direction="rtl")
        else:
            d.text((pad, y + lhm / 2), ln, font=font(ms), fill=(0, 110, 60, 255), anchor="lm")
        y += lhm
    if ls:
        d.line((pad, y + 8, bw - pad, y + 8), fill=(0, 0, 0, 40), width=2); y += 20
        for ln in ls:
            d.text((bw - pad, y + lhs / 2), ln, font=font(40, False), fill=(90, 95, 105, 255), anchor="rm", direction="rtl")
            y += lhs
    return with_shadow(im, 12, 8, 100)


def thought(text):
    fs = 64
    tw = measure(text, fs)
    w, h = int(tw + 140), 220
    im = Image.new("RGBA", (w, h + 90), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rng_ = random.Random(len(text))
    for k in range(9):
        cx = 60 + (w - 120) * k / 8; cy = h / 2 + rng_.uniform(-50, 50)
        r = rng_.uniform(55, 80)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(245, 245, 255, 255))
    d.rounded_rectangle((30, 40, w - 30, h - 40), 60, fill=(245, 245, 255, 255))
    for k, (x, y, r) in enumerate(((70, h + 20, 22), (40, h + 70, 13))):
        d.ellipse((x - r, y - r, x + r, y + r), fill=(245, 245, 255, 255))
    d.text((w / 2, h / 2), text, font=font(fs), fill=(60, 50, 120, 255), anchor="mm", direction="rtl" if is_ar(text) else "ltr")
    return with_shadow(im, 12, 8, 90)


def pop_in(img, im, x, y, tl, t0, t1=None, anchor="bl"):
    """paste with pop scale; (x,y) = bottom-left of the bubble tail area"""
    a, s = appear(tl, t0, 0.3)
    if a <= 0.01:
        return
    if t1 is not None and tl > t1:
        f = 1 - ease((tl - t1) / 0.25)
        if f <= 0.01:
            return
        s *= f
    w, h = im.width, im.height
    cx = x + w / 2 if anchor == "bl" else x - w / 2
    paste_c(img, im, cx, y - h / 2, s)


# ------------------------------------------------------------------ backgrounds
def make_station():
    img = grad_img(W, H, (150, 195, 230), (210, 225, 235)); d = ImageDraw.Draw(img)
    for k in range(-1, 5):
        x = k * 300
        d.arc((x - 30, -120, x + 330, 420), 180, 360, fill=(90, 100, 115, 255), width=14)
        d.line((x - 30, 150, x - 30, 1150), fill=(90, 100, 115, 255), width=18)
    for y in range(0, 300, 60):
        d.line((0, y, W, y), fill=(255, 255, 255, 60), width=3)
    d.rectangle((0, 820, W, 1200), fill=(225, 214, 190, 255))
    for x in range(0, W, 180):
        d.rectangle((x + 30, 860, x + 150, 1120), fill=(205, 192, 165, 255))
    floor = Image.new("RGBA", (W, H - 1200), (0, 0, 0, 0)); df = ImageDraw.Draw(floor)
    for yy_ in range(0, H - 1200, 90):
        for xx_ in range(0, W, 90):
            df.rectangle((xx_, yy_, xx_ + 89, yy_ + 89), fill=((170, 170, 175) if (xx_ // 90 + yy_ // 90) % 2 else (195, 195, 200)) + (255,))
    img.alpha_composite(floor, (0, 1200))
    return img


BG_STATION = make_station()
BOARD_ROWS = [("10:05", "BOLOGNA C.LE", "7"), ("10:12", "TORINO P.NUOVA", "12"), ("10:20", "VENEZIA S.L.", "4"),
              ("10:31", "ROMA TERMINI", "9")]


def board(img, tl):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((50, 230, 1030, 790), 24, fill=(18, 24, 48, 255), outline=(60, 70, 90, 255), width=8)
    f = ImageFont.truetype(MONO, 44); fh = ImageFont.truetype(MONO, 50)
    d.text((540, 290), "PARTENZE  ·  DEPARTURES", font=fh, fill=WHITE + (255,), anchor="mm")
    d.text((90, 360), "ORA", font=f, fill=(150, 160, 190, 255), anchor="lm")
    d.text((260, 360), "DESTINAZIONE", font=f, fill=(150, 160, 190, 255), anchor="lm")
    d.text((990, 360), "BIN", font=f, fill=(150, 160, 190, 255), anchor="rm")
    rnd = random.Random(int(tl * 20))
    for k, row in enumerate(BOARD_ROWS):
        y = 440 + k * 92
        settle = 0.5 + 0.35 * k
        hi = k == 0
        col = YELLOW if not hi or (tl % 0.8) < 0.55 else (255, 255, 255)
        for j, (txt_, x, anc) in enumerate(((row[0], 90, "lm"), (row[1], 260, "lm"), (row[2], 990, "rm"))):
            s = txt_ if tl > settle + 0.1 * j else "".join(rnd.choice("ABCDEFGHILMNOPRSTUVZ0123456789") if c != " " else " " for c in txt_)
            d.text((x, y), s, font=f, fill=col + (255,), anchor=anc)
        d.line((80, y + 46, 1000, y + 46), fill=(40, 50, 80, 255), width=2)


def make_counter():
    img = grad_img(W, H, (232, 220, 196), (205, 190, 165)); d = ImageDraw.Draw(img)
    for y in range(0, H, 120):
        d.line((0, y, W, y), fill=(0, 0, 0, 18), width=2)
    d.rounded_rectangle((120, 380, 960, 1030), 30, fill=(70, 80, 95, 255))
    d.rounded_rectangle((150, 410, 930, 1000), 20, fill=(170, 200, 215, 255))
    return img


BG_COUNTER = make_counter()


def counter_front(img):
    d = ImageDraw.Draw(img)
    glass = Image.new("RGBA", (780, 590), (200, 230, 245, 55))
    ImageDraw.Draw(glass).line((80, 40, 260, 400), fill=(255, 255, 255, 90), width=16)
    img.alpha_composite(glass, (150, 410))
    d.rectangle((60, 1000, 1020, 1160), fill=(150, 100, 60, 255))
    d.rectangle((60, 1000, 1020, 1020), fill=(120, 75, 45, 255))
    d.rounded_rectangle((300, 1040, 780, 1130), 16, fill=(0, 70, 140, 255))
    d.text((540, 1085), "BIGLIETTERIA", font=font(56), fill=WHITE + (255,), anchor="mm")


def make_platform():
    img = grad_img(W, H, (160, 200, 235), (225, 232, 238)); d = ImageDraw.Draw(img)
    d.polygon([(0, 0), (W, 0), (W, 200), (0, 260)], fill=(40, 70, 60, 255))
    for x in range(60, W, 240):
        d.line((x, 200, x, 1200), fill=(40, 70, 60, 255), width=16)
    for k in range(6):
        y = 860 + k * 22
        d.ellipse((-200 + k * 300, y - 140, 300 + k * 300, y + 120), fill=(120, 165, 110, 255))
    d.rectangle((0, 1080, W, 1240), fill=(120, 110, 100, 255))
    for x in range(0, W, 50):
        d.rectangle((x, 1150, x + 30, 1175), fill=(90, 70, 55, 255))
    d.line((0, 1145, W, 1145), fill=(170, 170, 180, 255), width=8); d.line((0, 1200, W, 1200), fill=(170, 170, 180, 255), width=8)
    d.rectangle((0, 1240, W, H), fill=(180, 180, 182, 255))
    d.rectangle((0, 1262, W, 1284), fill=(250, 210, 40, 255))
    d.line((700, 200, 700, 300), fill=(60, 60, 60, 255), width=8); d.line((900, 200, 900, 300), fill=(60, 60, 60, 255), width=8)
    d.rounded_rectangle((620, 300, 980, 520), 20, fill=(0, 70, 140, 255), outline=WHITE + (255,), width=6)
    d.text((800, 350), "BINARIO", font=font(52), fill=WHITE + (255,), anchor="mm")
    d.text((800, 445), "7", font=font(140), fill=WHITE + (255,), anchor="mm")
    return img


BG_PLATFORM = make_platform()


def train_img():
    tw = 2200
    im = Image.new("RGBA", (tw, 470), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, tw, 440), 60, fill=(240, 242, 245, 255))
    d.polygon([(0, 60), (160, 0), (160, 440), (0, 440)], fill=(240, 242, 245, 255))
    d.rectangle((0, 330, tw, 370), fill=GREEN + (255,)); d.rectangle((0, 370, tw, 395), fill=RED + (255,))
    for x in range(200, tw - 100, 210):
        d.rounded_rectangle((x, 80, x + 150, 220), 20, fill=(40, 60, 90, 255))
    for x in (520, 1360):
        d.rounded_rectangle((x, 60, x + 120, 420), 12, fill=(200, 205, 210, 255), outline=(120, 125, 130, 255), width=5)
    d.rounded_rectangle((30, 100, 140, 210), 20, fill=(40, 60, 90, 255))
    d.text((700, 280), "REGIONALE", font=font(60), fill=(0, 70, 140, 255), anchor="lm")
    for x in (300, 800, 1500, 2000):
        d.ellipse((x - 50, 400, x + 50, 470), fill=(40, 40, 40, 255))
    return im


TRAIN = train_img()


def make_interior():
    img = grad_img(W, H, (215, 210, 200), (180, 175, 168)); d = ImageDraw.Draw(img)
    d.rounded_rectangle((60, 250, 1020, 830), 50, fill=(90, 95, 100, 255))
    return img


BG_INT = make_interior()


def interior(img, t):
    win = Image.new("RGBA", (920, 540), (0, 0, 0, 0)); dw = ImageDraw.Draw(win)
    sky = grad_img(920, 540, (140, 190, 235), (220, 235, 240)); win.alpha_composite(sky)
    for layer, (col, amp, base, sp) in enumerate((((140, 180, 120), 60, 330, 120), ((90, 150, 80), 50, 420, 300))):
        pts = [(x, base - amp * (0.5 + 0.5 * math.sin((x + t * sp) / 110 + layer))) for x in range(0, 921, 20)]
        dw.polygon(pts + [(920, 540), (0, 540)], fill=col + (255,))
    for k in range(3):
        x = (k * 400 - t * 900) % 1300 - 200
        dw.rectangle((x, 60, x + 18, 540), fill=(70, 70, 70, 255))
    m = Image.new("L", (920, 540), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 919, 539), 36, fill=255)
    win.putalpha(m)
    img.alpha_composite(win, (80, 270))
    d = ImageDraw.Draw(img)
    for x in (80, 600):
        d.rounded_rectangle((x, 1180, x + 400, 1650), 40, fill=(30, 70, 140, 255))
        d.rounded_rectangle((x + 30, 1210, x + 370, 1330), 30, fill=(230, 230, 230, 255))


# ------------------------------------------------------------------ HUD + unlock card
LOGO = None
_lp = os.path.join(HERE, "logo", "ciao_khoya_watermark.png")
if os.path.exists(_lp):
    _L = Image.open(_lp).convert("RGBA")
    LOGO = _L.resize((150, int(_L.height * 150 / _L.width)), Image.LANCZOS)
    LOGO_BIG = _L.resize((380, int(_L.height * 380 / _L.width)), Image.LANCZOS)


def xp_at(t):
    xp = 0.0
    for (t0, *_r) in UNLOCKS:
        xp += 25 * ease((t - (t0 + 1.4)) / 0.6)
    if t >= T_CL + 0.9:
        xp -= 50 * ease((t - (T_CL + 0.9)) / 0.6)
    return xp


def hud(img, t):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((36, 40, 470, 112), 36, fill=(15, 20, 35, 220), outline=YELLOW + (255,), width=4)
    d.text((70, 76), "LV.1", font=font(44), fill=YELLOW + (255,), anchor="lm")
    d.text((190, 76), "LA STAZIONE", font=font(40), fill=WHITE + (255,), anchor="lm")
    xp = xp_at(t)
    neg = t >= T_CL + 0.9
    d.rounded_rectangle((36, 128, 470, 160), 16, fill=(15, 20, 35, 220))
    fw = 430 * clamp(xp / 100)
    if fw > 4:
        d.rounded_rectangle((38, 130, 38 + fw, 158), 14, fill=((255, 80, 70) if neg else (80, 220, 120)) + (255,))
    d.text((490, 144), f"{int(round(xp))}/100 XP", font=font(34), fill=WHITE + (255,), anchor="lm")
    if LOGO is not None:
        img.alpha_composite(LOGO, (W - LOGO.width - 36, 36))


def padlock(open_p):
    im = Image.new("RGBA", (150, 170), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    lift = 30 * open_p
    d.arc((30, 10 - lift, 120, 110 - lift), 180, 360, fill=(200, 200, 210, 255), width=16)
    d.line((30, 60 - lift, 30, 85 - lift * 0), fill=(200, 200, 210, 255), width=16) if open_p < 0.5 else None
    d.line((120, 60 - lift, 120, 80), fill=(200, 200, 210, 255), width=16)
    d.rounded_rectangle((10, 75, 140, 165), 18, fill=YELLOW + (255,))
    d.ellipse((63, 100, 87, 124), fill=(80, 60, 20, 255)); d.rectangle((70, 115, 80, 145), fill=(80, 60, 20, 255))
    return im


def unlock(img, t):
    for (t0, it, dar, pr) in UNLOCKS:
        tl = t - t0
        if 0 <= tl < UNLOCK_DUR:
            fade = 1 - ease((tl - (UNLOCK_DUR - 0.3)) / 0.3)
            img.alpha_composite(Image.new("RGBA", (W, H), (5, 8, 20, int(150 * ease(tl / 0.3) * fade))))
            a, s = appear(tl, 0.05, 0.4)
            nl = dar.count("\n") + 1
            cw, ch = 940, 560 + 70 * (nl - 1)
            c = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
            d.rounded_rectangle((0, 0, cw - 1, ch - 1), 46, fill=(18, 24, 40, 245), outline=YELLOW + (255,), width=6)
            d.text((cw / 2, 70), "كلمة جديدة!", font=font(52), fill=YELLOW + (255,), anchor="mm", direction="rtl")
            c.alpha_composite(padlock(ease((tl - 0.4) / 0.4)), (cw // 2 - 75, 100))
            d.text((cw / 2, 330), it, font=font(fit(it, 92, cw - 80)), fill=(90, 230, 140, 255), anchor="mm")
            d.multiline_text((cw / 2, 440 if nl == 1 else 470), dar, font=font(56 if nl == 1 else 48), fill=WHITE + (255,),
                             anchor="mm", align="center", direction="rtl")
            d.text((cw / 2, ch - 40), "كيتنطق: " + pr, font=font(36, False), fill=(190, 200, 220, 255), anchor="mm", direction="rtl")
            paste_c(img, c, W / 2, 960, s * fade)
            if 1.2 <= tl < 2.2:
                q = (tl - 1.2) / 1.0
                txt(img, "+25 XP", W / 2 + 200 * q, 640 - 470 * q, 72, (90, 230, 140), 1 - q * 0.6, 1)


# ------------------------------------------------------------------ scenes
def blinking(t, ph=0.0):
    return ((t + ph) % 3.3) < 0.12


def talk(t, t0, dur):
    return 0.5 + 0.5 * abs(math.sin((t - t0) * 13)) if t0 <= t < t0 + dur else 0.0


B = {
    "where": thought("فين نشري التيكي؟"),
    "k_ask": bubble("Un biglietto per Bologna, per favore.", "واحد التيكي لبولونيا، عافاك.", "left"),
    "c_q": bubble("Solo andata o andata e ritorno?", "غير الذهاب ولا مشية وجية؟", "left"),
    "what": thought("شنو؟!"),
    "k_ar": bubble("Andata e ritorno!", "مشية وجية!", "left"),
    "ctl1": bubble("Biglietto, prego!", "التيكي، عافاك!", "right"),
    "k_ecco": bubble("Eccolo!", "ها هو!", "left"),
    "ctl2": bubble("Ma non è convalidato!", "ولكن ما مختومش!", "right"),
    "huh": thought("شنو هي convalidato؟!"),
}


def scene1(t):
    tl = t - T_S1
    img = BG_STATION.copy()
    board(img, tl)
    p = ease((tl - 0.5) / 2.2)
    x = -420 + 720 * p
    walking = 0.5 < tl < 2.7
    img.alpha_composite(khoya(walk=tl * 9 if walking else None, blink=blinking(t)), (int(x), 1060 + int(8 * abs(math.sin(tl * 9))) if walking else 1060))
    pop_in(img, B["where"], min(int(x) + 300, W - B["where"].width - 10), 1110, tl, 2.9, 5.0)
    return img


def scene2(t):
    tl = t - T_S2
    img = BG_COUNTER.copy()
    img.alpha_composite(clerk(talk(tl, 3.3, 1.6), blinking(t, 1)), (320, 570))
    counter_front(img)
    shock = 5.3 <= tl < 6.9
    img.alpha_composite(khoya(talk(tl, 0.8, 1.6) + talk(tl, 7.0, 1.0), shock=shock, blink=blinking(t)), (-20, 1080))
    pop_in(img, B["k_ask"], 300, 1270, tl, 0.8, 3.0)
    pop_in(img, B["c_q"], 360, 560, tl, 3.3, 8.2)
    pop_in(img, B["what"], 300, 1250, tl, 5.3, 6.8)
    pop_in(img, B["k_ar"], 300, 1270, tl, 7.0, 8.3)
    return img


def scene3(t):
    tl = t - T_S3
    img = BG_PLATFORM.copy()
    p = ease((tl - 0.6) / 2.2)
    tx = int(1100 - 1250 * p)
    img.alpha_composite(TRAIN, (tx, 720 + (int(3 * math.sin(tl * 40)) if p < 1 else 0)))
    kx = -420 + 760 * ease((tl - 0.2) / 1.6)
    running = 0.2 < tl < 1.8
    board_on = tl > 7.6
    if not board_on:
        img.alpha_composite(khoya(walk=tl * 14 if running else None, blink=blinking(t), ticket=tl > 2.2),
                            (int(kx), 1080 + (int(10 * abs(math.sin(tl * 14))) if running else 0)))
    else:
        q = ease((tl - 7.6) / 0.6)
        k = khoya(walk=tl * 14).resize((int(440 * (1 - 0.3 * q)), int(620 * (1 - 0.3 * q))))
        img.alpha_composite(k, (int(kx + 140 * q), int(1080 - 200 * q)))
    return img


def scene4(t):
    tl = t - T_S4
    img = BG_INT.copy()
    interior(img, t)
    ce = ease((tl - 0.3) / 1.0)
    angry = 1.0 if tl > 5.4 else 0.0
    img.alpha_composite(controller(talk(tl, 1.4, 1.2) + talk(tl, 5.6, 1.4), angry, blinking(t, 2), point=tl > 5.4),
                        (int(1100 - 460 * ce), 1040))
    shock = tl > 7.6
    img.alpha_composite(khoya(talk(tl, 3.5, 0.8), shock=shock, ticket=tl > 3.2, blink=blinking(t)), (30, 1040))
    pop_in(img, B["ctl1"], 1040, 1020, tl, 1.4, 3.3, anchor="br")
    pop_in(img, B["k_ecco"], 260, 1020, tl, 3.5, 5.3)
    pop_in(img, B["ctl2"], 1040, 1020, tl, 5.6, 7.7, anchor="br")
    pop_in(img, B["huh"], 220, 900, tl, 7.8, 9.5)
    return img


def hook(t):
    img = Image.new("RGBA", (W, H), (12, 14, 30, 255))
    d = ImageDraw.Draw(img)
    for k in range(40):
        rnd = random.Random(k)
        x, y = rnd.uniform(0, W), (rnd.uniform(0, H) + t * 60 * rnd.uniform(0.3, 1)) % H
        d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(255, 255, 255, 120))
    a, s = appear(t, 0.1)
    txt(img, "مغربي جديد\nفإيطاليا", W / 2, 400, 130, WHITE, a, s)
    a, s = appear(t, 0.6)
    if a > 0.01:
        lv = Image.new("RGBA", (820, 150), (0, 0, 0, 0)); dl = ImageDraw.Draw(lv)
        dl.rounded_rectangle((0, 0, 819, 149), 30, fill=RED + (255,), outline=YELLOW + (255,), width=8)
        dl.text((410, 72), "LEVEL 1: LA STAZIONE", font=font(64), fill=WHITE + (255,), anchor="mm")
        paste_c(img, lv, W / 2, 700, s)
    img.alpha_composite(khoya(blink=blinking(t)), (320, 820 + int(30 * (1 - ease((t - 0.4) / 0.5)))))
    if t > 1.5 and (t * 2.5) % 1 < 0.65:
        txt(img, "PRESS START", W / 2, 1560, 64, YELLOW, 1, 1, shadow=False)
    return img


def cliff(t):
    tl = t - T_CL
    base = scene4(T_CL - 0.01).convert("L").convert("RGBA")
    img = Image.blend(scene4(T_CL - 0.01), base, ease(tl / 0.4))
    img.alpha_composite(Image.new("RGBA", (W, H), (60, 0, 0, int(150 * ease(tl / 0.4)))))
    if tl > 0.3:
        q = ease((tl - 0.3) / 0.25)
        stamp = Image.new("RGBA", (760, 260), (0, 0, 0, 0)); ds = ImageDraw.Draw(stamp)
        ds.rounded_rectangle((0, 0, 759, 259), 30, outline=(255, 60, 60, 255), width=16)
        ds.text((380, 125), "MULTA?!", font=font(170), fill=(255, 60, 60, 255), anchor="mm")
        stamp = stamp.rotate(-8, expand=True, resample=Image.BICUBIC)
        paste_c(img, stamp, W / 2, 620, 2.2 - 1.2 * q)
    a, s = appear(tl, 1.1)
    txt(img, "واش غادي يخلص\nالمخالفة؟", W / 2, 960, 100, WHITE, a, s)
    a, s = appear(tl, 2.6, 0.5)
    txt(img, "يتبع...", W / 2, 1230, 150, YELLOW, a, s)
    if tl > 4.6:
        img.alpha_composite(Image.new("RGBA", (W, H), (10, 12, 24, int(235 * ease((tl - 4.6) / 0.3)))))
        a, s = appear(tl, 4.8, 0.45)
        if LOGO is not None:
            paste_c(img, LOGO_BIG, W / 2, 600, s)
        txt(img, "تابعني", W / 2, 920, 160, WHITE, a, s)
        a, s = appear(tl, 5.2)
        txt(img, "باش تشوف الحلقة 2", W / 2, 1160, 86, YELLOW, a, s)
    return img


def frame(t):
    if t < T_S1:
        return hook(t)
    if t < T_S2:
        img = scene1(t)
    elif t < T_S3:
        img = scene2(t)
    elif t < T_S4:
        img = scene3(t)
    elif t < T_CL:
        img = scene4(t)
        if t >= ZOOM_T:  # dramatic zoom on the controller
            z = 1 + 0.18 * ease((t - ZOOM_T) / 0.35) * (1 - ease((t - ZOOM_T - 2.2) / 0.5))
            if z > 1.001:
                cx, cy = 760, 1250
                w2, h2 = W / z, H / z
                x0 = clamp(cx - w2 / 2, 0, W - w2); y0 = clamp(cy - h2 / 2, 0, H - h2)
                img = img.crop((int(x0), int(y0), int(x0 + w2), int(y0 + h2))).resize((W, H), Image.BILINEAR)
            if t < ZOOM_T + 0.5:
                img.alpha_composite(Image.new("RGBA", (W, H), (255, 0, 0, int(90 * (1 - (t - ZOOM_T) / 0.5)))))
    else:
        img = cliff(t)
        if t - T_CL < 4.6:
            hud(img, t)
        return img
    # scene transitions (quick slide-in)
    for ts in (T_S1, T_S2, T_S3, T_S4):
        if ts <= t < ts + 0.3:
            img.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (1 - (t - ts) / 0.3)))))
    unlock(img, t)
    hud(img, t)
    return img


if "--preview" in sys.argv:
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    ts = [2.5, 5.0, 7.2, 10.0, 13.5, 16.5, 18.0, 19.8, 22.5, 26.0, 29.5, 31.8, 35.2, 37.0, 39.0, 41.5, 44.5, 48.0, 50.5, 54.5]
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

# ------------------------------------------------------------------ audio: chiptune + game sfx
sr = 44100; n = sr * DUR; ta = np.arange(n) / sr
rng = np.random.default_rng(11)
mus = np.zeros(n); sfx = np.zeros(n)


def add(buf, sig, at):
    i0 = int(at * sr)
    if 0 <= i0 < n:
        e = min(n, i0 + len(sig)); buf[i0:e] += sig[:e - i0]


def env(dur, k):
    tt = np.arange(int(dur * sr)) / sr
    return tt, np.exp(-tt * k)


def sq(f, tt, duty=0.5):
    return np.where((tt * f) % 1 < duty, 1.0, -1.0)


def note(m):
    return 440 * 2 ** ((m - 69) / 12)


S16 = 0.125  # 120 bpm sixteenths
mel = [72, 76, 79, 76, 74, 77, 81, 77, 72, 76, 79, 84, 83, 79, 74, 71]
bas = [48, 48, 53, 53, 48, 48, 55, 55]
k = 0; t0 = 0.0
while t0 < ZOOM_T:
    tt, e = env(0.11, 18)
    add(mus, sq(note(mel[k % 16]), tt, 0.25) * e * 0.05, t0)
    if k % 2 == 0:
        tt, e = env(0.22, 8); add(mus, sq(note(bas[(k // 8) % 8]), tt) * e * 0.06, t0)
    if k % 4 == 0:
        tt, e = env(0.12, 30); add(mus, np.sin(2 * np.pi * np.cumsum(50 + 100 * np.exp(-tt * 40)) / sr) * e * 0.4, t0)
    if k % 4 == 2:
        tt, e = env(0.06, 70); add(mus, rng.normal(0, 1, len(tt)) * e * 0.06, t0)
    k += 1; t0 += S16
# suspense after the zoom: low pulse
for b in range(int((DUR - ZOOM_T) / 0.6)):
    tt, e = env(0.5, 5); add(mus, np.sin(2 * np.pi * 55 * tt) * e * 0.35, ZOOM_T + 0.8 + b * 0.6)
mus = mus / np.abs(mus).max() * 0.5
fade_m = np.ones(n); fade_m[int(ZOOM_T * sr):int((ZOOM_T + 0.05) * sr)] = np.linspace(1, 0.4, int(0.05 * sr))
fade_m[int((ZOOM_T + 0.05) * sr):] = 0.4


def arp(notes, step=0.06, k=12, amp=0.08, duty=0.5):
    total = step * len(notes) + 0.3
    out = np.zeros(int(total * sr))
    for j, m in enumerate(notes):
        tt, e = env(0.3, k)
        i0 = int(j * step * sr); seg = sq(note(m), tt, duty) * e * amp
        out[i0:i0 + len(seg)] += seg[:len(out) - i0]
    return out


coin = arp([76, 81, 88], 0.07, 10, 0.1)
unlock_sfx = arp([72, 76, 79, 84, 88], 0.06, 9, 0.08)
blip = arp([84], 0.05, 30, 0.05)
dun = arp([52, 51, 47], 0.45, 2.5, 0.16, 0.5)
tt = np.arange(int(1.6 * sr)) / sr
horn = (np.sin(2 * np.pi * 330 * tt) + np.sin(2 * np.pi * 415 * tt)) * 0.12 * np.clip(tt / 0.05, 0, 1) * np.clip((1.6 - tt) / 0.2, 0, 1)
tt = np.arange(int(3.0 * sr)) / sr
rumble = np.convolve(rng.normal(0, 1, len(tt)), np.ones(60) / 60, "same") * 0.5 * np.clip(tt / 0.5, 0, 1) * np.clip((3 - tt) / 0.8, 0, 1)
tt, e = env(0.5, 6); stampsfx = (np.sin(2 * np.pi * np.cumsum(120 * np.exp(-tt * 8) + 40) / sr) * 0.8 + rng.normal(0, 1, len(tt)) * 0.2) * e
add(sfx, arp([60, 64, 67, 72], 0.1, 8, 0.1), 0.6)
for tt0 in (T_S2 + 0.8, T_S2 + 3.3, T_S2 + 7.0, T_S4 + 1.4, T_S4 + 3.5):
    add(sfx, blip, tt0)
for tt0 in (T_S1 + 2.9, T_S2 + 5.3, T_S4 + 7.8):
    add(sfx, arp([79, 84], 0.08, 14, 0.06), tt0)
for (t0u, *_r) in UNLOCKS:
    add(sfx, unlock_sfx, t0u + 0.4); add(sfx, coin, t0u + 1.2)
add(sfx, horn, T_S3 + 0.4); add(sfx, rumble, T_S3 + 0.5)
add(sfx, dun, ZOOM_T)
add(sfx, stampsfx, T_CL + 0.3)
add(sfx, arp([67, 63, 60, 55], 0.12, 8, 0.08), T_CL + 0.9)
add(sfx, arp([60, 64, 67, 72, 76], 0.08, 8, 0.08), T_CL + 4.8)


def write(path, sig):
    sig = sig * np.clip(ta / 0.05, 0, 1) * np.clip((DUR - ta) / 1.0, 0, 1)
    pcm = (np.repeat(np.clip(sig, -0.95, 0.95)[:, None], 2, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())


for path_out, sig in ((OUT, mus * 0.7 * fade_m + sfx), (OUT.replace(".mp4", "_no_music.mp4"), sfx)):
    write(TMPA, sig)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", TMPV, "-i", TMPA, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "160k", "-shortest", "-movflags", "+faststart", path_out], check=True)
os.remove(TMPV); os.remove(TMPA)
print("done", DUR, "s")
