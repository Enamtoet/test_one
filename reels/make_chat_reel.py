"""Chat-story reel: 'A Moroccan orders a latte in Italy'.

Usage: python3 make_chat_reel.py OUT.mp4 [--preview]
"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FB, FS = os.path.join(HERE, "Cairo-Black.ttf"), os.path.join(HERE, "Cairo-SemiBold.ttf")
W, H, FPS = 1080, 1920, 30
GREEN, RED, WHITE = (0, 146, 70), (206, 43, 55), (255, 255, 255)
YELLOW, ORANGE, DARK = (255, 214, 90), (232, 118, 18), (28, 30, 40)

# ------------------------------------------------------------------ story
MSGS = [
    ("b", "Buongiorno! Cosa prendi?", "صباح الخير! شنو غادي تاخد؟"),
    ("k", "Un latte, per favore.", "واحد لاتي عافاك."),
    ("b", "Ecco a te!", "هاك!"),
    ("b", "PHOTO", None),
    ("k", "Ma… questo è solo latte!", "ولكن… هادا غير الحليب!"),
    ("b", "Certo! In Italia «latte» vuol dire latte.", "طبعا! فإيطاليا \"لاتي\" معناها الحليب."),
    ("b", "Vuoi un caffè macchiato o un cappuccino?", "بغيتي كافي ماكياطو ولا كاپوتشينو؟"),
    ("k", "Un cappuccino, grazie!", "كاپوتشينو، شكرا!"),
]
LESSON = [
    ("LATTE", "حليب"),
    ("CAFFÈ", "إسپريسو صغير"),
    ("CAFFÈ MACCHIATO", "قهوة مهرسة"),
    ("LATTE MACCHIATO", "حليب بشوية ديال القهوة"),
    ("CAPPUCCINO", "قهوة، حليب ورغوة"),
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


# ------------------------------------------------------------------ drawings
def cup_icon(size, steam_t=None):
    s = size
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((s * .08, s * .78, s * .92, s * .95), fill=(245, 240, 230, 255))
    d.rounded_rectangle((s * .2, s * .42, s * .72, s * .86), int(s * .1), fill=WHITE + (255,))
    d.ellipse((s * .66, s * .5, s * .9, s * .74), outline=WHITE + (255,), width=max(3, int(s * .05)))
    d.ellipse((s * .23, s * .4, s * .69, s * .5), fill=(120, 72, 40, 255))
    if steam_t is not None:
        for k in range(3):
            x0 = s * (.32 + .13 * k)
            pts = [(x0 + s * .04 * math.sin(steam_t * 4 + k + j * 0.9), s * (.36 - j * .06)) for j in range(5)]
            d.line(pts, fill=(255, 255, 255, 170), width=max(3, int(s * .03)), joint="curve")
    return im


def milk_photo(w=440, h=500):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(250, 250, 250, 255))
    d.rounded_rectangle((18, 18, w - 19, h - 80), 26, fill=(214, 233, 245, 255))
    d.rectangle((18, h - 170, w - 19, h - 80), fill=(186, 140, 100, 255))  # bar counter
    gx, gt, gb = w / 2, 80, h - 150
    d.polygon([(gx - 95, gt), (gx + 95, gt), (gx + 75, gb), (gx - 75, gb)], fill=(255, 255, 255, 120),
              outline=(150, 165, 180, 255), width=5)
    d.polygon([(gx - 88, gt + 40), (gx + 88, gt + 40), (gx + 75, gb - 4), (gx - 75, gb - 4)], fill=(252, 250, 242, 255))
    d.ellipse((gx - 88, gt + 28, gx + 88, gt + 52), fill=(255, 255, 255, 255))
    d.text((w / 2, h - 40), "latte", font=font(44), fill=(90, 95, 105, 255), anchor="mm")
    return im


# ------------------------------------------------------------------ chat bubbles
BW_MAX = 800
NAME = {"b": ("Marco · barista", ORANGE), "k": ("Khoya", (0, 120, 60))}
COL = {"b": (252, 252, 252), "k": (214, 247, 196)}


def wrap(s, size, bold, maxw):
    words, lines, cur = s.split(" "), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if measure(trial, size, bold) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur); cur = wd
    lines.append(cur)
    return lines


def make_bubble(who, it, dar):
    pad = 34
    if it == "PHOTO":
        body = milk_photo()
        return with_shadow(body, 14, 8, 90)
    fi, fd, fn = font(54), font(42, False), font(32)
    li = wrap(it, 54, True, BW_MAX - 2 * pad)
    ld = wrap(dar, 42, False, BW_MAX - 2 * pad)
    wmax = max([measure(x, 54) for x in li] + [measure(x, 42, False) for x in ld] + [measure(NAME[who][0], 32)])
    bw = int(wmax + 2 * pad)
    lh_i, lh_d = 72, 60
    bh = int(pad * 0.7 + 44 + len(li) * lh_i + 24 + len(ld) * lh_d + pad * 0.8)
    im = Image.new("RGBA", (bw + 30, bh), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0 = 30 if who == "b" else 0
    d.rounded_rectangle((x0, 0, x0 + bw, bh), 34, fill=COL[who] + (255,))
    if who == "b":
        d.polygon([(x0 + 2, bh - 50), (x0 + 2, bh - 4), (0, bh)], fill=COL[who] + (255,))
        d.polygon([(x0, bh - 46), (x0 + 30, bh - 6), (0, bh)], fill=COL[who] + (255,))
    else:
        d.polygon([(bw - 30, bh - 46), (bw, bh), (bw - 2, bh - 50)], fill=COL[who] + (255,))
        d.polygon([(bw - 30, bh - 46), (bw + 28, bh), (bw - 30, bh - 6)], fill=COL[who] + (255,))
    y = pad * 0.7
    d.text((x0 + pad, y + 20), NAME[who][0], font=fn, fill=NAME[who][1] + (255,), anchor="lm")
    y += 44
    for ln in li:
        d.text((x0 + pad, y + lh_i / 2), ln, font=fi, fill=DARK + (255,), anchor="lm")
        y += lh_i
    d.line((x0 + pad, y + 10, x0 + bw - pad, y + 10), fill=(0, 0, 0, 40), width=2)
    y += 24
    for ln in ld:
        d.text((x0 + bw - pad, y + lh_d / 2), ln, font=fd, fill=(85, 92, 100, 255), anchor="rm", direction="rtl")
        y += lh_d
    return with_shadow(im, 14, 8, 90)


BUBBLES = [make_bubble(*m) for m in MSGS]


def typing_bubble(who, t):
    im = Image.new("RGBA", (190, 100), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 189, 99), 40, fill=COL[who] + (255,))
    for k in range(3):
        b = max(0, math.sin(t * 9 - k * 0.9))
        cx, cy = 50 + k * 45, 52 - 12 * b
        d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=(140, 145, 150, 255))
    return with_shadow(im, 12, 6, 80)


# timeline
HOOK = 3.6
sched, t = [], HOOK + 0.3
for i, (who, it, dar) in enumerate(MSGS):
    typing = 0.45 if it == "PHOTO" else 0.7
    show = t + typing
    read = 2.3 if it == "PHOTO" else 1.2 + 0.045 * len(it)
    sched.append((t, show))
    t = show + read
CHAT_END = t + 0.4
LESSON0 = CHAT_END
LESSON_DUR = 1.0 + 1.3 * len(LESSON) + 3.0
OUT0 = LESSON0 + LESSON_DUR
DUR = int(math.ceil(OUT0 + 7.0))
PHOTO_T = sched[3][1]

AREA_Y, AREA_H, GAP = 300, 1330, 26


def header(img):
    hd = Image.new("RGBA", (W - 80, 170), (0, 0, 0, 0))
    ImageDraw.Draw(hd).rounded_rectangle((0, 0, W - 81, 169), 40, fill=(18, 28, 38, 235))
    img.alpha_composite(hd, (40, 100))
    d = ImageDraw.Draw(img)
    d.ellipse((70, 120, 200, 250), fill=(232, 118, 18, 255))
    img.alpha_composite(cup_icon(110), (80, 125))
    d.text((230, 160), "Bar da Marco", font=font(54), fill=WHITE + (255,), anchor="lm")
    d.ellipse((232, 210, 252, 230), fill=(80, 220, 120, 255))
    d.text((265, 218), "online", font=font(34, False), fill=(170, 220, 190, 255), anchor="lm")


def chat(t):
    img = background(t)
    header(img)
    layer = Image.new("RGBA", (W, AREA_H), (0, 0, 0, 0))
    items = []
    for i, (t_type, t_show) in enumerate(sched):
        who = MSGS[i][0]
        if t >= t_show:
            items.append((who, BUBBLES[i], ease((t - t_show) / 0.3), back((t - t_show) / 0.35)))
        elif t >= t_type:
            items.append((who, typing_bubble(who, t), 1.0, ease((t - t_type) / 0.2)))
            break
        else:
            break
    total = sum(b.height * p + GAP for _, b, p, _ in items)
    off = max(0.0, total - AREA_H)
    y = -off
    for who, b, p, s in items:
        h = b.height
        x = 20 if who == "b" else W - 20 - b.width
        if s < 0.999:
            bb = b.resize((max(1, int(b.width * s)), max(1, int(h * s))), Image.BILINEAR)
            ax = x if who == "b" else x + b.width - bb.width
            layer.alpha_composite(bb, (int(ax), int(y + h - bb.height))) if y + h > 0 else None
        else:
            if y + h > -50:
                layer.alpha_composite(b, (int(x), int(y)))
        y += h * p + GAP
    img.alpha_composite(layer, (0, AREA_Y))
    # comedic shake + caption at the milk photo
    if PHOTO_T <= t < PHOTO_T + 1.4:
        a = 1 - ease((t - PHOTO_T - 1.0) / 0.4)
        txt(img, "😳".replace("😳", "!؟"), W - 140, 1560, 110, YELLOW, a, back((t - PHOTO_T) / 0.3))
    return img


# ------------------------------------------------------------------ hook / lesson / outro
def hook(t):
    img = background(t)
    a, s = appear(t, 0.1)
    txt(img, "مغربي طلب \"لاتي\"\nفبار فإيطاليا...", W / 2, 420, 100, WHITE, a, s)
    a, s = appear(t, 0.4, 0.5)
    paste_c(img, with_shadow(cup_icon(380, t), 18, 10), W / 2, 900, s)
    a, s = appear(t, 1.2)
    txt(img, "شوف شنو وقع!", W / 2, 1380, 120, YELLOW, a, s)
    return img


ROWS = []
for k, (it, dar) in enumerate(LESSON):
    rw, rh = 940, 190
    r = Image.new("RGBA", (rw, rh), (0, 0, 0, 0)); d = ImageDraw.Draw(r)
    d.rounded_rectangle((0, 0, rw - 1, rh - 1), 40, fill=(250, 247, 240, 255))
    d.rounded_rectangle((0, 0, 22, rh - 1), 11, fill=(GREEN if k % 2 == 0 else RED) + (255,))
    d.text((60, rh * 0.33), it, font=font(fit(it, 64, rw - 120)), fill=(GREEN if k % 2 == 0 else RED) + (255,),
           anchor="lm")
    d.text((rw - 40, rh * 0.72), dar, font=font(fit(dar, 54, rw - 120, False), False), fill=DARK + (255,),
           anchor="rm", direction="rtl")
    ROWS.append(with_shadow(r, 14, 8, 100))


def lesson(tl):
    img = background(LESSON0 + tl)
    a, s = appear(tl, 0.1)
    txt(img, "الدرس: كيفاش تطلب القهوة فإيطاليا", W / 2, 260, fit("الدرس: كيفاش تطلب القهوة فإيطاليا", 76), YELLOW, a, s)
    for k, rimg in enumerate(ROWS):
        t0 = 0.9 + 1.3 * k
        p = ease((tl - t0) / 0.4)
        if p > 0.01:
            r2 = rimg.copy()
            if p < 1:
                r2.putalpha(Image.fromarray((np.asarray(r2.getchannel("A"), np.float32) * p).astype(np.uint8)))
            img.alpha_composite(r2, (int(W / 2 - r2.width / 2 + (1 - p) * 300), int(400 + k * 235)))
    return img


LOGO_BIG = None
_lp = os.path.join(HERE, "logo", "ciao_khoya_watermark.png")
if os.path.exists(_lp):
    LOGO_BIG = Image.open(_lp).convert("RGBA")
    LOGO_BIG = LOGO_BIG.resize((420, int(LOGO_BIG.height * 420 / LOGO_BIG.width)), Image.LANCZOS)
    LOGO_SM = LOGO_BIG.resize((170, int(LOGO_BIG.height * 170 / LOGO_BIG.width)), Image.LANCZOS)


def outro(tl):
    img = background(OUT0 + tl)
    fade = 1 - ease((tl - 3.0) / 0.3) if tl > 3.0 else 1
    a, s = appear(tl, 0.2)
    txt(img, "واش عمرك طلبتي \"لاتي\"\nفإيطاليا؟", W / 2, 640, fit("واش عمرك طلبتي \"لاتي\"", 96), WHITE, a * fade, s)
    a, s = appear(tl, 0.8)
    txt(img, "كتب ليا فالكومنتير", W / 2, 920, 86, YELLOW, a * fade, s)
    if tl > 3.2:
        a, s = appear(tl, 3.3, 0.45)
        if LOGO_BIG is not None:
            paste_c(img, LOGO_BIG, W / 2, 560, s)
        txt(img, "تابعني", W / 2, 900, 170, WHITE, a, s)
        a, s = appear(tl, 3.7)
        txt(img, "باش تتعلم الطاليانية\nبالدارجة", W / 2, 1150, 86, YELLOW, a, s)
    return img


def frame(t):
    if t < HOOK:
        img = hook(t)
    elif t < CHAT_END:
        img = chat(t)
    elif t < OUT0:
        img = lesson(t - LESSON0)
    else:
        img = outro(t - OUT0)
    if LOGO_BIG is not None and not (t >= OUT0 + 3.2):
        img.alpha_composite(LOGO_SM, (W - LOGO_SM.width - 70, 125 if HOOK <= t < CHAT_END else 50))
    return img


if "--preview" in sys.argv:
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    ts = [1.5, sched[0][0] + 0.3, sched[0][1] + 1, sched[1][1] + 1, sched[3][1] + 0.4, sched[4][1] + 1,
          sched[6][1] + 1, sched[7][1] + 1.2, LESSON0 + 2.5, LESSON0 + LESSON_DUR - 0.5, OUT0 + 1.5, OUT0 + 5.5]
    cols = 6
    sheet = Image.new("RGB", (360 * cols, 640 * ((len(ts) + cols - 1) // cols)))
    for k, tt in enumerate(ts):
        sheet.paste(frame(tt).convert("RGB").resize((360, 640)), ((k % cols) * 360, (k // cols) * 640))
    sheet.save(os.path.join(od, "sheet.png"))
    print("DUR", DUR, [round(x, 1) for _, x in sched], round(LESSON0, 1), round(OUT0, 1))
    sys.exit()

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
rng = np.random.default_rng(3)
mus = np.zeros(n); sfx = np.zeros(n)


def add(buf, sig, at):
    i0 = int(at * sr)
    if 0 <= i0 < n:
        e = min(n, i0 + len(sig)); buf[i0:e] += sig[:e - i0]


def env(dur, k):
    tt = np.arange(int(dur * sr)) / sr
    return tt, np.exp(-tt * k)


# light jazzy loop (100 bpm): bass + soft chords + brushed hats
beat = 0.6
chords = [(220, 261.6, 329.6, 392), (146.8, 220, 261.6, 349.2), (196, 246.9, 293.7, 349.2), (130.8, 196, 246.9, 329.6)]
roots = [110, 73.4, 98, 65.4]
for b in range(int(DUR / beat)):
    t0 = b * beat; bar = (b // 4) % 4
    tt, e = env(0.5, 6); add(mus, np.sin(2 * np.pi * roots[bar] * tt) * e * 0.3, t0)
    tt, e = env(0.06, 70); add(mus, np.diff(rng.normal(0, 1, len(tt) + 1)) * e * 0.03, t0 + beat / 2)
    if b % 2 == 0:
        tt, e = env(1.1, 2.5)
        add(mus, sum(np.sin(2 * np.pi * f * tt) for f in chords[bar]) * e * 0.04, t0)
    if b % 4 == 2:
        tt, e = env(0.15, 25); add(mus, np.diff(rng.normal(0, 1, len(tt) + 1)) * e * 0.08, t0)
mus = mus / np.abs(mus).max() * 0.5

tt, e = env(0.12, 35); pop = np.sin(2 * np.pi * (700 + 500 * np.exp(-tt * 40)) * tt) * e * 0.35
tt, e = env(0.6, 4); boing = np.sin(2 * np.pi * np.cumsum(520 * np.exp(-tt * 3) + 140) / sr) * e * 0.4
tt, e = env(0.5, 7); ding = (np.sin(2 * np.pi * 1318.5 * tt) + 0.6 * np.sin(2 * np.pi * 1975.5 * tt)) * e * 0.2
for i, (t_type, t_show) in enumerate(sched):
    add(sfx, pop, t_show)
add(sfx, boing, PHOTO_T + 0.15)
for k in range(len(LESSON)):
    add(sfx, ding, LESSON0 + 0.9 + 1.3 * k)
add(sfx, ding, 1.2); add(sfx, ding, OUT0 + 3.3)


def write(path, sig):
    sig = sig * np.clip(ta / 0.05, 0, 1) * np.clip((DUR - ta) / 1.2, 0, 1)
    pcm = (np.repeat(np.clip(sig, -0.95, 0.95)[:, None], 2, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())


for path_out, sig in ((OUT, mus * 0.7 + sfx), (OUT.replace(".mp4", "_no_music.mp4"), sfx)):
    write(TMPA, sig)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", TMPV, "-i", TMPA, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "160k", "-shortest", "-movflags", "+faststart", path_out], check=True)
os.remove(TMPV); os.remove(TMPA)
print("done", DUR, "s")
