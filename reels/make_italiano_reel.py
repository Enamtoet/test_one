"""Italian-for-Darija-speakers reel generator.

Usage: python3 make_italiano_reel.py OUT.mp4 [--preview]
Edit the EP dict below to make a new episode.
"""
import numpy as np, subprocess, math, wave, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FBLACK = os.path.join(HERE, "Cairo-Black.ttf")
FSEMI = os.path.join(HERE, "Cairo-SemiBold.ttf")
W, H, FPS = 1080, 1920, 30

EP = dict(
    hook1="إلا كنتي مغربي\nفإيطاليا...",
    hook2="راك كتهضر الطاليانية\nبلا ما تعرف!",
    count_txt="8 كلمات كتعرفهم من قبل",
    label_top="فالدارجة كنقولو",
    label_it="بالطاليانية",
    label_pr="كيتنطق",
    words=[
        ("كوزينة", "CUCINA", "كوتشينا"),
        ("سبيطار", "OSPEDALE", "أوسبيدالي"),
        ("بانيو", "BAGNO", "بانيو"),
        ("كاميو", "CAMION", "كاميون"),
        ("طابلة", "TAVOLA", "تاڤولا"),
        ("طوموبيل", "AUTOMOBILE", "أوتوموبيلي"),
        ("فاميلا", "FAMIGLIA", "فاميليا"),
        ("كارطة", "CARTA", "كارطا"),
    ],
    out1="شمن كلمة فيهم\nما كنتيش عارفها؟",
    out2="كتبها فالكومنتير",
    follow="تابعني",
    follow2="باش تتعلم الطاليانية\nبالدارجة",
    tag="EPISODIO 1",
)

HOOK = 4.0
CARD = 3.6
N = len(EP["words"])
OUT0 = HOOK + N * CARD
DUR = int(math.ceil(OUT0 + 7.2))

GREEN, RED, WHITE = (0, 146, 70), (206, 43, 55), (255, 255, 255)
YELLOW, ORANGE, DARK = (255, 214, 90), (232, 118, 18), (28, 30, 40)

_fc = {}


def font(sz, bold=True):
    k = (max(8, int(sz)), bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FBLACK if bold else FSEMI, k[0])
    return _fc[k]


def is_ar(s):
    return any("؀" <= c <= "ۿ" for c in s)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def back(x):
    x = clamp(x); c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


_D = ImageDraw.Draw(Image.new("L", (1, 1)))


def measure(s, size, bold=True):
    f = font(size, bold)
    bb = _D.multiline_textbbox((0, 0), s, font=f, align="center", spacing=4,
                               direction="rtl" if is_ar(s) else "ltr")
    return bb[2] - bb[0]


def txt(img, s, cx, cy, size, color, a=1.0, scale=1.0, stroke=0, stroke_col=(0, 0, 0), shadow=True, bold=True):
    if a <= 0.01 or scale <= 0.05:
        return
    f = font(size * scale, bold)
    dr = "rtl" if is_ar(s) else "ltr"
    sw = int(stroke * scale)
    bb = _D.multiline_textbbox((0, 0), s, font=f, stroke_width=sw, align="center", spacing=4, direction=dr)
    pad = 30
    tw, th = int(bb[2] - bb[0] + 2 * pad), int(bb[3] - bb[1] + 2 * pad)
    layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("L", (tw, th), 0)
        ImageDraw.Draw(sh).multiline_text((pad - bb[0], pad + 8 - bb[1]), s, font=f, fill=140, stroke_width=sw,
                                          align="center", spacing=4, direction=dr)
        layer.putalpha(sh.filter(ImageFilter.GaussianBlur(9)))
    ImageDraw.Draw(layer).multiline_text((pad - bb[0], pad - bb[1]), s, font=f, fill=tuple(color) + (255,),
                                         stroke_width=sw, stroke_fill=tuple(stroke_col) + (255,), align="center",
                                         spacing=4, direction=dr)
    if a < 1:
        al = (np.asarray(layer.getchannel("A"), np.float32) * a).astype(np.uint8)
        layer.putalpha(Image.fromarray(al))
    img.alpha_composite(layer, (int(cx - tw / 2), int(cy - th / 2)))


def appear(t, t0, d=0.35):
    return ease((t - t0) / d), back((t - t0) / d)


# ------------------------------------------------------------- background (zellige-like star pattern)
def grad(top, bot):
    tt = (np.arange(H, dtype=np.float32) / (H - 1))[:, None, None]
    g = np.array(top, np.float32) * (1 - tt) + np.array(bot, np.float32) * tt
    return np.broadcast_to(g, (H, W, 3)).copy()


