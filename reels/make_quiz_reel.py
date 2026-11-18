"""Quiz reel: 'Do you understand Italians? 3-second challenge'.

Usage: python3 make_quiz_reel.py OUT.mp4 [--preview]
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FB, FS = os.path.join(HERE, "Cairo-Black.ttf"), os.path.join(HERE, "Cairo-SemiBold.ttf")
W, H, FPS = 1080, 1920, 30
GREEN, RED, WHITE = (0, 146, 70), (206, 43, 55), (255, 255, 255)
YELLOW, ORANGE, DARK = (255, 214, 90), (232, 118, 18), (28, 30, 40)

# expression, pronunciation, options (Darija), correct index, example IT, example Darija
QUIZ = [
    ("BOH!", "بوه", ["ما عرفتش", "بزاف", "سير فحالك"], 0,
     "Dov'è Marco? Boh!", "فين ماركو؟ ما عرفتش!"),
    ("MAGARI!", "ماگاري", ["مستحيل", "يا ريت", "شكرا"], 1,
     "Domani c'è il sole? Magari!", "غدا غادي تكون الشمس؟ يا ريت!"),
    ("ALLORA…", "ألّورا", ["إيوا…", "غدا", "ديما"], 0,
     "Allora, andiamo?", "إيوا، نمشيو؟"),
    ("FIGURATI!", "فيگوراتي", ["سمح ليا", "عافاك", "بلا جميل"], 2,
     "Grazie! – Figurati!", "شكرا! – بلا جميل!"),
    ("MENO MALE!", "مينو مالي", ["خايب بزاف", "شوية بشوية", "الحمد لله"], 2,
     "Meno male che sei arrivato!", "الحمد لله اللي جيتي!"),
    ("CHE FIGATA!", "كي فيگاتا", ["حشومة!", "واعر!", "عيان"], 1,
     "Una Ferrari? Che figata!", "فيراري؟ واعر!"),
]
N = len(QUIZ)

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


# ------------------------------------------------------------------ background
def grad(top, bot):
    tt = (np.arange(H, dtype=np.float32) / (H - 1))[:, None, None]
    return np.broadcast_to(np.array(top, np.float32) * (1 - tt) + np.array(bot, np.float32) * tt, (H, W, 3)).copy()


yy = np.arange(H, dtype=np.float32)[:, None]; xx = np.arange(W, dtype=np.float32)[None, :]
vig = (1 - 0.45 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 2)[..., None].clip(0.4, 1)
BG = Image.fromarray(np.clip(grad((10, 66, 70), (12, 20, 40)) * vig, 0, 255).astype(np.uint8)).convert("RGBA")
TS = 160
PAT = Image.new("RGBA", (W + 2 * TS, H + 2 * TS), (0, 0, 0, 0))
_dp = ImageDraw.Draw(PAT)
for ty in range(0, H + 2 * TS, TS):
    for tx in range(0, W + 2 * TS, TS):
        cx, cy, r = tx + TS / 2, ty + TS / 2, TS * 0.36
        for off in (0, math.pi / 4):
            _dp.polygon([(cx + r * math.cos(a + off), cy + r * math.sin(a + off))
                         for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2)], outline=(255, 255, 255, 20), width=3)


def background(t):
    img = BG.copy()
    o = int(t * 18) % TS
    img.alpha_composite(PAT.crop((o, o, o + W, o + H)))
    d = ImageDraw.Draw(img)
    for y0 in (0, H - 14):
        for i, c in enumerate((GREEN, WHITE, RED)):
            d.rectangle((i * W / 3, y0, (i + 1) * W / 3, y0 + 14), fill=c + (255,))
    return img



# ------------------------------------------------------------------ timeline
HOOK = 3.8
Q = 7.4            # seconds per question
T_OPT, T_CD, CD = 0.6, 1.5, 3.0
T_REV = T_CD + CD  # reveal
OUT0 = HOOK + N * Q
DUR = int(math.ceil(OUT0 + 8.0))

LOGO = None
_lp = os.path.join(HERE, "logo", "ciao_khoya_watermark.png")
if os.path.exists(_lp):
    _L = Image.open(_lp).convert("RGBA")
    LOGO = _L.resize((170, int(_L.height * 170 / _L.width)), Image.LANCZOS)
    LOGO_BIG = _L.resize((380, int(_L.height * 380 / _L.width)), Image.LANCZOS)


def flag_it_circle(r):
    im = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i, c in enumerate((GREEN, WHITE, RED)):
        d.rectangle((i * 2 * r / 3, 0, (i + 1) * 2 * r / 3, 2 * r), fill=c + (255,))
    m = Image.new("L", (2 * r, 2 * r), 0); ImageDraw.Draw(m).ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=255)
    im.putalpha(m)
    ImageDraw.Draw(im).ellipse((0, 0, 2 * r - 1, 2 * r - 1), outline=WHITE + (255,), width=6)
    return im


FLAG_C = flag_it_circle(62)


def timer_ring(img, cx, cy, frac, num, pulse):
    d = ImageDraw.Draw(img)
    r = 95 * (1 + 0.08 * pulse)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(18, 28, 38, 230))
    col = YELLOW if num > 1 else (255, 90, 80)
    d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * frac, fill=col + (255,), width=18)
    txt(img, str(num), cx, cy - 8, int(100 * (1 + 0.15 * pulse)), col, shadow=False)


def check(d, cx, cy, s, col):
    d.line([(cx - s * .5, cy), (cx - s * .15, cy + s * .35), (cx + s * .55, cy - s * .4)], fill=col, width=int(s * .18),
           joint="curve")


def question(i, tl):
    img = background(HOOK + i * Q + tl)
    expr, pron, opts, ok, ex_it, ex_dar = QUIZ[i]
    slide = (1 - ease(tl / 0.35)) * W
    if tl > Q - 0.3:
        slide -= ease((tl - (Q - 0.3)) / 0.3) * W
    d = ImageDraw.Draw(img)
    # progress pill
    d.rounded_rectangle((W / 2 - 120, 110, W / 2 + 120, 190), 40, fill=RED + (255,))
    txt(img, f"{i + 1}/{N}", W / 2, 146, 58, WHITE, shadow=False)
    # speech bubble with the expression
    bx = W / 2 + slide
    a, s = appear(tl, 0.0, 0.4)
    bub = Image.new("RGBA", (860, 270), (0, 0, 0, 0)); db = ImageDraw.Draw(bub)
    db.rounded_rectangle((0, 0, 859, 239), 60, fill=(250, 247, 240, 255))
    db.polygon([(150, 230), (230, 230), (140, 269)], fill=(250, 247, 240, 255))
    paste_c(img, with_shadow(bub, 16, 10, 110), bx, 420, s)
    img.alpha_composite(FLAG_C, (int(bx - 400), 520))
    txt(img, "الطلياني كيقول:", bx + 230, 590, 44, (200, 230, 220), a, 1, bold=False)
    txt(img, expr, bx, 372, int(fit(expr, 130, 760) * s if s > 0 else 1), RED, a, 1, shadow=False)
    txt(img, pron, bx, 478, 46, (120, 118, 125), a, 1, shadow=False, bold=False)
    # options
    revealed = tl >= T_REV
    for k, o in enumerate(opts):
        oa, os_ = appear(tl, T_OPT + 0.15 * k, 0.3)
        if oa <= 0.01:
            continue
        y = 720 + k * 175
        x0, x1 = 90 + slide, W - 90 + slide
        fill, tcol, lcol = (250, 247, 240), DARK, (0, 120, 160)
        alpha = 1.0
        if revealed:
            if k == ok:
                fill, tcol, lcol = GREEN, WHITE, (0, 100, 50)
            else:
                alpha = 1 - 0.65 * ease((tl - T_REV) / 0.3)
        ov = Image.new("RGBA", (int(x1 - x0) + 40, 190), (0, 0, 0, 0)); do = ImageDraw.Draw(ov)
        do.rounded_rectangle((20, 20, x1 - x0 + 19, 169), 45, fill=fill + (255,))
        do.ellipse((x1 - x0 - 110, 40, x1 - x0, 150), fill=lcol + (255,))
        do.text((x1 - x0 - 55, 95), "ABC"[k], font=font(60), fill=WHITE + (255,), anchor="mm")
        do.text((x1 - x0 - 140, 92), o, font=font(fit(o, 66, x1 - x0 - 300)), fill=tcol + (255,), anchor="rm",
                direction="rtl")
        if revealed and k == ok:
            check(do, 110, 95, 70, WHITE + (255,))
        sc = os_ if not (revealed and k == ok) else 1 + 0.06 * math.sin(clamp((tl - T_REV) / 0.4) * math.pi)
        if alpha < 1:
            ov.putalpha(Image.fromarray((np.asarray(ov.getchannel("A"), np.float32) * alpha).astype(np.uint8)))
        sh = with_shadow(ov, 12, 8, 80) if alpha > 0.9 else ov
        paste_c(img, sh, (x0 + x1) / 2, y + 75, sc * (0.6 + 0.4 * oa))
    # countdown or example
    if T_CD <= tl < T_REV:
        rem = T_REV - tl
        num = int(math.ceil(rem))
        pulse = max(0.0, 1 - (math.ceil(rem) - rem) * 4)
        timer_ring(img, W / 2 + slide, 1350, rem / CD, num, pulse)
        if tl < T_CD + 1.0:
            txt(img, "عندك 3 ثواني!", W / 2 + slide, 1530, 56, YELLOW, ease((tl - T_CD) / 0.3), 1)
    elif revealed:
        a, s = appear(tl, T_REV + 0.4)
        card = Image.new("RGBA", (920, 260), (0, 0, 0, 0)); dc = ImageDraw.Draw(card)
        dc.rounded_rectangle((0, 0, 919, 259), 40, fill=(18, 28, 38, 235))
        dc.text((460, 52), "مثال", font=font(36, False), fill=YELLOW + (255,), anchor="mm", direction="rtl")
        dc.text((460, 125), ex_it, font=font(fit(ex_it, 58, 860)), fill=WHITE + (255,), anchor="mm")
        dc.text((460, 200), ex_dar, font=font(fit(ex_dar, 48, 860, False), False), fill=(200, 230, 220, 255),
                anchor="mm", direction="rtl")
        if a > 0.01:
            if a < 1:
                card.putalpha(Image.fromarray((np.asarray(card.getchannel("A"), np.float32) * a).astype(np.uint8)))
            paste_c(img, card, W / 2 + slide, 1390 + (1 - a) * 60)
    # score dots
    for k in range(N):
        cx = W / 2 + (k - (N - 1) / 2) * 60
        done = k < i or (k == i and revealed)
        d.ellipse((cx - 14, 1600 - 14, cx + 14, 1600 + 14), fill=(GREEN if done else (255, 255, 255)) + (255 if done else 70,))
    return img


def hook(t):
    img = background(t)
    a, s = appear(t, 0.1)
    txt(img, "واش كتفهم\nالطاليانيين؟", W / 2, 430, 130, WHITE, a, s)
    a, s = appear(t, 0.7)
    timer_ring(img, W / 2, 900, 1 - clamp((t - 0.7) / 3.0), 3, 0.5 * max(0, math.sin(t * 6)) if a > 0.5 else 0)
    a, s = appear(t, 1.2)
    txt(img, "تحدي: 6 كلمات\nعندك 3 ثواني فكل وحدة!", W / 2, 1270, fit("عندك 3 ثواني فكل وحدة!", 84), YELLOW, a, s)
    a, s = appear(t, 2.0)
    txt(img, "حسب النقط ديالك", W / 2, 1520, 62, WHITE, a, s, bold=False)
    return img


def outro(tl):
    img = background(OUT0 + tl)
    fade = 1 - ease((tl - 4.0) / 0.3) if tl > 4.0 else 1
    a, s = appear(tl, 0.1)
    txt(img, "شحال جبتي؟", W / 2, 330, 120, WHITE, a * fade, s)
    rows = [("6/6", "طلياني حقيقي!", GREEN), ("3-5", "مزيان، زيد!", ORANGE), ("0-2", "خاصك تتابعني", RED)]
    for k, (sc, lab, col) in enumerate(rows):
        ra, rs = appear(tl, 0.6 + 0.4 * k)
        if ra * fade <= 0.01:
            continue
        r = Image.new("RGBA", (880, 160), (0, 0, 0, 0)); dr = ImageDraw.Draw(r)
        dr.rounded_rectangle((0, 0, 879, 159), 45, fill=(250, 247, 240, 255))
        dr.rounded_rectangle((0, 0, 230, 159), 45, fill=col + (255,))
        dr.rectangle((180, 0, 230, 159), fill=col + (255,))
        dr.text((115, 80), sc, font=font(70), fill=WHITE + (255,), anchor="mm")
        dr.text((840, 80), lab, font=font(62), fill=DARK + (255,), anchor="rm", direction="rtl")
        r.putalpha(Image.fromarray((np.asarray(r.getchannel("A"), np.float32) * ra * fade).astype(np.uint8)))
        paste_c(img, r, W / 2, 600 + k * 200, rs)
    a, s = appear(tl, 2.0)
    txt(img, "كتب النتيجة ديالك\nفالكومنتير", W / 2, 1300, 88, YELLOW, a * fade, s)
    if tl > 4.2:
        a, s = appear(tl, 4.3, 0.45)
        if LOGO is not None:
            paste_c(img, LOGO_BIG, W / 2, 620, s)
        txt(img, "تابعني", W / 2, 940, 170, WHITE, a, s)
        a, s = appear(tl, 4.7)
        txt(img, "باش تتعلم الطاليانية\nبالدارجة", W / 2, 1190, 86, YELLOW, a, s)
    return img


def frame(t):
    if t < HOOK:
        img = hook(t)
    elif t < OUT0:
        i = int((t - HOOK) // Q)
        img = question(i, t - HOOK - i * Q)
    else:
        img = outro(t - OUT0)
    if LOGO is not None and not t >= OUT0 + 4.2:
        img.alpha_composite(LOGO, (W - LOGO.width - 40, 50))
    return img


if "--preview" in sys.argv:
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    ts = [2.5, HOOK + 1.2, HOOK + 2.6, HOOK + 5.0, HOOK + 6.8] + [HOOK + k * Q + 6.5 for k in range(1, N)] + \
         [OUT0 + 3.0, OUT0 + 6.5]
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

# ------------------------------------------------------------------ audio
sr = 44100; n = sr * DUR; ta = np.arange(n) / sr
rng = np.random.default_rng(4)
mus = np.zeros(n); sfx = np.zeros(n)


def add(buf, sig, at):
    i0 = int(at * sr)
    if 0 <= i0 < n:
        e = min(n, i0 + len(sig)); buf[i0:e] += sig[:e - i0]


def env(dur, k):
    tt = np.arange(int(dur * sr)) / sr
    return tt, np.exp(-tt * k)


beat = 0.5  # 120 bpm game-show groove
chords = [(261.6, 329.6, 392), (220, 261.6, 329.6), (174.6, 220, 261.6), (196, 246.9, 293.7)]
roots = [65.4, 55, 87.3, 98]
for b in range(int(DUR / beat)):
    t0 = b * beat; bar = (b // 4) % 4
    tt, e = env(0.3, 14); add(mus, np.sin(2 * np.pi * np.cumsum(45 + 80 * np.exp(-tt * 30)) / sr) * e * 0.6, t0)
    tt, e = env(0.45, 6); add(mus, np.sin(2 * np.pi * roots[bar] * 2 * tt) * e * 0.25, t0 + beat / 2)
    tt, e = env(0.05, 90); add(mus, np.diff(rng.normal(0, 1, len(tt) + 1)) * e * 0.03, t0 + beat / 2)
    if b % 2 == 0:
        for k, f in enumerate(chords[bar]):
            tt, e = env(0.25, 10)
            add(mus, (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * e * 0.05, t0 + k * 0.08)
mus = mus / np.abs(mus).max() * 0.5

tt, e = env(0.05, 60); tick = np.sin(2 * np.pi * 1800 * tt) * e * 0.35
tt, e = env(0.8, 4)
win = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * 4) * (tt >= dl) for f, dl in ((523.3, 0), (659.3, .08), (784, .16), (1046.5, .24))) * 0.12
tt = np.arange(int(0.3 * sr)) / sr
whoosh = np.convolve(rng.normal(0, 1, len(tt)), np.ones(12) / 12, "same") * np.sin(np.pi * tt / 0.3) ** 2 * 0.3
duck = np.ones(n)
for i in range(N):
    q0 = HOOK + i * Q
    add(sfx, whoosh, q0)
    for k in range(3):
        add(sfx, tick, q0 + T_CD + k)
    add(sfx, win, q0 + T_REV)
    duck[int((q0 + T_CD) * sr):int((q0 + T_REV) * sr)] = 0.45  # quieter music while the clock ticks
add(sfx, win, OUT0 + 4.3)


def write(path, sig):
    sig = sig * np.clip(ta / 0.05, 0, 1) * np.clip((DUR - ta) / 1.2, 0, 1)
    pcm = (np.repeat(np.clip(sig, -0.95, 0.95)[:, None], 2, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())


for path_out, sig in ((OUT, mus * 0.6 * duck + sfx), (OUT.replace(".mp4", "_no_music.mp4"), sfx)):
    write(TMPA, sig)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", TMPV, "-i", TMPA, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "160k", "-shortest", "-movflags", "+faststart", path_out], check=True)
os.remove(TMPV); os.remove(TMPA)
print("done", DUR, "s")
