"""Comedy reel: Moroccan mom VS Italian mamma (learn Italian through humor).

Usage: python3 make_mamma_reel.py OUT.mp4 [--preview]
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FB, FS = os.path.join(HERE, "Cairo-Black.ttf"), os.path.join(HERE, "Cairo-SemiBold.ttf")
W, H, FPS = 1080, 1920, 30
GREEN, RED, WHITE = (0, 146, 70), (206, 43, 55), (255, 255, 255)
YELLOW, ORANGE, DARK = (255, 214, 90), (232, 118, 18), (28, 30, 40)

# situation (Darija), Moroccan mom (Darija), Italian mamma (Italian), Darija translation of the Italian
SCENES = [
    ("ملي كترجع معطل للدار", "فين كنتي حتى\nلهاد الساعة؟!", "Dove sei stato fino a quest'ora?!", "فين كنتي حتى لهاد الساعة؟!"),
    ("ملي ما كتكملش الماكلة", "كول! ولّيتي\nغير العظم!", "Mangia! Sei pelle e ossa!", "كول! ولّيتي جلد وعظم!"),
    ("ملي غادي تخرج والجو بارد", "لبس الجاكيط،\nراه البرد!", "Mettiti la giacca, fa freddo!", "لبس الجاكيط، راه البرد!"),
    ("ملي كتقول: ما جيعانش", "ما جيعانش؟!\nغير شوية!", "Non hai fame? Solo un pochino!", "ما جيعانش؟ غير شوية!"),
    ("ملي كديرو شي مصيبة", "تسنا حتى\nيجي باك!", "Aspetta che torni papà!", "تسنا حتى يرجع باباك!"),
]
RECAP = [(s[2], s[3]) for s in SCENES]

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
HOOK, SC = 3.6, 7.5
T_MOM, T_MAM = 0.7, 2.9
FIN0 = HOOK + len(SCENES) * SC
REC0 = FIN0 + 4.6
OUT0 = REC0 + 6.4
DUR = int(math.ceil(OUT0 + 5.2))
MID = 960

# ------------------------------------------------------------------ split background
def grad(top, bot, h):
    tt = (np.arange(h, dtype=np.float32) / (h - 1))[:, None, None]
    return np.broadcast_to(np.array(top, np.float32) * (1 - tt) + np.array(bot, np.float32) * tt, (h, W, 3)).copy()


top = grad((178, 86, 52), (118, 46, 34), MID)
bot = grad((0, 104, 82), (0, 52, 48), H - MID)
arr = np.concatenate([top, bot], 0)
yy = np.arange(H, dtype=np.float32)[:, None]; xx = np.arange(W, dtype=np.float32)[None, :]
arr *= (1 - 0.35 * ((xx - W / 2) / W) ** 2 * 2)[..., None]
BG = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA")
TS = 150
PAT = Image.new("RGBA", (W + 2 * TS, H + 2 * TS), (0, 0, 0, 0)); _dp = ImageDraw.Draw(PAT)
for ty in range(0, H + 2 * TS, TS):
    for tx in range(0, W + 2 * TS, TS):
        cx, cy, r = tx + TS / 2, ty + TS / 2, TS * 0.36
        for off in (0, math.pi / 4):
            _dp.polygon([(cx + r * math.cos(a + off), cy + r * math.sin(a + off))
                         for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2)], outline=(255, 255, 255, 24), width=3)
# Italian half: tablecloth checks instead of zellige
CHECK = Image.new("RGBA", (W + 2 * TS, H), (0, 0, 0, 0)); _dc = ImageDraw.Draw(CHECK)
for ty in range(0, H, 60):
    for tx in range(0, W + 2 * TS, 60):
        if (tx // 60 + ty // 60) % 2 == 0:
            _dc.rectangle((tx, ty, tx + 59, ty + 59), fill=(255, 255, 255, 14))


def background(t, shake=0.0):
    img = BG.copy()
    o = int(t * 18) % TS
    img.alpha_composite(PAT.crop((o, o, o + W, o + MID)), (0, 0))
    img.alpha_composite(CHECK.crop((o, 0, o + W, H - MID)), (0, MID))
    d = ImageDraw.Draw(img)
    for i, c in enumerate((GREEN, WHITE, RED)):
        d.rectangle((i * W / 3, H - 14, (i + 1) * W / 3, H), fill=c + (255,))
        d.rectangle((i * W / 3, 0, (i + 1) * W / 3, 14), fill=((193, 39, 45) if i != 1 else (0, 98, 51)) + (255,))
    d.rectangle((0, MID - 4, W, MID + 4), fill=(255, 255, 255, 220))
    return img


# ------------------------------------------------------------------ characters
CW_, CH_ = 440, 580


def eyes(d, angry, blink, y=205, xs=(185, 255)):
    for k, x in enumerate(xs):
        h = 3 if blink else 17
        d.ellipse((x - 11, y - h, x + 11, y + h), fill=(35, 25, 25, 255))
        if not blink:
            d.ellipse((x - 3, y - 9, x + 4, y - 2), fill=(255, 255, 255, 255))
        s = -1 if k == 0 else 1
        tilt = 14 * angry
        d.line((x - 26, y - 34 - s * tilt * 0.5 * (-1), x + 26, y - 34 + s * tilt * 0.5 * (-1)) if False else
               (x - 26 * s, y - 40 + tilt, x + 22 * s, y - 32 - 0 * tilt) if angry > 0.05 else
               (x - 22, y - 36, x + 22, y - 36), fill=(60, 40, 35, 255), width=9)


def mouth(d, talk, cx=220, cy=265, lip=(150, 40, 40)):
    if talk > 0.05:
        h = 6 + 30 * talk
        d.ellipse((cx - 26, cy - h / 2, cx + 26, cy + h / 2), fill=(90, 20, 25, 255), outline=lip + (255,), width=5)
    else:
        d.arc((cx - 26, cy - 22, cx + 26, cy + 10), 20, 160, fill=lip + (255,), width=6)


def moroccan_mom(talk=0.0, angry=0.0, arm=0.0, blink=False, slipper=True):
    im = Image.new("RGBA", (CW_, CH_), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((95, 330, 345, 470), fill=(16, 110, 78, 255))
    d.polygon([(70, CH_), (370, CH_), (330, 400), (110, 400)], fill=(16, 110, 78, 255))
    d.line((220, 360, 220, CH_), fill=(230, 180, 60, 255), width=10)
    for y in range(390, CH_, 40):
        d.ellipse((212, y, 228, y + 16), fill=(230, 180, 60, 255))
    d.ellipse((95, 60, 345, 370), fill=(193, 39, 45, 255))               # scarf
    d.ellipse((140, 125, 300, 305), fill=(205, 155, 115, 255))           # face
    d.chord((128, 92, 312, 210), 180, 360, fill=(193, 39, 45, 255))      # scarf over forehead
    d.ellipse((150, 238, 180, 258), fill=(230, 120, 110, 110)); d.ellipse((260, 238, 290, 258), fill=(230, 120, 110, 110))
    eyes(d, angry, blink)
    mouth(d, talk)
    # raised arm with pointing finger (arm 0..1 = how high)
    sx, sy = 320, 400
    ang = math.radians(-20 - 70 * arm)
    hx, hy = sx + 110 * math.cos(ang), sy + 110 * math.sin(ang)
    d.line((sx, sy, hx, hy), fill=(16, 110, 78, 255), width=46)
    d.ellipse((hx - 26, hy - 26, hx + 26, hy + 26), fill=(205, 155, 115, 255))
    if slipper:
        d.line((hx, hy - 10, hx + 6, hy - 60), fill=(205, 155, 115, 255), width=16)
    return im


def italian_mamma(talk=0.0, angry=0.0, arm=0.0, blink=False, spoon=True):
    im = Image.new("RGBA", (CW_, CH_), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((95, 330, 345, 470), fill=(42, 62, 128, 255))
    d.polygon([(70, CH_), (370, CH_), (330, 400), (110, 400)], fill=(42, 62, 128, 255))
    d.rounded_rectangle((150, 390, 290, CH_ + 20), 30, fill=(250, 250, 250, 255))  # apron
    for y in range(420, CH_, 45):
        for x in (180, 220, 260):
            d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=(206, 43, 55, 255))
    d.ellipse((105, 70, 335, 300), fill=(120, 104, 98, 255))            # hair
    d.ellipse((178, 18, 262, 98), fill=(120, 104, 98, 255))             # bun
    d.ellipse((140, 115, 300, 295), fill=(246, 206, 176, 255))          # face
    for x in range(150, 300, 30):
        d.ellipse((x - 22, 100, x + 22, 142), fill=(120, 104, 98, 255))  # curls
    d.ellipse((150, 238, 180, 258), fill=(240, 130, 120, 110)); d.ellipse((260, 238, 290, 258), fill=(240, 130, 120, 110))
    eyes(d, angry, blink)
    for x in (185, 255):
        d.ellipse((x - 30, 175, x + 30, 235), outline=(50, 50, 60, 255), width=5)
    d.line((215, 200, 225, 200), fill=(50, 50, 60, 255), width=5)
    mouth(d, talk, lip=(200, 30, 50))
    sx, sy = 320, 400
    ang = math.radians(-20 - 70 * arm)
    hx, hy = sx + 110 * math.cos(ang), sy + 110 * math.sin(ang)
    d.line((sx, sy, hx, hy), fill=(42, 62, 128, 255), width=46)
    d.ellipse((hx - 26, hy - 26, hx + 26, hy + 26), fill=(246, 206, 176, 255))
    if spoon:
        d.line((hx, hy, hx + 30, hy - 130), fill=(160, 105, 55, 255), width=14)
        d.ellipse((hx + 12, hy - 185, hx + 58, hy - 115), fill=(175, 118, 62, 255))
    return im


def slipper_img():
    im = Image.new("RGBA", (180, 90), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 10, 180, 85), fill=(225, 190, 60, 255), outline=(150, 110, 30, 255), width=5)  # babouche
    d.chord((60, 5, 170, 80), 180, 360, fill=(240, 210, 90, 255))
    return im


def spoon_img():
    im = Image.new("RGBA", (220, 70), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.line((0, 35, 150, 35), fill=(160, 105, 55, 255), width=16)
    d.ellipse((140, 5, 218, 65), fill=(175, 118, 62, 255))
    return im


SLIP, SPOON = slipper_img(), spoon_img()


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


def bubble(main, sub=None, main_ar=True):
    pad, maxw = 34, 560
    ms = 62 if main_ar else 56
    lm = wrap(main, ms, True, maxw)
    ls = wrap(sub, 40, False, maxw) if sub else []
    wmax = max([measure(x, ms) for x in lm] + [measure(x, 40, False) for x in ls])
    bw = int(wmax + 2 * pad)
    lhm, lhs = int(ms * 1.35), 54
    bh = int(pad + len(lm) * lhm + (20 + len(ls) * lhs if ls else 0) + pad * 0.6)
    im = Image.new("RGBA", (bw + 40, bh), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((40, 0, 40 + bw, bh), 40, fill=(252, 250, 245, 255))
    d.polygon([(42, bh * 0.45), (42, bh * 0.75), (0, bh * 0.75)], fill=(252, 250, 245, 255))
    y = pad * 0.7
    for ln in lm:
        if main_ar:
            d.text((40 + bw - pad, y + lhm / 2), ln, font=font(ms), fill=DARK + (255,), anchor="rm", direction="rtl")
        else:
            d.text((40 + pad, y + lhm / 2), ln, font=font(ms), fill=(0, 110, 60, 255), anchor="lm")
        y += lhm
    if ls:
        d.line((40 + pad, y + 8, 40 + bw - pad, y + 8), fill=(0, 0, 0, 40), width=2)
        y += 20
        for ln in ls:
            d.text((40 + bw - pad, y + lhs / 2), ln, font=font(40, False), fill=(90, 95, 105, 255), anchor="rm",
                   direction="rtl")
            y += lhs
    return with_shadow(im, 14, 8, 100)


MOM_B = [bubble(s[1]) for s in SCENES]
MAM_B = [bubble(s[2], s[3], main_ar=False) for s in SCENES]


def label(img, text, x, y, flag):
    w = measure(text, 40) + 110
    im = Image.new("RGBA", (int(w), 76), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, 75), 38, fill=(0, 0, 0, 120))
    if flag == "ma":
        d.ellipse((14, 14, 62, 62), fill=(193, 39, 45, 255))
        pts = [(38 + 15 * math.sin(2 * math.pi * k / 5), 38 - 15 * math.cos(2 * math.pi * k / 5)) for k in range(5)]
        d.line([pts[(2 * k) % 5] for k in range(6)], fill=(0, 98, 51, 255), width=4)
    else:
        for i, c in enumerate((GREEN, WHITE, RED)):
            d.pieslice((14, 14, 62, 62), 90 + 120 * i, 210 + 120 * i, fill=c + (255,))
    d.text((80, 38), text, font=font(40), fill=WHITE + (255,), anchor="lm", direction="rtl" if is_ar(text) else "ltr")
    img.alpha_composite(im, (x, y))


def banner(img, text, a, s):
    if a <= 0.01:
        return
    fs = fit(text, 58, 860)
    w = measure(text, fs) + 90
    im = Image.new("RGBA", (int(w), 110), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, 109), 55, fill=(20, 24, 34, int(240 * a)), outline=(255, 214, 90, int(255 * a)), width=5)
    d.text((w / 2, 52), text, font=font(fs), fill=YELLOW + (int(255 * a),), anchor="mm", direction="rtl" if is_ar(text) else "ltr")
    paste_c(img, im, W / 2, MID, s)


def talk_amt(tl, t0, dur):
    if t0 <= tl < t0 + dur:
        return 0.5 + 0.5 * abs(math.sin((tl - t0) * 13))
    return 0.0


def blinking(t):
    return (t % 3.1) < 0.12


# character anchor positions (top-left of canvas)
MOM_XY, MAM_XY = (0, MID - CH_ + 10), (0, H - CH_ - 280)


def scene(i, tl):
    t = HOOK + i * SC + tl
    sh = 0.0
    if i == 4 and 4.8 <= tl < 6.6:
        sh = 1.0
    img = background(t)
    d_mom = talk_amt(tl, T_MOM, 1.6); d_mam = talk_amt(tl, T_MAM, 1.8)
    angry = 1.0 if i in (0, 4) else 0.5
    arm_m = 0.4 + 0.6 * abs(math.sin(tl * 7)) if d_mom else 0.2
    arm_i = 0.4 + 0.6 * abs(math.sin(tl * 9)) if d_mam else 0.2
    thrown = i == 4 and tl >= 4.8
    bob_m = 6 * math.sin(t * 3) + (8 * math.sin(tl * 26) if d_mom else 0)
    bob_i = 6 * math.sin(t * 3 + 1) + (8 * math.sin(tl * 26) if d_mam else 0)
    img.alpha_composite(moroccan_mom(d_mom, angry, arm_m, blinking(t), not thrown), (MOM_XY[0], int(MOM_XY[1] + bob_m)))
    img.alpha_composite(italian_mamma(d_mam, angry, arm_i, blinking(t + 1), not thrown),
                        (MAM_XY[0], int(MAM_XY[1] + bob_i)))
    fade = 1 - ease((tl - (SC - 0.4)) / 0.3)
    a, s = appear(tl, T_MOM, 0.3)
    if a > 0.01:
        b = MOM_B[i]
        paste_c(img, b, 420 + b.width / 2, 470, s * fade)
    a, s = appear(tl, T_MAM, 0.3)
    if a > 0.01:
        b = MAM_B[i]
        paste_c(img, b, 420 + b.width / 2, 1290, s * fade)
    a, s = appear(tl, 0.0, 0.35)
    if not (i == 4 and tl >= 4.7):
        banner(img, SCENES[i][0], a * fade, s)
    if thrown:
        p = clamp((tl - 4.8) / 1.1)
        # slipper flies from top mom down to the middle, spoon flies up from bottom mamma
        sx, sy = 330 + 230 * p, 420 + 540 * p - 260 * math.sin(math.pi * p)
        ix, iy = 330 + 230 * p, 1460 - 500 * p - 260 * math.sin(math.pi * p)
        if p < 1:
            img.alpha_composite(SLIP.rotate(-720 * p, expand=True), (int(sx - 100), int(sy - 100)))
            img.alpha_composite(SPOON.rotate(720 * p, expand=True), (int(ix - 110), int(iy - 110)))
        else:
            q = clamp((tl - 5.9) / 0.5)
            burst = Image.new("RGBA", (500, 500), (0, 0, 0, 0)); db = ImageDraw.Draw(burst)
            pts = [(250 + (230 if k % 2 == 0 else 110) * (0.6 + 0.4 * q) * math.cos(k * math.pi / 8),
                    250 + (230 if k % 2 == 0 else 110) * (0.6 + 0.4 * q) * math.sin(k * math.pi / 8)) for k in range(16)]
            db.polygon(pts, fill=YELLOW + (255,), outline=(0, 0, 0, 255))
            img.alpha_composite(burst, (int(560 - 250), int(MID - 250)))
            txt(img, "BONK!", 560, MID - 10, 110, RED, 1, back(q), shadow=False)
    return img


def hook(t):
    img = background(t)
    a, s = appear(t, 0.1)
    img.alpha_composite(moroccan_mom(talk_amt(t, 1.0, 0.8), 0, 0.3, blinking(t)), (MOM_XY[0], int(MOM_XY[1] + (1 - a) * 500)))
    a2, _ = appear(t, 0.35)
    img.alpha_composite(italian_mamma(talk_amt(t, 1.6, 0.8), 0, 0.3, blinking(t + 1)), (MAM_XY[0], int(MAM_XY[1] + (1 - a2) * 600)))
    a, s = appear(t, 0.5)
    txt(img, "مي\nالمغربية", 720, 470, 110, WHITE, a, s)
    a, s = appear(t, 0.8)
    txt(img, "الماما\nالطاليانية", 720, 1290, 110, WHITE, a, s)
    if t < 2.1:
        a, s = appear(t, 1.0)
        dd = ImageDraw.Draw(img)
        r = 95 * s
        if a > 0.01:
            dd.ellipse((W / 2 - r, MID - r, W / 2 + r, MID + r), fill=RED + (255,), outline=WHITE + (255,), width=8)
            txt(img, "VS", W / 2, MID - 8, int(90 * max(s, 0.1)), WHITE, a, 1, shadow=False)
    else:
        a, s = appear(t, 2.1)
        banner(img, "شكون فيهم أخطر؟", a, s)
    return img


def finale(tl):
    t = FIN0 + tl
    img = background(t)
    ov = Image.new("RGBA", (W, H), (20, 10, 20, int(150 * ease(tl / 0.4))))
    img.alpha_composite(ov)
    m = moroccan_mom(talk_amt(tl, 0.3, 1.0), 0, 0.2, blinking(t)).resize((352, 464), Image.LANCZOS)
    i_ = italian_mamma(talk_amt(tl, 0.3, 1.0), 0, 0.2, blinking(t + 1)).resize((352, 464), Image.LANCZOS)
    img.alpha_composite(m, (W // 2 - 352 + 30, 760))
    img.alpha_composite(i_.transpose(Image.FLIP_LEFT_RIGHT), (W // 2 - 30, 760))
    dh = ImageDraw.Draw(img)
    for k in range(9):
        ph = (tl * 0.6 + k / 9) % 1
        x = 200 + (k * 97) % 700 + 25 * math.sin(tl * 3 + k)
        y = 1250 - ph * 700
        r = 26
        al = int(255 * (1 - ph))
        dh.ellipse((x - r, y - r, x, y), fill=(230, 50, 80, al)); dh.ellipse((x, y - r, x + r, y), fill=(230, 50, 80, al))
        dh.polygon([(x - r, y - r / 2), (x + r, y - r / 2), (x, y + r * 0.9)], fill=(230, 50, 80, al))
    a, s = appear(tl, 0.3)
    txt(img, "الماما هي الماما\nفكل بلاد", W / 2, 400, 110, WHITE, a, s)
    a, s = appear(tl, 1.0)
    pill = "La mamma è sempre la mamma"
    banner(img, pill, a, s) if False else None
    if a > 0.01:
        fs = fit(pill, 58, 900)
        w = measure(pill, fs) + 80
        im = Image.new("RGBA", (int(w), 110), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, w - 1, 109), 55, fill=(0, 120, 70, int(255 * a)))
        d.text((w / 2, 52), pill, font=font(fs), fill=WHITE + (int(255 * a),), anchor="mm")
        paste_c(img, im, W / 2, 640, s)
    a, s = appear(tl, 1.8)
    txt(img, "تاگ خوك ولا ختك", W / 2, 1400, 84, YELLOW, a, s)
    return img


def recap(tl):
    img = background(REC0 + tl)
    img.alpha_composite(Image.new("RGBA", (W, H), (10, 14, 24, 200)))
    a, s = appear(tl, 0.1)
    txt(img, "حفظ جمل الماما", W / 2, 220, 96, YELLOW, a, s)
    for k, (it, dar) in enumerate(RECAP):
        p = ease((tl - 0.6 - 0.35 * k) / 0.35)
        if p <= 0.01:
            continue
        r = Image.new("RGBA", (960, 210), (0, 0, 0, 0)); d = ImageDraw.Draw(r)
        d.rounded_rectangle((0, 0, 959, 209), 40, fill=(250, 247, 240, 255))
        d.rounded_rectangle((0, 0, 22, 209), 11, fill=(GREEN if k % 2 == 0 else RED) + (255,))
        d.text((50, 70), it, font=font(fit(it, 56, 870)), fill=(0, 110, 60, 255), anchor="lm")
        d.text((920, 150), dar, font=font(fit(dar, 46, 870, False), False), fill=DARK + (255,), anchor="rm", direction="rtl")
        r.putalpha(Image.fromarray((np.asarray(r.getchannel("A"), np.float32) * p).astype(np.uint8)))
        img.alpha_composite(r, (int(60 + (1 - p) * 200), 340 + k * 240))
    a, s = appear(tl, 2.6)
    txt(img, "سجل الفيديو باش ترجع ليه", W / 2, 1600, 56, WHITE, a, s, bold=False)
    return img


LOGO = None
_lp = os.path.join(HERE, "logo", "ciao_khoya_watermark.png")
if os.path.exists(_lp):
    _L = Image.open(_lp).convert("RGBA")
    LOGO = _L.resize((160, int(_L.height * 160 / _L.width)), Image.LANCZOS)
    LOGO_BIG = _L.resize((400, int(_L.height * 400 / _L.width)), Image.LANCZOS)


def outro(tl):
    img = background(OUT0 + tl)
    img.alpha_composite(Image.new("RGBA", (W, H), (10, 14, 24, 215)))
    a, s = appear(tl, 0.2, 0.45)
    if LOGO is not None:
        paste_c(img, LOGO_BIG, W / 2, 620, s)
    txt(img, "تابعني", W / 2, 940, 170, WHITE, a, s)
    a, s = appear(tl, 0.6)
    txt(img, "باش تتعلم الطاليانية\nبالدارجة", W / 2, 1190, 86, YELLOW, a, s)
    return img


def frame(t):
    if t < HOOK:
        img = hook(t)
    elif t < FIN0:
        i = int((t - HOOK) // SC)
        tl = t - HOOK - i * SC
        img = scene(i, tl)
        if i == 4 and 4.8 <= tl < 6.4:  # screen shake
            dx = int(14 * math.sin(tl * 70)); dy = int(10 * math.cos(tl * 55))
            img = Image.new("RGBA", (W, H), (0, 0, 0, 255)).copy() if False else img.transform(
                img.size, Image.AFFINE, (1, 0, dx, 0, 1, dy), resample=Image.BILINEAR)
    elif t < REC0:
        img = finale(t - FIN0)
    elif t < OUT0:
        img = recap(t - REC0)
    else:
        img = outro(t - OUT0)
    if LOGO is not None and t < OUT0:
        img.alpha_composite(LOGO, (W - LOGO.width - 40, 40))
    return img


if "--preview" in sys.argv:
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    ts = [0.9, 2.8] + [HOOK + k * SC + 4.8 for k in range(4)] + [HOOK + 4 * SC + 4.5, HOOK + 4 * SC + 5.5,
                                                                   HOOK + 4 * SC + 6.3, FIN0 + 2.5, REC0 + 3.5, OUT0 + 2]
    cols = 6
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

# ------------------------------------------------------------------ audio: tarantella + cartoon sfx
sr = 44100; n = sr * DUR; ta = np.arange(n) / sr
rng = np.random.default_rng(9)
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


E8 = 0.17  # eighth note, 6/8
bars = [[69, 72, 76, 81, 76, 72], [67, 71, 74, 79, 74, 71], [65, 69, 72, 77, 72, 69], [64, 68, 71, 76, 71, 68]]
bass = [45, 43, 41, 40]
k = 0; t0 = 0.0
while t0 < DUR:
    bar = (k // 6) % 4; nt = bars[bar][k % 6]
    tt, e = env(0.16, 16)
    f = note(nt)
    add(mus, (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(4 * np.pi * f * tt)) * e * (1 + 0.3 * np.sin(2 * np.pi * 28 * tt)) * 0.07, t0)
    if k % 3 == 0:
        tt, e = env(0.3, 9); add(mus, np.sin(2 * np.pi * note(bass[bar]) * tt) * e * 0.25, t0)
        tt, e = env(0.08, 45); add(mus, np.diff(rng.normal(0, 1, len(tt) + 1)) * e * 0.05, t0)  # tambourine
    k += 1; t0 += E8
mus = mus / np.abs(mus).max() * 0.5

tt, e = env(0.12, 35); pop = np.sin(2 * np.pi * (650 + 500 * np.exp(-tt * 40)) * tt) * e * 0.3
tt = np.arange(int(0.3 * sr)) / sr
whoosh = np.convolve(rng.normal(0, 1, len(tt)), np.ones(12) / 12, "same") * np.sin(np.pi * tt / 0.3) ** 2 * 0.3
tt = np.arange(int(1.1 * sr)) / sr
slide = np.sin(2 * np.pi * np.cumsum(500 + 900 * tt / 1.1) / sr) * 0.18 * np.clip(tt / 0.05, 0, 1)
tt, e = env(0.5, 9); bonk = np.sin(2 * np.pi * np.cumsum(200 * np.exp(-tt * 6) + 60) / sr) * e * 0.7
tt, e = env(0.9, 4)
aww = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * 3) * (tt >= dl) for f, dl in ((523.3, 0), (659.3, .1), (784, .2))) * 0.12


def babble(t0, dur, base):
    tt_ = 0.0
    while tt_ < dur:
        tb, eb = env(0.08, 30)
        f = base * (1 + 0.25 * rng.random())
        add(sfx, np.sign(np.sin(2 * np.pi * f * tb)) * eb * 0.035, t0 + tt_)
        tt_ += 0.09 + 0.05 * rng.random()


add(sfx, whoosh, 0.0); add(sfx, pop, 1.0); add(sfx, whoosh, 2.1)
for i in range(len(SCENES)):
    s0 = HOOK + i * SC
    add(sfx, whoosh, s0)
    add(sfx, pop, s0 + T_MOM); babble(s0 + T_MOM, 1.6, 330)
    add(sfx, pop, s0 + T_MAM); babble(s0 + T_MAM, 1.8, 260)
add(sfx, slide, HOOK + 4 * SC + 4.8); add(sfx, bonk, HOOK + 4 * SC + 5.9)
add(sfx, aww, FIN0 + 0.3); add(sfx, pop, OUT0 + 0.2)


def write(path, sig):
    sig = sig * np.clip(ta / 0.05, 0, 1) * np.clip((DUR - ta) / 1.2, 0, 1)
    pcm = (np.repeat(np.clip(sig, -0.95, 0.95)[:, None], 2, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())


for path_out, sig in ((OUT, mus * 0.6 + sfx), (OUT.replace(".mp4", "_no_music.mp4"), sfx)):
    write(TMPA, sig)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", TMPV, "-i", TMPA, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "160k", "-shortest", "-movflags", "+faststart", path_out], check=True)
os.remove(TMPV); os.remove(TMPA)
print("done", DUR, "s")
