"""Viral short: decoding Italian text-message slang (cmq, nn, xké, sn, dmn, tvb).

Usage: python3 make_sms_reel.py OUT.mp4 [--preview]
"""
import math, os, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FB, FS = os.path.join(HERE, "Cairo-Black.ttf"), os.path.join(HERE, "Cairo-SemiBold.ttf")
W, H, FPS = 1080, 1920, 30
GREEN, RED, WHITE = (0, 150, 75), (215, 40, 50), (255, 255, 255)
YELLOW, DARK = (255, 214, 90), (30, 32, 42)

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



MSG = "Ciao! cmq nn vengo stasera xké sn stanco. Ci vediamo dmn, tvb"
TOKENS = [  # abbreviation, full Italian, Arabic
    ("cmq", "comunque", "على كل حال"),
    ("nn", "non", "لا"),
    ("xké", "perché", "لأن"),
    ("sn", "sono", "أنا"),
    ("dmn", "domani", "غداً"),
    ("tvb", "ti voglio bene", "أحبك؟!"),
]
T_NOTIF, T_MSG, T_DEC = 0.4, 3.0, 4.6
DSTEP = 2.2
T_SHOCK = T_DEC + 6 * DSTEP          # 17.8
T_CALM = T_SHOCK + 1.6
T_FACT = T_CALM + 2.2
T_TRANS = T_FACT + 3.8
T_OUT = T_TRANS + 3.6
DUR = int(math.ceil(T_OUT + 3.4))

LOGO = None
_lp = os.path.join(HERE, "logo", "ciao_khoya_watermark.png")
if os.path.exists(_lp):
    _L = Image.open(_lp).convert("RGBA")
    LOGO = _L.resize((140, int(_L.height * 140 / _L.width)), Image.LANCZOS)
    LOGO_BIG = _L.resize((340, int(_L.height * 340 / _L.width)), Image.LANCZOS)


def make_bg():
    tt = (np.arange(H, dtype=np.float32) / (H - 1))[:, None, None]
    a = np.broadcast_to(np.array((40, 30, 90), np.float32) * (1 - tt) + np.array((10, 10, 30), np.float32) * tt, (H, W, 3))
    img = Image.fromarray(a.astype(np.uint8)).convert("RGBA")
    lay = Image.new("RGBA", (W // 4, H // 4), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for cx, cy, r, c in ((60, 80, 90, (255, 90, 160, 70)), (220, 300, 110, (60, 160, 255, 60)), (120, 420, 80, (255, 214, 90, 40))):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=c)
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(30)).resize((W, H), Image.BILINEAR))
    for i, c in enumerate(((0, 146, 70), WHITE, (206, 43, 55))):
        ImageDraw.Draw(img).rectangle((i * W / 3, 0, (i + 1) * W / 3, 12), fill=c + (255,))
    return img


BG = make_bg()
PX, PY, PW, PH = 110, 330, 860, 880   # phone (top part)


def flag_circle(d, cx, cy, r):
    for i, c in enumerate(((0, 146, 70), WHITE, (206, 43, 55))):
        d.pieslice((cx - r, cy - r, cx + r, cy + r), 90 + 120 * i, 210 + 120 * i, fill=c + (255,))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=WHITE + (255,), width=4)


