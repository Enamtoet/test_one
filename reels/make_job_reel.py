"""GPS-style short: how to find a job in Italy, step by step (Modern Standard Arabic).

Usage: python3 make_job_reel.py OUT.mp4 [--preview]
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FB, FS = os.path.join(HERE, "Cairo-Black.ttf"), os.path.join(HERE, "Cairo-SemiBold.ttf")
W, H, FPS = 1080, 1920, 30
GREEN, RED, WHITE = (40, 200, 110), (230, 60, 60), (255, 255, 255)
YELLOW, DARK, BLUE = (255, 205, 60), (24, 26, 34), (60, 140, 255)

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



STEPS = [
    ("الأوراق", "Permesso di soggiorno\n+ Codice fiscale", "تأكد أن إقامتك تسمح بالعمل"),
    ("السيرة الذاتية", "Curriculum Vitae\nin italiano", "صفحة واحدة + صورة + رقم هاتفك"),
    ("مكتب التشغيل", "Centro per l'Impiego", "سجّل مجاناً في أقرب مكتب"),
    ("وكالات ومواقع العمل", "Adecco · Randstad · Gi Group\nIndeed · InfoJobs", "اترك سيرتك في أكثر من مكان"),
    ("المقابلة", "Sono disponibile da subito!", "يعني: أنا جاهز للعمل فوراً"),
]
N = len(STEPS)
HOOK, STEP = 2.8, 4.3
ARR0 = HOOK + N * STEP
OUT0 = ARR0 + 2.8
DUR = int(math.ceil(OUT0 + 2.6))

ROUTE = [(170, 1180), (170, 1010), (540, 1010), (540, 850), (910, 850), (910, 690), (540, 690), (540, 530),
         (170, 530), (170, 380), (540, 380), (540, 290)]
STOP_IDX = [1, 3, 5, 7, 9]
SEG = [math.dist(ROUTE[i], ROUTE[i + 1]) for i in range(len(ROUTE) - 1)]
CUM = [0.0]
for s_ in SEG:
    CUM.append(CUM[-1] + s_)


def at_len(L):
    L = max(0.0, min(CUM[-1], L))
    for i in range(len(SEG)):
        if CUM[i + 1] >= L:
            f = (L - CUM[i]) / SEG[i]
            (x0, y0), (x1, y1) = ROUTE[i], ROUTE[i + 1]
            return x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, math.atan2(y1 - y0, x1 - x0)
    x, y = ROUTE[-1]
    return x, y, -math.pi / 2


def car_len(t):
    if t < HOOK:
        return 0.0
    if t >= ARR0:
        return CUM[STOP_IDX[-1]] + (CUM[-1] - CUM[STOP_IDX[-1]]) * ease((t - ARR0) / 0.9)
    i = int((t - HOOK) // STEP)
    tl = t - HOOK - i * STEP
    L0 = CUM[STOP_IDX[i - 1]] if i > 0 else 0.0
    L1 = CUM[STOP_IDX[i]]
    return L0 + (L1 - L0) * ease(tl / 1.0)


def make_map():
    img = Image.new("RGBA", (W, H), (22, 26, 36, 255)); d = ImageDraw.Draw(img)
    for x in range(-40, W + 80, 185):
        d.line((x, 200, x + 30, 1300), fill=(38, 44, 58, 255), width=26)
    for y in range(230, 1300, 160):
        d.line((0, y, W, y + 20), fill=(38, 44, 58, 255), width=22)
    for (x, y, w_, h_) in ((240, 1080, 220, 120), (620, 920, 200, 110), (260, 760, 200, 130), (650, 580, 200, 120),
                           (260, 600, 180, 80), (700, 1070, 240, 140), (680, 300, 280, 140)):
        d.rounded_rectangle((x, y, x + w_, y + h_), 18, fill=(30, 52, 44, 255))
    d.ellipse((760, 400, 1000, 540), fill=(28, 50, 80, 255))
    d.line(ROUTE, fill=(30, 70, 140, 255), width=34, joint="curve")
    return img


MAP = make_map()

LOGO = None
_lp = os.path.join(HERE, "logo", "ciao_khoya_watermark.png")
if os.path.exists(_lp):
    _L = Image.open(_lp).convert("RGBA")
    LOGO = _L.resize((120, int(_L.height * 120 / _L.width)), Image.LANCZOS)
    LOGO_BIG = _L.resize((300, int(_L.height * 300 / _L.width)), Image.LANCZOS)


def arrow_icon(d, x, y, ang, s=1.0):
    pts = [(34, 0), (-24, -26), (-12, 0), (-24, 26)]
    rot = [(x + s * (px * math.cos(ang) - py * math.sin(ang)), y + s * (px * math.sin(ang) + py * math.cos(ang))) for px, py in pts]
    d.ellipse((x - 46 * s, y - 46 * s, x + 46 * s, y + 46 * s), fill=(60, 140, 255, 70))
    d.polygon(rot, fill=WHITE + (255,), outline=BLUE + (255,))


def pin(d, x, y, n, state):
    col = GREEN if state == 2 else (YELLOW if state == 1 else (90, 100, 120))
    d.ellipse((x - 34, y - 34, x + 34, y + 34), fill=col + (255,), outline=WHITE + (255,), width=5)
    if state == 2:
        d.line([(x - 15, y), (x - 4, y + 12), (x + 17, y - 12)], fill=WHITE + (255,), width=8, joint="curve")
    else:
        d.text((x, y - 2), str(n), font=font(38), fill=DARK + (255,) if state == 1 else WHITE + (255,), anchor="mm")


def flag(d, x, y):
    d.line((x, y, x, y - 110), fill=WHITE + (255,), width=8)
    for r in range(3):
        for c in range(4):
            col = WHITE if (r + c) % 2 == 0 else DARK
            d.rectangle((x + c * 20, y - 110 + r * 20, x + c * 20 + 20, y - 90 + r * 20), fill=col + (255,))


def nav_banner(img, text_, sub, col=(20, 140, 90)):
    b = Image.new("RGBA", (W - 60, 150), (0, 0, 0, 0)); d = ImageDraw.Draw(b)
    d.rounded_rectangle((0, 0, W - 61, 149), 40, fill=col + (245,))
    # turn arrow
    d.line((90, 115, 90, 60, 140, 60), fill=WHITE + (255,), width=14, joint="curve")
    d.polygon([(140, 38), (175, 60), (140, 82)], fill=WHITE + (255,))
    d.text((W - 110, 52), text_, font=font(fit(text_, 54, 760)), fill=WHITE + (255,), anchor="rm", direction="rtl")
    d.text((W - 110, 110), sub, font=font(36, False), fill=(210, 240, 225, 255), anchor="rm", direction="rtl")
    img.alpha_composite(b, (30, 40))


def step_card(img, i, a, s):
    title, it, tip = STEPS[i]
    c = Image.new("RGBA", (980, 400), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, 979, 399), 46, fill=(250, 250, 252, 250))
    d.rounded_rectangle((830, 30, 950, 150), 60, fill=YELLOW + (255,))
    d.text((890, 88), str(i + 1), font=font(72), fill=DARK + (255,), anchor="mm")
    d.text((800, 90), title, font=font(fit(title, 66, 740)), fill=DARK + (255,), anchor="rm", direction="rtl")
    lines = it.split("\n")
    fs = fit(max(lines, key=len), 56 if len(lines) == 1 else 50, 900)
    for k, ln in enumerate(lines):
        d.text((490, 200 + (k - (len(lines) - 1) / 2) * fs * 1.25), ln, font=font(fs), fill=(0, 120, 70, 255), anchor="mm")
    d.line((60, 290, 920, 290), fill=(0, 0, 0, 30), width=3)
    d.text((490, 345), tip, font=font(fit(tip, 46, 900, False), False), fill=(70, 72, 84, 255), anchor="mm", direction="rtl")
    c.putalpha(Image.fromarray((np.asarray(c.getchannel("A"), np.float32) * a).astype(np.uint8)))
    paste_c(img, c, W / 2, 1490 + (1 - a) * 120, 0.94 + 0.06 * s)


def frame(t):
    img = MAP.copy(); d = ImageDraw.Draw(img)
    L = car_len(t)
    # travelled route in bright blue
    pts = [ROUTE[0]]
    for i in range(1, len(ROUTE)):
        if CUM[i] <= L:
            pts.append(ROUTE[i])
        else:
            x, y, _ = at_len(L); pts.append((x, y)); break
    if len(pts) > 1:
        d.line(pts, fill=BLUE + (255,), width=22, joint="curve")
    cur = int((t - HOOK) // STEP) if HOOK <= t < ARR0 else (-1 if t < HOOK else N)
    for k, idx in enumerate(STOP_IDX):
        x, y = ROUTE[idx]
        tl = t - HOOK - k * STEP
        state = 2 if (k < cur or (k == cur and tl > 1.1) or t >= ARR0) else (1 if k == cur else 0)
        pin(d, x, y, k + 1, state)
    flag(d, *ROUTE[-1])
    d.text((ROUTE[-1][0] + 110, ROUTE[-1][1] - 60), "LAVORO", font=font(46), fill=WHITE + (255,), anchor="lm")
    x, y, ang = at_len(L)
    arrow_icon(d, x, y, ang, 1.0)
    if t < HOOK:
        nav_banner(img, "الوجهة: عمل في إيطاليا", "5 خطوات · ابدأ الآن")
        a, s = appear(t, 0.2)
        card = Image.new("RGBA", (980, 400), (0, 0, 0, 0)); dc = ImageDraw.Draw(card)
        dc.rounded_rectangle((0, 0, 979, 399), 46, fill=(250, 250, 252, 250))
        dc.text((490, 130), "كيف تجد عملاً", font=font(96), fill=DARK + (255,), anchor="mm", direction="rtl")
        dc.text((490, 270), "في إيطاليا؟", font=font(110), fill=(0, 120, 70, 255), anchor="mm", direction="rtl")
        card.putalpha(Image.fromarray((np.asarray(card.getchannel("A"), np.float32) * a).astype(np.uint8)))
        paste_c(img, card, W / 2, 1490, 0.9 + 0.1 * s)
    elif t < ARR0:
        i = int((t - HOOK) // STEP); tl = t - HOOK - i * STEP
        nav_banner(img, f"الخطوة {i + 1} من {N}", STEPS[i][0])
        a, s = appear(tl, 0.9, 0.35)
        fade = 1 - ease((tl - (STEP - 0.25)) / 0.25)
        step_card(img, i, a * fade, s)
    elif t < OUT0:
        tl = t - ARR0
        nav_banner(img, "وصلت إلى وجهتك!", "LAVORO TROVATO", (200, 120, 20))
        a, s = appear(tl, 0.9, 0.4)
        card = Image.new("RGBA", (980, 400), (0, 0, 0, 0)); dc = ImageDraw.Draw(card)
        dc.rounded_rectangle((0, 0, 979, 399), 46, fill=(250, 250, 252, 250))
        dc.text((490, 120), "وجدت العمل!", font=font(100), fill=(0, 120, 70, 255), anchor="mm", direction="rtl")
        dc.text((490, 270), "Ho trovato lavoro!", font=font(80), fill=DARK + (255,), anchor="mm")
        card.putalpha(Image.fromarray((np.asarray(card.getchannel("A"), np.float32) * a).astype(np.uint8)))
        paste_c(img, card, W / 2, 1490, 0.9 + 0.1 * s)
        if tl > 0.9:  # confetti
            rng_ = np.random.default_rng(3)
            for k in range(60):
                x0 = rng_.uniform(0, W); sp = rng_.uniform(500, 900); ph = rng_.uniform(0, 6.28)
                yy_ = -50 + (tl - 0.9) * sp
                xx_ = x0 + 40 * math.sin(tl * 4 + ph)
                col = [(255, 205, 60), (40, 200, 110), (230, 60, 60), (60, 140, 255), (255, 255, 255)][k % 5]
                d2 = ImageDraw.Draw(img)
                d2.rectangle((xx_ - 9, yy_ - 5, xx_ + 9, yy_ + 5), fill=col + (255,))
    else:
        tl = t - OUT0
        img.alpha_composite(Image.new("RGBA", (W, H), (14, 16, 24, int(230 * ease(tl / 0.3)))))
        a, s = appear(tl, 0.1, 0.4)
        if LOGO is not None:
            paste_c(img, LOGO_BIG, W / 2, 760, s)
        txt(img, "احفظ الفيديو", W / 2, 1010, 100, YELLOW, a, s)
        a, s = appear(tl, 0.4)
        txt(img, "وأرسله لصديق يبحث عن عمل", W / 2, 1160, fit("وأرسله لصديق يبحث عن عمل", 66, W - 120), WHITE, a, s)
    if LOGO is not None and t < OUT0:
        img.alpha_composite(LOGO, (W - LOGO.width - 40, 205))
    return img


if "--preview" in sys.argv:
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    ts = [2.0] + [HOOK + k * STEP + 2.6 for k in range(N)] + [ARR0 + 2.0, OUT0 + 1.8]
    sheet = Image.new("RGB", (360 * 4, 640 * 2))
    for k, tt in enumerate(ts):
        sheet.paste(frame(tt).convert("RGB").resize((360, 640)), ((k % 4) * 360, (k // 4) * 640))
    sheet.save(os.path.join(od, "sheet.png")); print("DUR", DUR); sys.exit()

OUT = sys.argv[1]
TMPV, TMPA = OUT + ".v.mp4", OUT + ".a.wav"
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                       "-pix_fmt", "yuv420p", TMPV], stdin=subprocess.PIPE)
for fi in range(FPS * DUR):
    ff.stdin.write(frame(fi / FPS).convert("RGB").tobytes())
ff.stdin.close(); ff.wait()

sr = 44100; n = sr * DUR; ta = np.arange(n) / sr
rng = np.random.default_rng(15)
mus = np.zeros(n); sfx = np.zeros(n)


def add(buf, sig, at):
    i0 = int(at * sr)
    if 0 <= i0 < n:
        e = min(n, i0 + len(sig)); buf[i0:e] += sig[:e - i0]


def env(dur, k):
    tt = np.arange(int(dur * sr)) / sr
    return tt, np.exp(-tt * k)


beat = 0.5
chords = [(261.6, 329.6, 392), (220, 261.6, 329.6), (174.6, 220, 261.6), (196, 246.9, 293.7)]
for b in range(int(DUR / beat)):
    t0 = b * beat; bar = (b // 4) % 4
    tt, e = env(0.3, 14); add(mus, np.sin(2 * np.pi * np.cumsum(45 + 80 * np.exp(-tt * 30)) / sr) * e * 0.5, t0)
    if b % 2 == 1:
        tt, e = env(0.12, 28); add(mus, np.diff(rng.normal(0, 1, len(tt) + 1)) * e * 0.08, t0)
    tt, e = env(0.05, 80); add(mus, np.diff(rng.normal(0, 1, len(tt) + 1)) * e * 0.03, t0 + beat / 2)
    if b % 4 == 0:
        tt, e = env(2.0, 1.4); add(mus, sum(np.sin(2 * np.pi * f * tt) for f in chords[bar]) * e * 0.035, t0)
mus = mus / np.abs(mus).max() * 0.45
tt, e = env(0.4, 8)
navding = (np.sin(2 * np.pi * 880 * tt) * (tt < 0.15) + np.sin(2 * np.pi * 1174.7 * tt) * (tt >= 0.15)) * e * 0.2
tt, e = env(0.12, 35); pop = np.sin(2 * np.pi * (650 + 500 * np.exp(-tt * 40)) * tt) * e * 0.25
tt = np.arange(int(1.0 * sr)) / sr
drive = np.convolve(rng.normal(0, 1, len(tt)), np.ones(40) / 40, "same") * np.sin(np.pi * tt) * 0.25
tt, e = env(1.2, 3)
fanfare = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * 2.5) * (tt >= dl) for f, dl in ((523.3, 0), (659.3, .12), (784, .24), (1046.5, .36))) * 0.12
add(sfx, navding, 0.2)
for i in range(N):
    s0 = HOOK + i * STEP
    add(sfx, drive, s0); add(sfx, navding, s0 + 1.0); add(sfx, pop, s0 + 1.1)
add(sfx, drive, ARR0); add(sfx, fanfare, ARR0 + 0.9); add(sfx, pop, OUT0 + 0.1)


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
