"""Problem-solving short: permesso expired while waiting for renewal -> the ricevuta (Modern Standard Arabic).

Facts (check before posting, rules can change): art. 5 c. 9-bis D.Lgs. 286/1998 - with a renewal request filed
on time and the receipt, the foreign worker may stay and work while waiting, even beyond 60 days, until a contrary
communication from the authorities. A permit expired for more than 60 days with no renewal request = irregular.

Usage: python3 make_ricevuta_reel.py OUT.mp4 [--preview]
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FB, FS = os.path.join(HERE, "Cairo-Black.ttf"), os.path.join(HERE, "Cairo-SemiBold.ttf")
W, H, FPS = 1080, 1920, 30
GREEN, RED, WHITE = (30, 170, 90), (220, 50, 50), (255, 255, 255)
YELLOW, DARK, ORANGE = (255, 200, 50), (26, 28, 38), (240, 140, 30)
NAVY = (18, 30, 56)

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



T_Q, T_YES, T_LINE, T_WITH, T_LAW, T_OUT = 2.8, 5.0, 9.0, 16.0, 21.0, 24.0
DUR = 27

LOGO = None
_lp = os.path.join(HERE, "logo", "ciao_khoya_watermark.png")
if os.path.exists(_lp):
    _L = Image.open(_lp).convert("RGBA")
    LOGO = _L.resize((120, int(_L.height * 120 / _L.width)), Image.LANCZOS)
    LOGO_BIG = _L.resize((300, int(_L.height * 300 / _L.width)), Image.LANCZOS)


def make_bg():
    tt = (np.arange(H, dtype=np.float32) / (H - 1))[:, None, None]
    a = np.broadcast_to(np.array((26, 44, 80), np.float32) * (1 - tt) + np.array((10, 16, 32), np.float32) * tt, (H, W, 3))
    img = Image.fromarray(a.astype(np.uint8)).convert("RGBA")
    for i, c in enumerate(((0, 146, 70), WHITE, (206, 43, 55))):
        ImageDraw.Draw(img).rectangle((i * W / 3, 0, (i + 1) * W / 3, 12), fill=c + (255,))
    return img


BG = make_bg()


def permit_card():
    cw, ch = 760, 470
    c = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, cw - 1, ch - 1), 36, fill=(232, 238, 246, 255), outline=(150, 170, 200, 255), width=4)
    d.rounded_rectangle((0, 0, cw - 1, 90), 36, fill=(40, 90, 150, 255)); d.rectangle((0, 50, cw - 1, 90), fill=(40, 90, 150, 255))
    d.text((cw / 2, 46), "PERMESSO DI SOGGIORNO", font=font(44), fill=WHITE + (255,), anchor="mm")
    d.rounded_rectangle((40, 130, 230, 380), 20, fill=(200, 210, 225, 255))
    d.ellipse((95, 165, 175, 245), fill=(150, 160, 180, 255)); d.chord((70, 250, 200, 400), 180, 360, fill=(150, 160, 180, 255))
    for k, (lab, val) in enumerate((("COGNOME", "———————"), ("NOME", "—————"), ("SCADENZA", "10/10/2026"))):
        d.text((270, 150 + k * 85), lab, font=font(28, False), fill=(110, 120, 140, 255), anchor="lm")
        d.text((270, 188 + k * 85), val, font=font(42), fill=DARK + (255,), anchor="lm")
    return c


def ricevuta():
    cw, ch = 560, 640
    c = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rectangle((0, 0, cw - 1, ch - 1), fill=(255, 250, 225, 255))
    for x in range(0, cw, 28):
        d.polygon([(x, ch - 1), (x + 14, ch - 18), (x + 28, ch - 1)], fill=(0, 0, 0, 0))
    d.rectangle((0, 0, cw - 1, 80), fill=(255, 205, 0, 255))
    d.text((cw / 2, 42), "RICEVUTA", font=font(52), fill=DARK + (255,), anchor="mm")
    for k in range(6):
        d.rounded_rectangle((50, 130 + k * 55, 50 + [420, 300, 380, 260, 400, 220][k], 150 + k * 55), 8, fill=(200, 195, 175, 255))
    rng_ = np.random.default_rng(2)
    x = 60
    while x < cw - 60:
        w_ = int(rng_.integers(3, 12))
        d.rectangle((x, 480, x + w_, 590), fill=DARK + (255,)); x += w_ + int(rng_.integers(4, 10))
    return c


CARD, REC = permit_card(), ricevuta()


def stamp(text_, col):
    im = Image.new("RGBA", (620, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 8, 611, 191), 24, outline=col + (240,), width=14)
    d.text((310, 100), text_, font=font(110), fill=col + (240,), anchor="mm")
    return im.rotate(-10, expand=True, resample=Image.BICUBIC)


SCADUTO = stamp("SCADUTO", RED)


def worried(r):
    im = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=(255, 205, 60, 255))
    for x in (0.65, 1.35):
        d.ellipse((r * x - r * .12, r * .7, r * x + r * .12, r * .98), fill=(60, 40, 20, 255))
        d.line((r * x - r * .22, r * .52 + (r * .08 if x < 1 else -r * .0), r * x + r * .2, r * .58 - (0 if x < 1 else r * .08)), fill=(60, 40, 20, 255), width=6)
    d.arc((r * .6, r * 1.3, r * 1.4, r * 1.8), 200, 340, fill=(60, 40, 20, 255), width=8)
    d.ellipse((r * 1.55, r * .45, r * 1.8, r * .85), fill=(110, 180, 255, 230))
    return im


FACE = worried(90)


def check_row(img, y, text_, a, ok=True):
    if a <= 0.01:
        return
    row = Image.new("RGBA", (940, 150), (0, 0, 0, 0)); d = ImageDraw.Draw(row)
    d.rounded_rectangle((0, 0, 939, 149), 40, fill=(255, 255, 255, 245))
    col = GREEN if ok else ORANGE
    d.ellipse((800, 25, 900, 125), fill=col + (255,))
    if ok:
        d.line([(825, 75), (843, 95), (877, 58)], fill=WHITE + (255,), width=12, joint="curve")
    else:
        d.text((850, 74), "!", font=font(70), fill=WHITE + (255,), anchor="mm")
    d.text((770, 75), text_, font=font(fit(text_, 54, 720)), fill=DARK + (255,), anchor="rm", direction="rtl")
    row.putalpha(Image.fromarray((np.asarray(row.getchannel("A"), np.float32) * a).astype(np.uint8)))
    img.alpha_composite(row, (int(70 + (1 - a) * 200), int(y)))


def timeline(img, tl):
    d = ImageDraw.Draw(img)
    x0, x1, y = 90, 990, 680
    # draw RTL timeline: time flows right -> left (Arabic reading)
    xm = 640            # expiry
    x60 = 330           # +60 days
    p = ease(tl / 1.2)
    xr = x1 - (x1 - x0) * p
    segs = [(x1, xm, GREEN), (xm, x60, ORANGE), (x60, x0, RED)]
    for a_, b_, col in segs:
        if xr < a_:
            d.rounded_rectangle((max(b_, xr), y - 22, a_, y + 22), 22, fill=col + (255,))
    rows = [
        (0.4, "قبل انتهاء الإقامة", "قدّم طلب التجديد", GREEN),
        (1.4, "حتى 60 يوماً بعد الانتهاء", "ما زال ممكناً", ORANGE),
        (2.4, "أكثر من 60 يوماً بدون طلب", "وضع غير قانوني", RED),
    ]
    for k, (t0, l1, l2, col) in enumerate(rows):
        a = ease((tl - t0) / 0.35)
        if a <= 0.01:
            continue
        row = Image.new("RGBA", (940, 170), (0, 0, 0, 0)); dr = ImageDraw.Draw(row)
        dr.rounded_rectangle((0, 0, 939, 169), 40, fill=(255, 255, 255, 245))
        dr.rounded_rectangle((870, 20, 910, 150), 20, fill=col + (255,))
        dr.text((840, 58), l1, font=font(fit(l1, 50, 780)), fill=DARK + (255,), anchor="rm", direction="rtl")
        dr.text((840, 122), l2, font=font(fit(l2, 44, 780, False), False), fill=col + (255,), anchor="rm", direction="rtl")
        row.putalpha(Image.fromarray((np.asarray(row.getchannel("A"), np.float32) * a).astype(np.uint8)))
        img.alpha_composite(row, (int(70 + (1 - a) * 200), 900 + k * 195))
    a, s = appear(tl, 3.6)
    txt(img, "لا تنتظر حتى آخر لحظة!", W / 2, 1530, 72, YELLOW, a, s)


def frame(t):
    img = BG.copy()
    if t < T_YES:
        a, s = appear(t, 0.05, 0.4)
        paste_c(img, with_shadow(CARD, 18, 10, 120), W / 2, 760, 0.9 + 0.1 * s)
        if t > 0.6:
            q = ease((t - 0.6) / 0.25)
            paste_c(img, SCADUTO, W / 2 + 40, 800, 2.0 - 1.0 * q)
        a, s = appear(t, 0.9)
        txt(img, "انتهت إقامتك…\nوالجديدة لم تصل بعد؟", W / 2, 300, 84, WHITE, a, s)
        if t >= T_Q:
            a, s = appear(t, T_Q)
            paste_c(img, FACE, W / 2, 1200, s)
            txt(img, "هل يمكنك أن تعمل؟", W / 2, 1420, 92, YELLOW, a, s)
    elif t < T_LINE:
        tl = t - T_YES
        a, s = appear(tl, 0.05)
        txt(img, "نعم!", W / 2, 260, 170, GREEN, a, s)
        a, s = appear(tl, 0.6)
        txt(img, "بشرط واحد: الوصل", W / 2, 440, 84, WHITE, a, s)
        a, s = appear(tl, 1.0, 0.45)
        paste_c(img, with_shadow(REC, 16, 10, 120), W / 2, 920, s)
        a, s = appear(tl, 2.0)
        txt(img, "Ricevuta = الوصل الذي تأخذه\nعند تقديم طلب التجديد", W / 2, 1400, fit("Ricevuta = الوصل الذي تأخذه", 60, W - 120), WHITE, a, s)
    elif t < T_WITH:
        tl = t - T_LINE
        a, s = appear(tl, 0.0)
        txt(img, "متى تقدّم الطلب؟", W / 2, 330, 96, WHITE, a, s)
        timeline(img, tl - 0.3)
    elif t < T_LAW:
        tl = t - T_WITH
        a, s = appear(tl, 0.0)
        txt(img, "مع الوصل:", W / 2, 330, 104, YELLOW, a, s)
        rows = [("تستمر في العمل", True), ("إقامتك قانونية أثناء الانتظار", True),
                ("حتى لو تأخر الرد أكثر من 60 يوماً", True), ("احتفظ به دائماً + صوّره", False)]
        for k, (r_, ok) in enumerate(rows):
            check_row(img, 480 + k * 190, r_, ease((tl - 0.4 - 0.6 * k) / 0.35), ok)
    elif t < T_OUT:
        tl = t - T_LAW
        a, s = appear(tl, 0.0)
        txt(img, "هذا ما يقوله القانون", W / 2, 560, 84, WHITE, a, s)
        a, s = appear(tl, 0.4)
        txt(img, "art. 5 c. 9-bis D.Lgs. 286/1998", W / 2, 720, 56, YELLOW, a, s)
        a, s = appear(tl, 1.0)
        txt(img, "حالتك خاصة؟ اسأل الباتروناتو\nPatronato (مجاناً)", W / 2, 1000, fit("حالتك خاصة؟ اسأل الباتروناتو", 66, W - 120), WHITE, a, s)
    else:
        tl = t - T_OUT
        a, s = appear(tl, 0.05, 0.4)
        if LOGO is not None:
            paste_c(img, LOGO_BIG, W / 2, 700, s)
        txt(img, "أرسل الفيديو لشخص\nينتظر إقامته", W / 2, 1000, 84, YELLOW, a, s)
        a, s = appear(tl, 0.4)
        txt(img, "واحفظه لنفسك", W / 2, 1220, 66, WHITE, a, s)
    if LOGO is not None and t < T_OUT:
        img.alpha_composite(LOGO, (W - LOGO.width - 36, 36))
    return img


if "--preview" in sys.argv:
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    ts = [1.5, 4.2, 7.8, 14.5, 19.5, 23.0, 26.0]
    sheet = Image.new("RGB", (360 * 4, 640 * 2))
    for k, tt in enumerate(ts):
        sheet.paste(frame(tt).convert("RGB").resize((360, 640)), ((k % 4) * 360, (k // 4) * 640))
    sheet.save(os.path.join(od, "sheet.png")); print("ok"); sys.exit()

OUT = sys.argv[1]
TMPV, TMPA = OUT + ".v.mp4", OUT + ".a.wav"
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                       "-pix_fmt", "yuv420p", TMPV], stdin=subprocess.PIPE)
for fi in range(FPS * DUR):
    ff.stdin.write(frame(fi / FPS).convert("RGB").tobytes())
ff.stdin.close(); ff.wait()

sr = 44100; n = sr * DUR; ta = np.arange(n) / sr
rng = np.random.default_rng(16)
mus = np.zeros(n); sfx = np.zeros(n)


def add(buf, sig, at):
    i0 = int(at * sr)
    if 0 <= i0 < n:
        e = min(n, i0 + len(sig)); buf[i0:e] += sig[:e - i0]


def env(dur, k):
    tt = np.arange(int(dur * sr)) / sr
    return tt, np.exp(-tt * k)


beat = 0.6
chords = [(220, 261.6, 329.6), (174.6, 220, 261.6), (261.6, 329.6, 392), (196, 246.9, 293.7)]
for b in range(int(DUR / beat)):
    t0 = b * beat; bar = (b // 4) % 4
    if t0 >= T_YES or b % 2 == 0:
        tt, e = env(0.3, 14); add(mus, np.sin(2 * np.pi * np.cumsum(45 + 70 * np.exp(-tt * 30)) / sr) * e * 0.45, t0)
    if t0 >= T_YES and b % 4 in (1, 3):
        tt, e = env(0.12, 30); add(mus, np.diff(rng.normal(0, 1, len(tt) + 1)) * e * 0.07, t0)
    if b % 4 == 0:
        tt, e = env(2.4, 1.2); add(mus, sum(np.sin(2 * np.pi * f * tt) for f in chords[bar]) * e * 0.035, t0)
mus = mus / np.abs(mus).max() * 0.45
tt, e = env(0.45, 9); thud = (np.sin(2 * np.pi * np.cumsum(140 * np.exp(-tt * 10) + 45) / sr) * 0.8 + rng.normal(0, 1, len(tt)) * 0.15) * e
tt, e = env(0.9, 4)
win = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * 3) * (tt >= dl) for f, dl in ((523.3, 0), (659.3, .1), (784, .2), (1046.5, .3))) * 0.12
tt, e = env(0.12, 35); pop = np.sin(2 * np.pi * (650 + 500 * np.exp(-tt * 40)) * tt) * e * 0.25
tt, e = env(0.6, 6); ding = (np.sin(2 * np.pi * 1318.5 * tt) + 0.6 * np.sin(2 * np.pi * 1975.5 * tt)) * e * 0.16
add(sfx, thud, 0.62); add(sfx, pop, T_Q); add(sfx, win, T_YES); add(sfx, pop, T_YES + 1.0)
for k in range(3):
    add(sfx, pop, T_LINE + 0.6 + 1.3 * k)
add(sfx, ding, T_LINE + 4.5)
for k in range(4):
    add(sfx, ding if k < 3 else pop, T_WITH + 0.4 + 0.6 * k)
add(sfx, pop, T_LAW + 0.4); add(sfx, ding, T_OUT)


def write(path, sig):
    sig = sig * np.clip(ta / 0.05, 0, 1) * np.clip((DUR - ta) / 0.6, 0, 1)
    pcm = (np.repeat(np.clip(sig, -0.95, 0.95)[:, None], 2, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())


for path_out, sig in ((OUT, mus * 0.7 + sfx), (OUT.replace(".mp4", "_no_music.mp4"), sfx)):
    write(TMPA, sig)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", TMPV, "-i", TMPA, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "160k", "-shortest", "-movflags", "+faststart", path_out], check=True)
os.remove(TMPV); os.remove(TMPA)
print("done", DUR, "s")
