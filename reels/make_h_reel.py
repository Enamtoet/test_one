"""One-idea short: why SPAGHETTI has an H (C/G + H rule). Loopable ~14s.

Usage: python3 make_h_reel.py OUT.mp4 [--preview]
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FB, FS = os.path.join(HERE, "Cairo-Black.ttf"), os.path.join(HERE, "Cairo-SemiBold.ttf")
W, H, FPS = 1080, 1920, 30
GREEN, RED, WHITE = (60, 210, 120), (255, 80, 80), (255, 255, 255)
YELLOW, DARK = (255, 205, 60), (24, 22, 30)

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



DUR = 14
T_OUT, T_WRONG, T_IN, T_RIGHT, T_GRID, T_END = 2.0, 2.5, 4.6, 5.1, 7.3, 11.9
WORD = "SPAGHETTI"
HI = 4  # index of H
SIZE = 176

LOGO = None
_lp = os.path.join(HERE, "logo", "ciao_khoya_watermark.png")
if os.path.exists(_lp):
    _L = Image.open(_lp).convert("RGBA")
    LOGO = _L.resize((130, int(_L.height * 130 / _L.width)), Image.LANCZOS)
    LOGO_BIG = _L.resize((300, int(_L.height * 300 / _L.width)), Image.LANCZOS)


def make_bg():
    tt = (np.arange(H, dtype=np.float32) / (H - 1))[:, None, None]
    a = np.broadcast_to(np.array((44, 30, 26), np.float32) * (1 - tt) + np.array((16, 12, 14), np.float32) * tt, (H, W, 3))
    img = Image.fromarray(a.astype(np.uint8)).convert("RGBA")
    lay = Image.new("RGBA", (W // 4, H // 4), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.ellipse((40, 120, 230, 300), fill=(255, 170, 60, 50))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(35)).resize((W, H), Image.BILINEAR))
    for i, c in enumerate(((0, 146, 70), WHITE, (206, 43, 55))):
        ImageDraw.Draw(img).rectangle((i * W / 3, 0, (i + 1) * W / 3, 12), fill=c + (255,))
    return img


BG = make_bg()
F = font(SIZE)
_d = ImageDraw.Draw(Image.new("L", (1, 1)))
LW = [_d.textlength(c, font=F) for c in WORD]


def layout(with_h):
    ws = [w for k, w in enumerate(LW) if with_h or k != HI]
    total = sum(ws)
    xs, x = [], W / 2 - total / 2
    for k in range(len(WORD)):
        if not with_h and k == HI:
            xs.append(None); continue
        xs.append(x); x += LW[k]
    return xs


XS_H, XS_NO = layout(True), layout(False)
XS_NO[HI] = XS_H[HI]


def letter(img, ch, x, y, col, a=1.0, sc=1.0, glow=False):
    if a <= 0.01:
        return
    f = font(SIZE * sc)
    lay = Image.new("RGBA", (int(SIZE * 1.3 * sc) + 40, int(SIZE * 1.7 * sc)), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    if glow:
        g = Image.new("RGBA", lay.size, (0, 0, 0, 0))
        ImageDraw.Draw(g).text((20, SIZE * 0.85 * sc), ch, font=f, fill=YELLOW + (200,), anchor="lm")
        lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(18)))
    dl.text((20, SIZE * 0.85 * sc), ch, font=f, fill=col + (255,), anchor="lm")
    if a < 1:
        lay.putalpha(Image.fromarray((np.asarray(lay.getchannel("A"), np.float32) * a).astype(np.uint8)))
    img.alpha_composite(lay, (int(x - 20), int(y - SIZE * 0.85 * sc)))


def word(img, t, cy):
    # p_out: H leaving (0..1), p_in: H returning
    p_out = ease((t - T_OUT) / 0.45)
    p_in = ease((t - T_IN) / 0.5)
    gap_closed = p_out * (1 - p_in)
    col = WHITE
    if T_WRONG <= t < T_IN:
        col = RED
    elif t >= T_RIGHT:
        col = GREEN
    for k, ch in enumerate(WORD):
        a, s = appear(t, 0.05 + 0.05 * k, 0.3)
        if k == HI:
            if t < T_OUT:
                pulse = 1 + 0.08 * abs(math.sin(t * 6)) if t > 0.7 else 1
                letter(img, ch, XS_H[k], cy, YELLOW, a, s * pulse, glow=t > 0.7)
            elif t < T_IN:
                y = cy - 700 * p_out
                letter(img, ch, XS_H[k], y, YELLOW, 1 - 0.3 * p_out, 1 + 0.3 * p_out, glow=True)
            else:
                bounce = back((t - T_IN) / 0.5)
                y = cy - 700 * (1 - bounce)
                letter(img, ch, XS_H[k], y, YELLOW if t < T_RIGHT + 0.6 else col, 1, 1, glow=t < T_RIGHT + 0.6)
            continue
        x = XS_H[k] + (XS_NO[k] - XS_H[k]) * gap_closed
        letter(img, ch, x, cy, col, a, s)


def chip(img, s, cx, cy, col, a, sc, mark):
    if a <= 0.01:
        return
    fs = fit(s, 78, 800)
    tw = measure(s, fs) + 200
    im = Image.new("RGBA", (int(tw), 140), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, tw - 1, 139), 70, fill=col + (int(255 * a),))
    d.text((tw - 70, 68), mark, font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70),
           fill=WHITE + (int(255 * a),), anchor="mm")
    d.text(((tw - 120) / 2, 66), s, font=font(fs), fill=WHITE + (int(255 * a),), anchor="mm", direction="rtl")
    paste_c(img, im, cx, cy, sc)


GRID = [("CI · CE", "تش", "CIAO = تشاو", (120, 170, 255)), ("CHI · CHE", "ك", "CHE = كي", (120, 170, 255)),
        ("GI · GE", "دج", "GELATO = دجيلاتو", (255, 170, 80)), ("GHI · GHE", "گ", "SPAGHETTI = سپاگيتّي", (255, 170, 80))]


def frame(t):
    img = BG.copy()
    if t < T_GRID:
        a, s = appear(t, 0.4)
        top = "لماذا يوجد H هنا؟" if t < T_RIGHT else "H تجعل G قاسية!"
        if t >= T_RIGHT:
            a, s = appear(t, T_RIGHT + 0.3)
        txt(img, top, W / 2, 470, 92, WHITE, a, s)
        word(img, t, 860)
        if T_WRONG <= t < T_IN:
            a, s = appear(t, T_WRONG)
            txt(img, "بدون H:", W / 2, 1080, 60, (220, 200, 200), a, 1, bold=False)
            chip(img, "سپادجيتّي", W / 2, 1220, (200, 50, 50), a, s, "✗")
        if t >= T_RIGHT:
            a, s = appear(t, T_RIGHT)
            txt(img, "مع H:", W / 2, 1080, 60, (200, 230, 210), a, 1, bold=False)
            chip(img, "سپاگيتّي", W / 2, 1220, (30, 150, 80), a, s, "✓")
    elif t < T_END:
        tl = t - T_GRID
        a, s = appear(tl, 0.05)
        txt(img, "القاعدة كاملة:", W / 2, 330, 92, YELLOW, a, s)
        for k, (pat, snd, ex, col) in enumerate(GRID):
            p = ease((tl - 0.4 - 0.5 * k) / 0.35)
            if p <= 0.01:
                continue
            cw, ch = 960, 230
            c = Image.new("RGBA", (cw, ch), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
            d.rounded_rectangle((0, 0, cw - 1, ch - 1), 44, fill=(255, 255, 255, 245))
            d.rounded_rectangle((cw - 250, 0, cw - 1, ch - 1), 44, fill=col + (255,))
            d.rectangle((cw - 250, 0, cw - 210, ch - 1), fill=col + (255,))
            d.text((cw - 125, ch / 2), snd, font=font(110), fill=WHITE + (255,), anchor="mm", direction="rtl")
            d.text((50, 80), pat, font=font(72), fill=DARK + (255,), anchor="lm")
            d.text((50, 170), ex, font=font(fit(ex, 46, cw - 360, False), False), fill=(100, 100, 110, 255), anchor="lm")
            c.putalpha(Image.fromarray((np.asarray(c.getchannel("A"), np.float32) * p).astype(np.uint8)))
            paste_c(img, c, W / 2 + (1 - p) * 250, 560 + k * 265)
        a, s = appear(tl, 2.6)
        if a > 0.01:
            dd = ImageDraw.Draw(img)
            for k, s_ in enumerate(("g (Google) = گ", "j (Jeans) = دج")):
                dd.text((W / 2, 1625 + k * 70), s_, font=font(48, False), fill=(210, 200, 190, int(255 * a)), anchor="mm",
                        direction="ltr")
    else:
        tl = t - T_END
        a, s = appear(tl, 0.05, 0.4)
        if LOGO is not None:
            paste_c(img, LOGO_BIG, W / 2, 760, s)
        txt(img, "احفظ الفيديو", W / 2, 1020, 100, YELLOW, a, s)
        a, s = appear(tl, 0.4)
        txt(img, "وتابعنا لتتعلم الإيطالية بالعربي", W / 2, 1170, fit("وتابعنا لتتعلم الإيطالية بالعربي", 64, W - 120), WHITE, a, s)
    if LOGO is not None and t < T_END:
        img.alpha_composite(LOGO, (W - LOGO.width - 36, 40))
    return img


if "--preview" in sys.argv:
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    ts = [1.2, 2.3, 3.6, 4.85, 6.4, 9.6, 11.6, 13.0]
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
rng = np.random.default_rng(14)
mus = np.zeros(n); sfx = np.zeros(n)


def add(buf, sig, at):
    i0 = int(at * sr)
    if 0 <= i0 < n:
        e = min(n, i0 + len(sig)); buf[i0:e] += sig[:e - i0]


def env(dur, k):
    tt = np.arange(int(dur * sr)) / sr
    return tt, np.exp(-tt * k)


beat = 0.5
for b in range(int(DUR / beat)):
    t0 = b * beat
    tt, e = env(0.3, 14); add(mus, np.sin(2 * np.pi * np.cumsum(45 + 80 * np.exp(-tt * 30)) / sr) * e * 0.5, t0)
    if b % 2 == 1:
        tt, e = env(0.12, 28); add(mus, np.diff(rng.normal(0, 1, len(tt) + 1)) * e * 0.09, t0)
    tt, e = env(0.05, 80); add(mus, np.diff(rng.normal(0, 1, len(tt) + 1)) * e * 0.03, t0 + beat / 2)
    m = [57, 60, 64, 62, 60, 64, 67, 64][b % 8]
    tt, e = env(0.3, 10); f = 440 * 2 ** ((m - 69) / 12)
    add(mus, (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * e * 0.06, t0)
mus = mus / np.abs(mus).max() * 0.45
tt, e = env(0.1, 40); pop = np.sin(2 * np.pi * (700 + 500 * np.exp(-tt * 40)) * tt) * e * 0.18
tt = np.arange(int(0.4 * sr)) / sr
whoosh = np.sin(2 * np.pi * np.cumsum(300 + 1500 * tt / 0.4) / sr) * np.sin(np.pi * tt / 0.4) * 0.12
tt, e = env(0.5, 5); buzz = np.sign(np.sin(2 * np.pi * 110 * tt)) * e * 0.12
tt, e = env(0.06, 60); click = np.diff(rng.normal(0, 1, len(tt) + 1)) * e * 0.4
tt, e = env(0.6, 6); ding = (np.sin(2 * np.pi * 1318.5 * tt) + 0.6 * np.sin(2 * np.pi * 1975.5 * tt)) * e * 0.18
for k in range(len(WORD)):
    add(sfx, pop, 0.05 + 0.05 * k)
add(sfx, whoosh, T_OUT); add(sfx, buzz, T_WRONG); add(sfx, whoosh[::-1].copy(), T_IN - 0.1); add(sfx, click, T_IN + 0.35)
add(sfx, ding, T_RIGHT)
for k in range(4):
    add(sfx, pop, T_GRID + 0.4 + 0.5 * k)
add(sfx, ding, T_END)


def write(path, sig):
    sig = sig * np.clip(ta / 0.03, 0, 1) * np.clip((DUR - ta) / 0.4, 0, 1)
    pcm = (np.repeat(np.clip(sig, -0.95, 0.95)[:, None], 2, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())


for path_out, sig in ((OUT, mus * 0.7 + sfx), (OUT.replace(".mp4", "_no_music.mp4"), sfx)):
    write(TMPA, sig)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", TMPV, "-i", TMPA, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "160k", "-shortest", "-movflags", "+faststart", path_out], check=True)
os.remove(TMPV); os.remove(TMPA)
print("done", DUR, "s")
