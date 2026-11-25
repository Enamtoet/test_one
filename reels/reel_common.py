"""Shared helpers for Ciao Khoya reels (fonts, text, easing, logo, render + audio)."""
import math, os, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FB, FS = os.path.join(HERE, "Cairo-Black.ttf"), os.path.join(HERE, "Cairo-SemiBold.ttf")
DJV = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
W, H, FPS = 1080, 1920, 30
GREEN, RED, WHITE = (30, 170, 90), (220, 50, 50), (255, 255, 255)
YELLOW, DARK, ORANGE, BLUE = (255, 200, 50), (26, 28, 38), (240, 140, 30), (60, 140, 255)

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




def alpha_mul(im, a):
    if a >= 0.999:
        return im
    im = im.copy()
    im.putalpha(Image.fromarray((np.asarray(im.getchannel("A"), np.float32) * max(0.0, a)).astype(np.uint8)))
    return im


def make_bg(top, bot):
    tt = (np.arange(H, dtype=np.float32) / (H - 1))[:, None, None]
    a = np.broadcast_to(np.array(top, np.float32) * (1 - tt) + np.array(bot, np.float32) * tt, (H, W, 3))
    img = Image.fromarray(a.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    for i, c in enumerate(((0, 146, 70), WHITE, (206, 43, 55))):
        d.rectangle((i * W / 3, 0, (i + 1) * W / 3, 12), fill=c + (255,))
    return img


_L = Image.open(os.path.join(HERE, "logo", "ciao_khoya_watermark.png")).convert("RGBA")
LOGO = _L.resize((120, int(_L.height * 120 / _L.width)), Image.LANCZOS)
LOGO_BIG = _L.resize((300, int(_L.height * 300 / _L.width)), Image.LANCZOS)


def card(w, h, fill=(255, 255, 255, 245), r=40):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=fill)
    return c


def row(img, y, text_, a, kind="ok", sub=None):
    """Check-list row: kind ok / warn / no."""
    if a <= 0.01:
        return
    hh = 150 if sub is None else 190
    r = card(940, hh); d = ImageDraw.Draw(r)
    col = {"ok": GREEN, "warn": ORANGE, "no": RED}[kind]
    d.ellipse((805, hh / 2 - 48, 901, hh / 2 + 48), fill=col + (255,))
    cx, cy = 853, hh / 2
    if kind == "ok":
        d.line([(cx - 24, cy), (cx - 6, cy + 20), (cx + 26, cy - 18)], fill=WHITE + (255,), width=12, joint="curve")
    elif kind == "warn":
        d.text((cx, cy - 4), "!", font=font(70), fill=WHITE + (255,), anchor="mm")
    else:
        d.line((cx - 20, cy - 20, cx + 20, cy + 20), fill=WHITE + (255,), width=12)
        d.line((cx - 20, cy + 20, cx + 20, cy - 20), fill=WHITE + (255,), width=12)
    if sub is None:
        d.text((775, hh / 2), text_, font=font(fit(text_, 52, 720)), fill=DARK + (255,), anchor="rm", direction="rtl" if is_ar(text_) and not text_[0].isascii() else "ltr")
    else:
        d.text((775, 66), text_, font=font(fit(text_, 50, 720)), fill=DARK + (255,), anchor="rm", direction="rtl" if is_ar(text_) and not text_[0].isascii() else "ltr")
        d.text((775, 140), sub, font=font(fit(sub, 40, 720, False), False), fill=(90, 95, 110, 255), anchor="rm", direction="rtl" if is_ar(sub) and not sub[0].isascii() else "ltr")
    img.alpha_composite(alpha_mul(r, a), (int(70 + (1 - a) * 200), int(y)))


def outro(img, tl, line1, line2="واحفظه لنفسك"):
    a, s = appear(tl, 0.05, 0.4)
    paste_c(img, LOGO_BIG, W / 2, 700, s)
    txt(img, line1, W / 2, 1000, fit(max(line1.split("\n"), key=len), 84, W - 120), YELLOW, a, s)
    a, s = appear(tl, 0.4)
    txt(img, line2, W / 2, 1220, 64, WHITE, a, s)


def stamp(text_, col, size=110, w=620, h=200, rot=-10):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 8, w - 9, h - 9), 24, outline=col + (240,), width=14)
    d.text((w / 2, h / 2), text_, font=font(fit(text_, size, w - 60)), fill=col + (240,), anchor="mm",
           direction="rtl" if is_ar(text_) else "ltr")
    return im.rotate(rot, expand=True, resample=Image.BICUBIC)


# ------------------------------------------------------------------ audio
SR = 44100


def _env(dur, k):
    tt = np.arange(int(dur * SR)) / SR
    return tt, np.exp(-tt * k)