def phone(t, state, shake=0.0):
    im = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, PW - 1, PH + 80), 80, fill=(18, 18, 24, 255))
    d.rounded_rectangle((22, 22, PW - 23, PH + 60), 62, fill=(236, 229, 218, 255))
    d.rounded_rectangle((PW / 2 - 80, 34, PW / 2 + 80, 66), 16, fill=(18, 18, 24, 255))
    d.rectangle((22, 90, PW - 23, 210), fill=(32, 110, 100, 255))
    flag_circle(d, 100, 150, 40)
    d.text((165, 128), "Marco", font=font(48), fill=WHITE + (255,), anchor="lm")
    d.text((165, 178), "online", font=font(30, False), fill=(200, 240, 225, 255), anchor="lm")
    # message bubble with token states
    if t >= T_MSG:
        a = ease((t - T_MSG) / 0.35)
        words = MSG.split(" ")
        f = font(50); fb = font(50)
        x0, y0, maxw = 70, 270, PW - 170
        x, y = x0 + 30, y0 + 40
        lh = 74
        lines = [[]]
        lw = 0
        for wd in words:
            core = wd.rstrip("!,.")
            tok = next((k for k, tk in enumerate(TOKENS) if tk[0] == core), None)
            shown = wd
            if tok is not None and state.get(tok, 0) >= 1:
                shown = wd.replace(core, TOKENS[tok][1])
            wdw = d.textlength(shown + " ", font=f)
            if lw + wdw > maxw and lines[-1]:
                lines.append([]); lw = 0
            lines[-1].append((wd, shown, tok)); lw += wdw
        bh = 40 + len(lines) * lh + 30
        bw = maxw + 60
        bub = Image.new("RGBA", (bw + 30, bh + 10), (0, 0, 0, 0)); db = ImageDraw.Draw(bub)
        db.rounded_rectangle((20, 0, bw + 20, bh), 34, fill=(255, 255, 255, 255))
        db.polygon([(20, 20), (0, 0), (40, 0)], fill=(255, 255, 255, 255))
        yy_ = 40 + lh / 2
        for ln in lines:
            xx_ = 50
            for wd, shown, tok in ln:
                core = wd.rstrip("!,.")
                ww = db.textlength(shown, font=f)
                if tok is not None:
                    st = state.get(tok, 0)
                    if st >= 1:
                        db.rounded_rectangle((xx_ - 6, yy_ - 34, xx_ + ww + 6, yy_ + 34), 12, fill=(200, 245, 215, 255))
                        db.text((xx_, yy_), shown, font=fb, fill=GREEN + (255,), anchor="lm")
                    else:
                        hl = (255, 236, 150, 255) if st == 0 else (255, 214, 90, 255)
                        db.rounded_rectangle((xx_ - 6, yy_ - 34, xx_ + ww + 6, yy_ + 34), 12, fill=hl)
                        db.text((xx_, yy_), shown, font=fb, fill=(150, 60, 0, 255), anchor="lm")
                else:
                    db.text((xx_, yy_), shown, font=f, fill=DARK + (255,), anchor="lm")
                xx_ += ww + db.textlength(" ", font=f)
            yy_ += lh
        db.text((bw - 10, bh - 22), "21:47", font=font(26, False), fill=(140, 140, 150, 255), anchor="rm")
        bub.putalpha(Image.fromarray((np.asarray(bub.getchannel("A"), np.float32) * a).astype(np.uint8)))
        im.alpha_composite(bub, (x0 - 20, int(y0 + (1 - a) * 40)))
    # notification banner
    if T_NOTIF <= t < T_MSG + 0.3:
        p = ease((t - T_NOTIF) / 0.35) * (1 - ease((t - T_MSG) / 0.3))
        y = -140 + 230 * p
        nb = Image.new("RGBA", (PW - 80, 150), (0, 0, 0, 0)); dn = ImageDraw.Draw(nb)
        dn.rounded_rectangle((0, 0, PW - 81, 149), 36, fill=(250, 250, 252, 245))
        flag_circle(dn, 70, 75, 34)
        dn.text((130, 50), "Marco", font=font(40), fill=DARK + (255,), anchor="lm")
        dn.text((130, 105), "Ciao! cmq nn vengo stasera xké…", font=font(34, False), fill=(90, 90, 100, 255), anchor="lm")
        im.alpha_composite(nb, (40, int(y)))
    return im


