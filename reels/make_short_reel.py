"""Short, simple reels: one Italian phrase in ~16 seconds (Modern Standard Arabic, for all Arabic speakers).

Usage: python3 make_short_reel.py OUT_DIR [--preview]
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FB, FS = os.path.join(HERE, "Cairo-Black.ttf"), os.path.join(HERE, "Cairo-SemiBold.ttf")
W, H, FPS = 1080, 1920, 30
GREEN, RED, WHITE = (0, 146, 70), (206, 43, 55), (255, 255, 255)
YELLOW, DARK = (255, 214, 90), (28, 30, 40)

SHORTS = [
    dict(slug="figurati", bg=((8, 70, 72), (4, 30, 40)),
         hook="قال لك إيطالي: Grazie\nبماذا ترد؟", it="Figurati!", pr="فيگوراتي",
         ar="لا شكر على واجب", ex_it="Grazie! – Figurati!", ex_ar="شكراً! – لا شكر على واجب!",
         tip="مع الغرباء والمدير: Si figuri"),
    dict(slug="magari", bg=((90, 24, 40), (35, 8, 20)),
         hook="كيف تقول \"يا ليت\"\nبالإيطالية؟", it="Magari!", pr="ماگاري",
         ar="يا ليت!", ex_it="Domani c'è il sole? – Magari!", ex_ar="غداً مشمس؟ – يا ليت!",
         tip="وأحياناً تعني: ربما"),
    dict(slug="ripetere", bg=((20, 36, 90), (8, 12, 40)),
         hook="لم تفهم ما قاله الإيطالي؟\nلا تسكت! قل:", it="Può ripetere,\nper favore?", pr="پوو ريپيتيري، پير فاڤوري",
         ar="هل يمكنك الإعادة\nمن فضلك؟", ex_it="Scusi, può ripetere, per favore?", ex_ar="عفواً، هل يمكنك الإعادة من فضلك؟",
         tip="وإذا كان يتكلم بسرعة: Più piano, per favore"),
    dict(slug="quanto_costa", bg=((40, 70, 20), (14, 30, 8)),
         hook="في السوق…\nكيف تسأل عن السعر؟", it="Quanto costa?", pr="كوانتو كوستا",
         ar="كم سعره؟", ex_it="Quanto costa questa borsa?", ex_ar="كم سعر هذه الحقيبة؟",
         tip="لأكثر من شيء: Quanto costano?\u200e"),
    dict(slug="boh", bg=((60, 26, 90), (22, 8, 40)),
         hook="كلمة يقولها الإيطاليون\nكل يوم… من 3 حروف!", it="Boh!", pr="بوه",
         ar="لا أعرف!", ex_it="Dov'è Marco? – Boh!", ex_ar="أين ماركو؟ – لا أعرف!",
         tip="كلمة عامية: لا تستعملها مع المدير"),
]

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



T_IT, T_AR, T_EX, T_END = 2.8, 6.6, 9.4, 13.4
DUR = 16

LOGO = None
_lp = os.path.join(HERE, "logo", "ciao_khoya_watermark.png")
if os.path.exists(_lp):
    _L = Image.open(_lp).convert("RGBA")
    LOGO = _L.resize((140, int(_L.height * 140 / _L.width)), Image.LANCZOS)
    LOGO_BIG = _L.resize((360, int(_L.height * 360 / _L.width)), Image.LANCZOS)


def make_bg(top, bot):
    tt = (np.arange(H, dtype=np.float32) / (H - 1))[:, None, None]
    a = np.broadcast_to(np.array(top, np.float32) * (1 - tt) + np.array(bot, np.float32) * tt, (H, W, 3))
    return Image.fromarray(a.astype(np.uint8)).convert("RGBA")


def blobs(img, t):
    lay = Image.new("RGBA", (W // 4, H // 4), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k in range(3):
        cx = W / 8 + W / 8 * math.sin(t * 0.25 + k * 2.1)
        cy = H / 8 + H / 10 * math.cos(t * 0.2 + k * 1.7)
        r = 90 + 20 * k
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, 14))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(25)).resize((W, H), Image.BILINEAR))


def typewriter(img, s, cy, size, t0, t, color):
    """Latin text revealed letter by letter, centered, multi-line."""
    lines = s.split("\n")
    f = font(size)
    lh = size * 1.25
    y0 = cy - lh * (len(lines) - 1) / 2
    idx = 0
    d = ImageDraw.Draw(img)
    for li, ln in enumerate(lines):
        x = W / 2 - d.textlength(ln, font=f) / 2
        for ch in ln:
            p = ease((t - t0 - idx * 0.045) / 0.25)
            if p > 0.01:
                lay = Image.new("RGBA", (int(size * 1.4), int(size * 1.6)), (0, 0, 0, 0))
                ImageDraw.Draw(lay).text((size * 0.2, size * 0.8), ch, font=f, fill=color + (int(255 * p),), anchor="lm",
                                         stroke_width=max(2, size // 22), stroke_fill=(0, 0, 0, int(140 * p)))
                img.alpha_composite(lay, (int(x - size * 0.2), int(y0 + li * lh - size * 0.8 + (1 - p) * 40)))
            x += d.textlength(ch, font=f)
            idx += 1


def frame(S, bg, t):
    img = bg.copy(); blobs(img, t)
    d = ImageDraw.Draw(img)
    for i, c in enumerate((GREEN, WHITE, RED)):
        d.rectangle((i * W / 3, 0, (i + 1) * W / 3, 12), fill=c + (255,))
    if t < T_END:
        # 1) hook
        fade = 1 - ease((t - (T_IT - 0.3)) / 0.3)
        a, s = appear(t, 0.15, 0.4)
        hs = fit(S["hook"].split("\n")[0], 92, W - 140)
        txt(img, S["hook"], W / 2, 900, hs, WHITE, a * fade, s)
        if t >= T_IT - 0.05:
            # 2) italian phrase (stays) + pronunciation
            nl = S["it"].count("\n") + 1
            size = fit(max(S["it"].split("\n"), key=len), 150 if nl == 1 else 120, W - 140)
            up = ease((t - T_AR) / 0.4) * 230
            typewriter(img, S["it"], 640 - up + (0 if nl == 1 else 20), size, T_IT, t, YELLOW)
            a, s = appear(t, T_IT + 0.9)
            txt(img, "النطق: " + S["pr"], W / 2, 640 - up + (130 if nl == 1 else 220), fit("النطق: " + S["pr"], 54, W - 160, False),
                (220, 230, 240), a, 1, bold=False)
        if t >= T_AR:
            # 3) meaning
            a, s = appear(t, T_AR + 0.2, 0.4)
            nl = S["ar"].count("\n") + 1
            d.line((W / 2 - 60, 905 - (0 if nl == 1 else 40), W / 2 + 60, 905 - (0 if nl == 1 else 40)), fill=(255, 255, 255, int(120 * a)), width=4)
            txt(img, S["ar"], W / 2, 1040, fit(max(S["ar"].split("\n"), key=len), 110 if nl == 1 else 92, W - 140), WHITE, a, s)
        if t >= T_EX:
            # 4) example + tip
            a, s = appear(t, T_EX, 0.4)
            card = Image.new("RGBA", (960, 330), (0, 0, 0, 0)); dc = ImageDraw.Draw(card)
            dc.rounded_rectangle((0, 0, 959, 329), 40, fill=(255, 255, 255, 235))
            dc.text((480, 50), "مثال", font=font(36, False), fill=(120, 120, 130, 255), anchor="mm", direction="rtl")
            dc.text((480, 125), S["ex_it"], font=font(fit(S["ex_it"], 58, 900)), fill=(0, 120, 60, 255), anchor="mm")
            dc.text((480, 200), S["ex_ar"], font=font(fit(S["ex_ar"], 50, 900, False), False), fill=DARK + (255,), anchor="mm", direction="rtl")
            dc.line((60, 250, 900, 250), fill=(0, 0, 0, 30), width=2)
            dc.text((480, 292), "💡".replace("💡", "") + S["tip"], font=font(fit(S["tip"], 42, 900)), fill=(170, 90, 10, 255),
                    anchor="mm", direction="rtl")
            card.putalpha(Image.fromarray((np.asarray(card.getchannel("A"), np.float32) * a).astype(np.uint8)))
            paste_c(img, card, W / 2, 1400 + (1 - a) * 80)
        if LOGO is not None:
            img.alpha_composite(LOGO, (W - LOGO.width - 36, 40))
    else:
        tl = t - T_END
        a, s = appear(tl, 0.0, 0.4)
        if LOGO is not None:
            paste_c(img, LOGO_BIG, W / 2, 700, s)
        txt(img, S["it"].replace("\n", " "), W / 2, 1000, fit(S["it"].replace("\n", " "), 90, W - 140), YELLOW, a, s)
        a, s = appear(tl, 0.4)
        txt(img, "احفظ الفيديو وتابعنا\nلتتعلم الإيطالية بالعربي", W / 2, 1230, 70, WHITE, a, s)
    return img


if __name__ == "__main__":
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    preview = "--preview" in sys.argv
    for S in SHORTS:
        bg = make_bg(*S["bg"])
        if preview:
            ts = [1.5, 4.5, 8.0, 12.0, 14.8]
            sheet = Image.new("RGB", (360 * len(ts), 640))
            for k, tt in enumerate(ts):
                sheet.paste(frame(S, bg, tt).convert("RGB").resize((360, 640)), (k * 360, 0))
            sheet.save(os.path.join(od, f"sheet_{S['slug']}.png"))
            continue
        out = os.path.join(od, f"ciao_khoya_short_{S['slug']}.mp4")
        tmpv, tmpa = out + ".v.mp4", out + ".a.wav"
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                               "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                               "-pix_fmt", "yuv420p", tmpv], stdin=subprocess.PIPE)
        for fi in range(FPS * DUR):
            ff.stdin.write(frame(S, bg, fi / FPS).convert("RGB").tobytes())
        ff.stdin.close(); ff.wait()
        # audio: soft lo-fi beat + light sfx
        sr = 44100; n = sr * DUR; ta = np.arange(n) / sr
        rng = np.random.default_rng(5)
        mus = np.zeros(n); sfx = np.zeros(n)

        def add(buf, sig, at):
            i0 = int(at * sr)
            if 0 <= i0 < n:
                e = min(n, i0 + len(sig)); buf[i0:e] += sig[:e - i0]

        def env(dur, k):
            tt_ = np.arange(int(dur * sr)) / sr
            return tt_, np.exp(-tt_ * k)

        beat = 0.66
        chords = [(220, 261.6, 329.6), (174.6, 220, 261.6), (196, 246.9, 293.7), (164.8, 207.7, 246.9)]
        for b in range(int(DUR / beat)):
            t0 = b * beat; bar = (b // 4) % 4
            tt_, e = env(0.3, 14); add(mus, np.sin(2 * np.pi * np.cumsum(45 + 70 * np.exp(-tt_ * 30)) / sr) * e * 0.5, t0)
            if b % 4 in (1, 3):
                tt_, e = env(0.12, 30); add(mus, np.diff(rng.normal(0, 1, len(tt_) + 1)) * e * 0.08, t0)
            tt_, e = env(0.05, 80); add(mus, np.diff(rng.normal(0, 1, len(tt_) + 1)) * e * 0.02, t0 + beat / 2)
            if b % 4 == 0:
                tt_, e = env(2.6, 1.2)
                add(mus, sum(np.sin(2 * np.pi * f * tt_) for f in chords[bar]) * e * 0.035, t0)
        mus = mus / np.abs(mus).max() * 0.45
        tt_, e = env(0.12, 35); pop = np.sin(2 * np.pi * (650 + 500 * np.exp(-tt_ * 40)) * tt_) * e * 0.25
        tt_, e = env(0.03, 120); tick = np.sin(2 * np.pi * 2200 * tt_) * e * 0.06
        tt_, e = env(0.6, 6); ding = (np.sin(2 * np.pi * 1318.5 * tt_) + 0.6 * np.sin(2 * np.pi * 1975.5 * tt_)) * e * 0.15
        add(sfx, pop, 0.15)
        nch = len(S["it"].replace("\n", ""))
        for k in range(nch):
            add(sfx, tick, T_IT + k * 0.045)
        add(sfx, ding, T_AR + 0.2); add(sfx, pop, T_EX); add(sfx, ding, T_END)

        def write(path, sig):
            sig = sig * np.clip(ta / 0.05, 0, 1) * np.clip((DUR - ta) / 0.8, 0, 1)
            pcm = (np.repeat(np.clip(sig, -0.95, 0.95)[:, None], 2, 1) * 32767).astype(np.int16)
            with wave.open(path, "wb") as wf:
                wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())

        for path_out, sig in ((out, mus * 0.7 + sfx), (out.replace(".mp4", "_no_music.mp4"), sfx)):
            write(tmpa, sig)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmpv, "-i", tmpa, "-c:v", "copy", "-c:a", "aac",
                            "-b:a", "160k", "-shortest", "-movflags", "+faststart", path_out], check=True)
        os.remove(tmpv); os.remove(tmpa)
        print("done", out)