yy = np.arange(H, dtype=np.float32)[:, None]; xx = np.arange(W, dtype=np.float32)[None, :]
vig = (1 - 0.45 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 2)[..., None].clip(0.4, 1)
BG = Image.fromarray(np.clip(grad((10, 66, 70), (12, 20, 40)) * vig, 0, 255).astype(np.uint8)).convert("RGBA")
TS = 160
pat = Image.new("RGBA", (W + 2 * TS, H + 2 * TS), (0, 0, 0, 0))
dp = ImageDraw.Draw(pat)
for ty in range(0, H + 2 * TS, TS):
    for tx in range(0, W + 2 * TS, TS):
        cx, cy, r = tx + TS / 2, ty + TS / 2, TS * 0.36
        sq1 = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2)]
        sq2 = [(cx + r * math.cos(a + math.pi / 4), cy + r * math.sin(a + math.pi / 4)) for a in
               (0, math.pi / 2, math.pi, 3 * math.pi / 2)]
        dp.polygon(sq1, outline=(255, 255, 255, 20), width=3)
        dp.polygon(sq2, outline=(255, 255, 255, 20), width=3)
        dp.ellipse((cx - 8, cy - 8, cx + 8, cy + 8), outline=(255, 214, 90, 28), width=3)


def flag_bar(img):
    d = ImageDraw.Draw(img)
    for y0 in (0, H - 14):
        for i, c in enumerate((GREEN, WHITE, RED)):
            d.rectangle((i * W / 3, y0, (i + 1) * W / 3, y0 + 14), fill=c + (255,))


def background(t):
    img = BG.copy()
    o = int(t * 18) % TS
    img.alpha_composite(pat.crop((o, o, o + W, o + H)))
    flag_bar(img)
    return img


# ------------------------------------------------------------- flags
def flag_ma(w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 18, fill=(193, 39, 45, 255))
    cx, cy, r = w / 2, h / 2, h * 0.3
    pts = [(cx + r * math.sin(2 * math.pi * k / 5), cy - r * math.cos(2 * math.pi * k / 5)) for k in range(5)]
    star = [pts[(2 * k) % 5] for k in range(6)]
    d.line(star, fill=(0, 98, 51, 255), width=max(4, int(h * 0.05)), joint="curve")
    return im


def flag_it(w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), 18, fill=255)
    d = ImageDraw.Draw(im)
    for i, c in enumerate((GREEN, WHITE, RED)):
        d.rectangle((i * w / 3, 0, (i + 1) * w / 3, h), fill=c + (255,))
    im.putalpha(m)
    return im


def with_shadow(im, blur=18, off=12):
    w, h = im.size
    out = Image.new("RGBA", (w + 4 * blur, h + 4 * blur + off), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 120), (2 * blur, 2 * blur + off, 2 * blur + w, 2 * blur + h + off), im.getchannel("A"))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    out.alpha_composite(im, (2 * blur, 2 * blur))
    return out


FMA = with_shadow(flag_ma(330, 220)); FIT = with_shadow(flag_it(330, 220))


def paste_c(img, im, cx, cy, s=1.0):
    if s <= 0.02:
        return
    if s != 1.0:
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
    img.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def arrow(img, x0, y0, x1, y1, col=WHITE, w=14, p=1.0):
    if p <= 0:
        return
    d = ImageDraw.Draw(img)
    xe, ye = x0 + (x1 - x0) * p, y0 + (y1 - y0) * p
    d.line((x0, y0, xe, ye), fill=col + (255,), width=w)
    ang = math.atan2(ye - y0, xe - x0); L = 40
    for s in (-1, 1):
        a = ang + math.pi + s * 0.6
        d.line((xe, ye, xe + L * math.cos(a), ye + L * math.sin(a)), fill=col + (255,), width=w)


# ------------------------------------------------------------- scenes
def hook(t):
    img = background(t)
    a, s = appear(t, 0.1)
    txt(img, EP["hook1"], W / 2, 400, 100, WHITE, a, s)
    a, s = appear(t, 0.3, 0.5)
    paste_c(img, FMA, 770 + (1 - a) * 500, 900)
    a2, _ = appear(t, 0.55, 0.5)
    paste_c(img, FIT, 310 - (1 - a2) * 500, 900)
    arrow(img, 600, 900, 480, 900, YELLOW, 16, ease((t - 0.9) / 0.3))
    a, s = appear(t, 1.1)
    txt(img, EP["hook2"], W / 2, 1320, 104, YELLOW, a, s, stroke=0)
    a, s = appear(t, 2.3)
    txt(img, EP["count_txt"], W / 2, 1600, 72, WHITE, a, s, bold=False)
    return img