def decoder(img, k, tl):
    ab, full, ar = TOKENS[k]
    a, s = appear(tl, 0.0, 0.3)
    fade = 1 - ease((tl - (DSTEP - 0.25)) / 0.25) if k < 5 else 1.0
    card = Image.new("RGBA", (940, 400), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, 939, 399), 46, fill=(14, 16, 34, 240), outline=YELLOW + (255,), width=5)
    d.text((470, 50), f"فك الشيفرة {k + 1}/6", font=font(36, False), fill=(180, 180, 210, 255), anchor="mm", direction="rtl")
    d.text((470, 125), ab, font=font(84), fill=YELLOW + (255,), anchor="mm")
    # scramble -> full word
    rnd = random.Random(int(tl * 25) + k * 100)
    prog = clamp((tl - 0.35) / 0.7)
    n = len(full)
    shown = "".join(c if (i < prog * n or c == " ") else rnd.choice("abcdefghilmnopqrstuvz") for i, c in enumerate(full))
    d.text((470, 235), "↓", font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44), fill=(180, 180, 210, 255), anchor="mm") if False else None
    d.text((470, 225), shown, font=font(fit(full, 90, 860)), fill=((90, 230, 140) if prog >= 1 else (160, 170, 200)) + (255,), anchor="mm")
    if prog >= 1:
        q = ease((tl - 1.05) / 0.3)
        d.text((470, 330), ar, font=font(72), fill=WHITE + (int(255 * q),), anchor="mm", direction="rtl")
    card.putalpha(Image.fromarray((np.asarray(card.getchannel("A"), np.float32) * a * fade).astype(np.uint8)))
    paste_c(img, card, W / 2, 1420, 0.9 + 0.1 * s)


def emoji_face(r, shock=True):
    im = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=(255, 205, 60, 255))
    for x in (0.65, 1.35):
        d.ellipse((r * x - r * .18, r * .62, r * x + r * .18, r * 1.0), fill=WHITE + (255,), outline=(60, 40, 20, 255), width=4)
        d.ellipse((r * x - r * .07, r * .74, r * x + r * .07, r * .88), fill=(60, 40, 20, 255))
    d.ellipse((r * .8, r * 1.25, r * 1.2, r * 1.7), fill=(120, 40, 30, 255))
    return im


def heart(size, col=(230, 50, 80)):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    r = size / 4
    d.ellipse((0, 0, 2 * r, 2 * r), fill=col + (255,)); d.ellipse((2 * r, 0, 4 * r, 2 * r), fill=col + (255,))
    d.polygon([(0, r * 1.2), (size, r * 1.2), (size / 2, size * 0.95)], fill=col + (255,))
    return im


FACE = emoji_face(110)
HEART = heart(120)