def sfx_bank(seed=1):
    rng = np.random.default_rng(seed)
    b = {}
    tt, e = _env(0.12, 35); b["pop"] = np.sin(2 * np.pi * (650 + 500 * np.exp(-tt * 40)) * tt) * e * 0.25
    tt, e = _env(0.6, 6); b["ding"] = (np.sin(2 * np.pi * 1318.5 * tt) + 0.6 * np.sin(2 * np.pi * 1975.5 * tt)) * e * 0.16
    tt, e = _env(0.45, 9); b["thud"] = (np.sin(2 * np.pi * np.cumsum(140 * np.exp(-tt * 10) + 45) / SR) * 0.8 + rng.normal(0, 1, len(tt)) * 0.15) * e
    tt, e = _env(0.9, 4)
    b["win"] = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * 3) * (tt >= dl) for f, dl in ((523.3, 0), (659.3, .1), (784, .2), (1046.5, .3))) * 0.12
    tt, e = _env(0.25, 18); b["coin"] = (np.sin(2 * np.pi * 1975 * tt) * (tt < 0.06) + np.sin(2 * np.pi * 2637 * tt) * (tt >= 0.06)) * e * 0.12
    tt, e = _env(0.5, 5); b["buzz"] = np.sign(np.sin(2 * np.pi * 110 * tt)) * e * 0.1
    tt, e = _env(0.03, 100); b["tick"] = np.sign(np.sin(2 * np.pi * 1800 * tt)) * e * 0.05
    tt = np.arange(int(0.35 * SR)) / SR
    b["whoosh"] = np.convolve(rng.normal(0, 1, len(tt)), np.ones(12) / 12, "same") * np.sin(np.pi * tt / 0.35) ** 2 * 0.3
    tt, e = _env(0.4, 8); b["crash"] = rng.normal(0, 1, len(tt)) * e * 0.35 + np.sin(2 * np.pi * 90 * tt) * e * 0.4
    tt = np.arange(int(1.2 * SR)) / SR
    b["fuse"] = rng.normal(0, 1, len(tt)) * 0.05 * (0.6 + 0.4 * np.sin(2 * np.pi * 13 * tt))
    return b


def music(dur, seed=2, chords=None, beat=0.6, intro_sparse=0.0):
    rng = np.random.default_rng(seed)
    n = int(SR * dur); mus = np.zeros(n)
    chords = chords or [(220, 261.6, 329.6), (174.6, 220, 261.6), (261.6, 329.6, 392), (196, 246.9, 293.7)]

    def add(sig, at):
        i0 = int(at * SR)
        if 0 <= i0 < n:
            e = min(n, i0 + len(sig)); mus[i0:e] += sig[:e - i0]
    for b in range(int(dur / beat)):
        t0 = b * beat; bar = (b // 4) % 4
        if t0 >= intro_sparse or b % 2 == 0:
            tt, e = _env(0.3, 14); add(np.sin(2 * np.pi * np.cumsum(45 + 70 * np.exp(-tt * 30)) / SR) * e * 0.45, t0)
        if t0 >= intro_sparse and b % 4 in (1, 3):
            tt, e = _env(0.12, 30); add(np.diff(rng.normal(0, 1, len(tt) + 1)) * e * 0.07, t0)
        tt, e = _env(0.05, 80); add(np.diff(rng.normal(0, 1, len(tt) + 1)) * e * 0.02, t0 + beat / 2)
        if b % 4 == 0:
            tt, e = _env(2.4, 1.2); add(sum(np.sin(2 * np.pi * f * tt) for f in chords[bar]) * e * 0.035, t0)
    return mus / np.abs(mus).max() * 0.45


def render(out, frame_fn, dur, events, seed=1, chords=None):
    """Render frames + music + sfx. events: list of (time, sfx_name)."""
    tmpv, tmpa = out + ".v.mp4", out + ".a.wav"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                           "-pix_fmt", "yuv420p", tmpv], stdin=subprocess.PIPE)
    for fi in range(int(FPS * dur)):
        ff.stdin.write(frame_fn(fi / FPS).convert("RGB").tobytes())
    ff.stdin.close(); ff.wait()
    n = int(SR * dur); ta = np.arange(n) / SR
    bank = sfx_bank(seed); sfx = np.zeros(n)
    for t0, name in events:
        sig = bank[name]; i0 = int(t0 * SR)
        if 0 <= i0 < n:
            e = min(n, i0 + len(sig)); sfx[i0:e] += sig[:e - i0]
    mus = music(dur, seed, chords)
    for path, sig in ((out, mus * 0.7 + sfx), (out.replace(".mp4", "_no_music.mp4"), sfx)):
        sig = sig * np.clip(ta / 0.05, 0, 1) * np.clip((dur - ta) / 0.6, 0, 1)
        pcm = (np.repeat(np.clip(sig, -0.95, 0.95)[:, None], 2, 1) * 32767).astype(np.int16)
        with wave.open(tmpa, "wb") as wf:
            wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(pcm.tobytes())
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmpv, "-i", tmpa, "-c:v", "copy", "-c:a", "aac",
                        "-b:a", "160k", "-shortest", "-movflags", "+faststart", path], check=True)
    os.remove(tmpv); os.remove(tmpa)


def preview(path, frame_fn, ts, cols=4):
    rows_ = (len(ts) + cols - 1) // cols
    sheet = Image.new("RGB", (360 * cols, 640 * rows_))
    for k, tt in enumerate(ts):
        sheet.paste(frame_fn(tt).convert("RGB").resize((360, 640)), ((k % cols) * 360, (k // cols) * 640))
    sheet.save(path)