CW, CHh = 900, 1150
card = Image.new("RGBA", (CW, CHh), (0, 0, 0, 0))
ImageDraw.Draw(card).rounded_rectangle((0, 0, CW - 1, CHh - 1), 50, fill=(250, 247, 240, 255))
dcard = ImageDraw.Draw(card)
dcard.rectangle((0, 520, CW, 524), fill=(225, 220, 210, 255))
CARD_IMG = with_shadow(card, 26, 16)
CY0 = 400


def word_card(i, tl):
    img = background(HOOK + i * CARD + tl)
    dar, it, pr = EP["words"][i]
    xo = (1 - ease(tl / 0.35)) * W
    if tl > CARD - 0.32:
        xo -= ease((tl - (CARD - 0.32)) / 0.32) * W
    cx = W / 2 + xo
    paste_c(img, CARD_IMG, cx, CY0 + CHh / 2)
    d = ImageDraw.Draw(img)
    # badge
    d.rounded_rectangle((cx - 90, CY0 - 45, cx + 90, CY0 + 45), 45, fill=RED + (255,))
    txt(img, f"{i + 1}/{N}", cx, CY0 - 4, 54, WHITE, shadow=False)
    a, s = appear(tl, 0.2)
    txt(img, EP["label_top"], cx, CY0 + 120, 50, (120, 118, 125), a, 1, shadow=False, bold=False)
    a, s = appear(tl, 0.3)
    txt(img, dar, cx, CY0 + 290, 150, DARK, a, s, shadow=False)
    # arrow down
    p = ease((tl - 0.8) / 0.3)
    if p > 0:
        bob = 8 * math.sin(tl * 6)
        arrow(img, cx, CY0 + 455, cx, CY0 + 460 + 120 * p + bob, ORANGE, 14, 1)
    a, s = appear(tl, 1.0)
    txt(img, EP["label_it"], cx, CY0 + 640, 50, (120, 118, 125), a, 1, shadow=False, bold=False)
    size = 150
    while measure(it, size) > CW - 140:
        size -= 6
    a, s = appear(tl, 1.15, 0.4)
    txt(img, it, cx, CY0 + 790, size, GREEN if i % 2 == 0 else RED, a, s, shadow=False)
    a, s = appear(tl, 1.55)
    if a > 0.01:
        lab = f"{EP['label_pr']}: {pr}"
        tw = measure(lab, 62) + 70
        pill = Image.new("RGBA", (int(tw), 110), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle((0, 0, tw - 1, 109), 55, fill=ORANGE + (int(255 * a),))
        paste_c(img, pill, cx, CY0 + 990, s)
        txt(img, lab, cx, CY0 + 982, 62, WHITE, a, s, shadow=False)
    # progress
    seg, gap = 90, 14
    tot = N * seg + (N - 1) * gap
    x = W / 2 - tot / 2
    for k in range(N):
        col = YELLOW if k <= i else (255, 255, 255)
        al = 255 if k <= i else 70
        d.rounded_rectangle((x, 1700, x + seg, 1714), 7, fill=col + (al,))
        x += seg + gap
    return img


def outro(tl):
    img = background(OUT0 + tl)
    fade = 1 - ease((tl - 3.3) / 0.3) if tl > 3.3 else 1
    a, s = appear(tl, 0.2)
    txt(img, EP["out1"], W / 2, 640, 104, WHITE, a * fade, s)
    a, s = appear(tl, 0.8)
    txt(img, EP["out2"], W / 2, 920, 86, YELLOW, a * fade, s)
    p = ease((tl - 1.1) / 0.3) * fade
    if p > 0.01:
        bob = 20 * abs(math.sin(tl * 4))
        arrow(img, W / 2, 1060 + bob, W / 2, 1220 + bob, YELLOW, 16, p)
    if tl > 3.5:
        a, s = appear(tl, 3.6, 0.45)
        paste_c(img, FIT, W / 2, 560, 0.75 * s)
        txt(img, EP["follow"], W / 2, 820, 180, WHITE, a, s)
        a, s = appear(tl, 4.0)
        txt(img, EP["follow2"], W / 2, 1080, 86, YELLOW, a, s)
        a, s = appear(tl, 4.4)
        txt(img, EP["tag"], W / 2, 1300, 52, (200, 230, 220), a, s, bold=False)
    return img


def frame(t):
    if t < HOOK:
        img = hook(t)
        return img
    if t < OUT0:
        i = int((t - HOOK) // CARD)
        return word_card(i, t - HOOK - i * CARD)
    return outro(t - OUT0)


if "--preview" in sys.argv:
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    ts = [0.6, 2.9, 4.2, 5.0, 6.5, 7.4, 9.3, 15, 27, 31.5, 34.5, 38.5]
    sheet = Image.new("RGB", (360 * 6, 640 * 2))
    for k, tt in enumerate(ts):
        sheet.paste(frame(tt).convert("RGB").resize((360, 640)), ((k % 6) * 360, (k // 6) * 640))
    sheet.save(os.path.join(od, "sheet.png"))
    sys.exit()

OUT = sys.argv[1]
TMPV, TMPA = OUT + ".v.mp4", OUT + ".a.wav"
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                       "-pix_fmt", "yuv420p", TMPV], stdin=subprocess.PIPE)
for fi in range(FPS * DUR):
    ff.stdin.write(frame(fi / FPS).convert("RGB").tobytes())
    if fi % 300 == 0:
        print("frame", fi, flush=True)
ff.stdin.close(); ff.wait()

# ------------------------------------------------------------- music: upbeat 120 bpm loop + sfx
sr = 44100; n = sr * DUR; ta = np.arange(n) / sr
mus = np.zeros(n); rng = np.random.default_rng(3)
beat = 0.5


def add(sig, at):
    i0 = int(at * sr)
    if i0 >= n: return
    e = min(n, i0 + len(sig)); mus[i0:e] += sig[:e - i0]


def env(dur, k):
    tt = np.arange(int(dur * sr)) / sr
    return tt, np.exp(-tt * k)


tt, e = env(0.35, 14); kick = np.sin(2 * np.pi * np.cumsum(45 + 90 * np.exp(-tt * 30)) / sr) * e * 0.9
tt, e = env(0.18, 28); snare = np.diff(rng.normal(0, 1, len(tt) + 1)) * e * 0.18
tt, e = env(0.05, 90); hat = np.diff(np.diff(rng.normal(0, 1, len(tt) + 2))) * e * 0.035
A3, C4, E4, F3, G3, D4, B3, G4, A4, F4 = 220, 261.6, 329.6, 174.6, 196, 293.7, 246.9, 392, 440, 349.2
chords = [(A3, C4, E4, A4), (F3, A3, C4, F4), (C4 / 2 * 2, E4, G4, C4 * 2), (G3, B3, D4, G4)]
roots = [110, 87.3, 130.8, 98]


def pluck(f, dur=0.32, amp=0.06):
    tt, e = env(dur, 9)
    return (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt) + 0.15 * np.sin(6 * np.pi * f * tt)) * e * amp


start_beats = 0
nb = int(DUR / beat)
for b in range(nb):
    t0 = b * beat
    bar = (b // 4) % 4
    add(kick, t0)
    if b % 4 in (1, 3): add(snare, t0)
    add(hat, t0 + beat / 2); add(hat * 0.6, t0)
    ch = chords[bar]
    for k in range(2):
        add(pluck(ch[(b * 2 + k) % 4]), t0 + k * beat / 2)
    if b % 2 == 0:
        tt, e = env(0.9, 3)
        add(np.sin(2 * np.pi * roots[bar] * tt) * e * 0.22, t0)
# duck music under where voice is & normalize
mus = mus / np.abs(mus).max() * 0.55
sfx = np.zeros(n)


def add_sfx(sig, at):
    i0 = int(at * sr); e_ = min(n, i0 + len(sig)); sfx[i0:e_] += sig[:e_ - i0]


tt, e = env(0.5, 7); ding = (np.sin(2 * np.pi * 1318.5 * tt) + 0.6 * np.sin(2 * np.pi * 1975.5 * tt)) * e * 0.22
tt = np.arange(int(0.3 * sr)) / sr
wn = rng.normal(0, 1, len(tt)); wn = np.convolve(wn, np.ones(12) / 12, "same")
whoosh = wn * np.sin(np.pi * tt / 0.3) ** 2 * 0.35
for i in range(N):
    add_sfx(whoosh, HOOK + i * CARD); add_sfx(ding, HOOK + i * CARD + 1.15)
add_sfx(ding, 1.1); add_sfx(whoosh, OUT0); add_sfx(ding, OUT0 + 3.6)


def write(path, sig):
    sig = sig * np.clip(ta / 0.05, 0, 1) * np.clip((DUR - ta) / 1.2, 0, 1)
    sig = np.clip(sig, -0.95, 0.95)
    pcm = (np.repeat(sig[:, None], 2, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())


write(TMPA, mus * 0.7 + sfx)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", TMPV, "-i", TMPA, "-c:v", "copy", "-c:a", "aac", "-b:a",
                "160k", "-shortest", "-movflags", "+faststart", OUT], check=True)
write(TMPA, sfx)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", TMPV, "-i", TMPA, "-c:v", "copy", "-c:a", "aac", "-b:a",
                "160k", "-shortest", "-movflags", "+faststart", OUT.replace(".mp4", "_sfx_only.mp4")], check=True)
os.remove(TMPV); os.remove(TMPA)
print("done", DUR, "s")