def frame(t):
    img = BG.copy()
    state = {}
    for k in range(6):
        t0 = T_DEC + k * DSTEP
        if t >= t0 + 1.05:
            state[k] = 1
        elif t >= t0:
            state[k] = 0.5
    shake = 0.0
    if T_NOTIF <= t < T_NOTIF + 0.6:
        shake = 10 * math.sin(t * 90)
    if T_SHOCK <= t < T_SHOCK + 0.7:
        shake = 18 * math.sin(t * 80)
    if t < T_FACT:
        ph = phone(t, state)
        img.alpha_composite(ph, (int(PX + shake), PY))
    # top caption
    if t < T_DEC:
        a, s = appear(t, 0.1)
        txt(img, "صديقك الإيطالي أرسل لك\nهذه الرسالة…", W / 2 - 60, 180, 62, WHITE, a, s)
        a, s = appear(t, 1.6)
        txt(img, "هل فهمت شيئاً؟", W / 2, 1420, 110, YELLOW, a, s)
    elif t < T_SHOCK:
        k = int((t - T_DEC) // DSTEP)
        txt(img, "لنفك الشيفرة!", W / 2, 170, 72, YELLOW)
        decoder(img, k, t - T_DEC - k * DSTEP)
    elif t < T_FACT:
        decoder(img, 5, t - T_DEC - 5 * DSTEP)
        if t < T_CALM:
            img.alpha_composite(Image.new("RGBA", (W, H), (200, 0, 30, int(90 * (1 - ease((t - T_SHOCK) / 0.6))))))
            a, s = appear(t, T_SHOCK, 0.3)
            paste_c(img, FACE, W / 2, 210, s)
        else:
            a, s = appear(t, T_CALM, 0.35)
            txt(img, "اهدأ! بين الأصدقاء\nمعناها: أعزّك", W / 2 - 60, 180, 62, WHITE, a, s)
            hb = 1 + 0.1 * abs(math.sin((t - T_CALM) * 6))
            paste_c(img, HEART, W / 2, 1720, hb * s)
    elif t < T_TRANS:
        tl = t - T_FACT
        img.alpha_composite(Image.new("RGBA", (W, H), (10, 10, 30, int(200 * ease(tl / 0.3)))))
        a, s = appear(tl, 0.1)
        txt(img, "لماذا؟", W / 2, 420, 110, WHITE, a, s)
        txt(img, "x = per", W / 2, 580, 130, YELLOW, a, s)
        a, s = appear(tl, 0.8)
        txt(img, "2 × 3", W / 2, 820, 170, WHITE, a, s)
        a, s = appear(tl, 1.4)
        txt(img, "due PER tre", W / 2, 1030, 120, (90, 230, 140), a, s)
        a, s = appear(tl, 2.0)
        txt(img, "لأن علامة الضرب تُقرأ:", W / 2, 1230, 72, WHITE, a, s)
        a, s = appear(tl, 2.4)
        txt(img, "PER", W / 2, 1390, 140, (90, 230, 140), a, s)
    elif t < T_OUT:
        tl = t - T_TRANS
        a, s = appear(tl, 0.1)
        txt(img, "الترجمة الكاملة:", W / 2, 420, 84, YELLOW, a, s)
        card = Image.new("RGBA", (960, 640), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
        d.rounded_rectangle((0, 0, 959, 639), 46, fill=(255, 255, 255, 245))
        it_lines = ["Ciao! Comunque non vengo stasera", "perché sono stanco.", "Ci vediamo domani, ti voglio bene."]
        for i, ln in enumerate(it_lines):
            d.text((480, 80 + i * 70), ln, font=font(fit(it_lines[0], 50, 900)), fill=GREEN + (255,), anchor="mm")
        d.line((80, 320, 880, 320), fill=(0, 0, 0, 40), width=3)
        ar_lines = ["مرحباً! على كل حال لن آتي الليلة", "لأنني متعب.", "نلتقي غداً، أعزّك."]
        for i, ln in enumerate(ar_lines):
            d.text((480, 390 + i * 74), ln, font=font(fit(ar_lines[0], 54, 900)), fill=DARK + (255,), anchor="mm", direction="rtl")
        a2, s2 = appear(tl, 0.4)
        card.putalpha(Image.fromarray((np.asarray(card.getchannel("A"), np.float32) * a2).astype(np.uint8)))
        paste_c(img, card, W / 2, 900, 0.92 + 0.08 * s2)
    else:
        tl = t - T_OUT
        a, s = appear(tl, 0.05)
        txt(img, "هل أرسل لك إيطالي tvb؟", W / 2, 520, fit("هل أرسل لك إيطالي tvb؟", 88, W - 100), WHITE, a, s)
        a, s = appear(tl, 0.4)
        txt(img, "اكتب في التعليقات", W / 2, 680, 80, YELLOW, a, s)
        a, s = appear(tl, 0.9, 0.45)
        if LOGO is not None:
            paste_c(img, LOGO_BIG, W / 2, 1000, s)
        txt(img, "تابعنا لتتعلم الإيطالية بالعربي", W / 2, 1260, fit("تابعنا لتتعلم الإيطالية بالعربي", 72, W - 120), WHITE, a, s)
    if LOGO is not None and t < T_OUT:
        img.alpha_composite(LOGO, (W - LOGO.width - 30, 30)) if t >= T_DEC or True else None
    return img


if "--preview" in sys.argv:
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    ts = [1.2, 3.8, T_DEC + 1.6, T_DEC + 2 * DSTEP + 1.6, T_DEC + 5 * DSTEP + 1.5, T_SHOCK + 0.3, T_CALM + 1.0,
          T_FACT + 2.6, T_TRANS + 2.0, T_OUT + 2.0]
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

# ------------------------------------------------------------------ audio
sr = 44100; n = sr * DUR; ta = np.arange(n) / sr
rng = np.random.default_rng(12)
mus = np.zeros(n); sfx = np.zeros(n)


def add(buf, sig, at):
    i0 = int(at * sr)
    if 0 <= i0 < n:
        e = min(n, i0 + len(sig)); buf[i0:e] += sig[:e - i0]


def env(dur, k):
    tt = np.arange(int(dur * sr)) / sr
    return tt, np.exp(-tt * k)


beat = 0.6
chords = [(220, 277.2, 329.6), (196, 246.9, 293.7), (174.6, 220, 261.6), (164.8, 207.7, 246.9)]
for b in range(int(DUR / beat)):
    t0 = b * beat; bar = (b // 4) % 4
    tt, e = env(0.3, 14); add(mus, np.sin(2 * np.pi * np.cumsum(45 + 70 * np.exp(-tt * 30)) / sr) * e * 0.5, t0)
    if b % 4 in (1, 3):
        tt, e = env(0.12, 30); add(mus, np.diff(rng.normal(0, 1, len(tt) + 1)) * e * 0.08, t0)
    tt, e = env(0.05, 80); add(mus, np.diff(rng.normal(0, 1, len(tt) + 1)) * e * 0.025, t0 + beat / 2)
    if b % 4 == 0:
        tt, e = env(2.4, 1.2); add(mus, sum(np.sin(2 * np.pi * f * tt) for f in chords[bar]) * e * 0.035, t0)
mus = mus / np.abs(mus).max() * 0.45
duck = np.ones(n); duck[int(T_SHOCK * sr):int((T_SHOCK + 1.2) * sr)] = 0.15

tt, e = env(0.35, 8)
notif = (np.sin(2 * np.pi * 1046.5 * tt) * (tt < 0.12) + np.sin(2 * np.pi * 1568 * tt) * (tt >= 0.12)) * e * 0.25
tt = np.arange(int(0.6 * sr)) / sr
buzz = np.sign(np.sin(2 * np.pi * 150 * tt)) * 0.08 * (np.sin(2 * np.pi * 8 * tt) > 0)
tt, e = env(0.03, 100); tick = np.sign(np.sin(2 * np.pi * 1800 * tt)) * e * 0.04
tt, e = env(0.6, 6); ding = (np.sin(2 * np.pi * 1318.5 * tt) + 0.6 * np.sin(2 * np.pi * 1975.5 * tt)) * e * 0.18
tt = np.arange(int(0.5 * sr)) / sr
scratch = np.sin(2 * np.pi * np.cumsum(900 * np.exp(-tt * 5) + 100) / sr) * np.exp(-tt * 4) * 0.25 + rng.normal(0, 1, len(tt)) * np.exp(-tt * 8) * 0.1
tt, e = env(0.8, 4)
aww = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * 3) * (tt >= dl) for f, dl in ((523.3, 0), (659.3, .1), (784, .2))) * 0.12
add(sfx, buzz, T_NOTIF); add(sfx, notif, T_NOTIF + 0.1); add(sfx, notif, T_MSG)
for k in range(6):
    t0 = T_DEC + k * DSTEP
    for j in range(18):
        add(sfx, tick, t0 + 0.35 + j * 0.04)
    add(sfx, ding, t0 + 1.05)
add(sfx, scratch, T_SHOCK); add(sfx, aww, T_CALM); add(sfx, ding, T_FACT + 1.4); add(sfx, notif, T_TRANS); add(sfx, ding, T_OUT + 0.9)


def write(path, sig):
    sig = sig * np.clip(ta / 0.05, 0, 1) * np.clip((DUR - ta) / 0.8, 0, 1)
    pcm = (np.repeat(np.clip(sig, -0.95, 0.95)[:, None], 2, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())


for path_out, sig in ((OUT, mus * 0.7 * duck + sfx), (OUT.replace(".mp4", "_no_music.mp4"), sfx)):
    write(TMPA, sig)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", TMPV, "-i", TMPA, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "160k", "-shortest", "-movflags", "+faststart", path_out], check=True)
os.remove(TMPV); os.remove(TMPA)
print("done", DUR, "s")
