import numpy as np, subprocess, math, wave, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS, DUR = 1080, 1920, 30, 40
OUT = sys.argv[1]
TMPV = OUT + ".video.mp4"
TMPA = OUT + ".audio.wav"
rng = np.random.default_rng(7)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
_fc = {}


HERE = os.path.dirname(os.path.abspath(__file__))
AB = os.path.join(HERE, "Cairo-Black.ttf")
AR = os.path.join(HERE, "Cairo-SemiBold.ttf")


def font(sz, bold=True, arabic=False):
    k = (int(sz), bold, arabic)
    if k not in _fc:
        f = (AB if bold else AR) if arabic else (FB if bold else FR)
        _fc[k] = ImageFont.truetype(f, int(sz))
    return _fc[k]


def is_ar(s):
    return any("\u0600" <= c <= "\u06ff" for c in s)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def fbm(w, h, seed, octs=((4, 1), (8, .5), (16, .25), (32, .125), (64, .06)), aspect=None):
    r = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    for n, a in octs:
        rows = max(2, int(n * h / w)) if aspect is None else max(2, int(n * aspect))
        small = r.random((rows, n)).astype(np.float32)
        im = Image.fromarray((small * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        out += a * (np.asarray(im, np.float32) / 255 - 0.5)
    return out


yy = np.arange(H, dtype=np.float32)[:, None]
xx = np.arange(W, dtype=np.float32)[None, :]


def grad(top, bot, h=H, w=W):
    t = (np.arange(h, dtype=np.float32) / (h - 1))[:, None, None]
    g = np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t
    return np.broadcast_to(g, (h, w, 3)).copy()


r2 = ((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2
VIG = (1 - 0.55 * r2)[..., None].clip(0.3, 1)


def to_img(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def put_text(img, s, cx, cy, size, t, t0, color=(255, 255, 255), dur_in=0.35, pop=True,
             bold=True, t1=None, spacing=10):
    if t < t0:
        return
    a = ease((t - t0) / dur_in)
    if t1 is not None and t > t1:
        a *= 1 - ease((t - t1) / 0.3)
    if a <= 0.01:
        return
    sz = size * (1 + 0.3 * (1 - a)) if pop else size
    f = font(sz, bold, is_ar(s))
    dr = "rtl" if is_ar(s) else "ltr"
    sw = max(3, int(sz * 0.075))
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = d.multiline_textbbox((0, 0), s, font=f, stroke_width=sw, align="center", spacing=spacing, direction=dr)
    tw, th = int(bb[2] - bb[0] + 40), int(bb[3] - bb[1] + 40)
    layer = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    # soft shadow
    sh = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(sh).multiline_text((20 - bb[0], 26 - bb[1]), s, font=f, fill=150, stroke_width=sw,
                                      align="center", spacing=spacing, direction=dr)
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    layer.putalpha(sh)
    ImageDraw.Draw(layer).multiline_text((20 - bb[0], 20 - bb[1]), s, font=f, fill=tuple(color) + (255,),
                                         stroke_width=sw, stroke_fill=(0, 0, 0, 255), align="center",
                                         spacing=spacing, direction=dr)
    if a < 1:
        al = np.asarray(layer.getchannel("A"), np.float32) * a
        layer.putalpha(Image.fromarray(al.astype(np.uint8)))
    img.alpha_composite(layer, (int(cx - tw / 2), int(cy - th / 2)))


# ---------------------------------------------------------------- Scene 1: bleeding glacier
ice = grad((222, 236, 247), (135, 175, 208))
ice += fbm(W, H, 1)[..., None] * np.array([45, 50, 55], np.float32)
streak = fbm(W, H, 2, octs=((40, 1), (90, .5), (200, .3)), aspect=0.15)
ice += streak[..., None] * np.array([40, 45, 50], np.float32)
cr = Image.new("L", (W, H), 0)
dc = ImageDraw.Draw(cr)
for i in range(40):
    x, y = rng.uniform(0, W), rng.uniform(0, H)
    pts = [(x, y)]
    for _ in range(12):
        x += rng.normal(0, 25); y += rng.normal(30, 20); pts.append((x, y))
    dc.line(pts, fill=int(rng.uniform(80, 200)), width=int(rng.uniform(1, 4)))
cr = np.asarray(cr.filter(ImageFilter.GaussianBlur(1.2)), np.float32)[..., None] / 255
ice = ice * (1 - 0.35 * cr) + np.array([60, 95, 130]) * 0.35 * cr

chans = []
for i in range(9):
    x0 = rng.uniform(330, 760); y0 = rng.uniform(560, 700); w = rng.uniform(16, 60)
    delay = rng.uniform(0, 0.9); speed = rng.uniform(750, 1150)
    pts = []; x = x0
    for y in range(int(y0), H + 60, 20):
        x += rng.normal(0, 5); pts.append((x + 14 * math.sin(y / 90 + i), y))
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).line(pts, fill=255, width=int(w), joint="curve")
    m = m.filter(ImageFilter.GaussianBlur(4))
    chans.append((np.asarray(m, np.float32) / 255, y0, delay, speed))
pool_top = Image.new("L", (W, H), 0)
ImageDraw.Draw(pool_top).ellipse((300, 560, 800, 700), fill=255)
pool_top = np.asarray(pool_top.filter(ImageFilter.GaussianBlur(14)), np.float32) / 255
pool_bot = Image.new("L", (W, H), 0)
ImageDraw.Draw(pool_bot).ellipse((120, 1760, 980, 2100), fill=255)
pool_bot = np.asarray(pool_bot.filter(ImageFilter.GaussianBlur(25)), np.float32) / 255
blood = np.zeros((H, W, 3), np.float32) + np.array([128, 16, 12], np.float32)
blood += fbm(W, H, 3)[..., None] * np.array([90, 20, 10], np.float32)
blood += streak[..., None] * np.array([50, 10, 5], np.float32)


def scene1_arr(t):
    alpha = np.zeros((H, W), np.float32)
    for m, y0, delay, speed in chans:
        front = y0 + (t - delay) * speed
        if front <= y0:
            continue
        rowf = np.clip((front - yy) / 70, 0, 1)
        np.maximum(alpha, m * rowf, out=alpha)
    np.maximum(alpha, pool_top * ease(t / 0.6), out=alpha)
    np.maximum(alpha, pool_bot * ease((t - 1.6) / 1.2), out=alpha)
    a = alpha[..., None]
    out = ice * (1 - a) + blood * a
    return out * VIG


def scene1(t):
    img = to_img(scene1_arr(t))
    put_text(img, "جبل ديال الجليد", W / 2, 260, 112, t, 0.15)
    put_text(img, "كيسيل منو الدم؟", W / 2, 420, 116, t, 0.6, color=(255, 70, 55))
    return img


BLED = scene1_arr(4.0)

# ---------------------------------------------------------------- Scene 2: valley + location
LW = 1700


def ridge(width, base, amp, seed):
    r = np.random.default_rng(seed); y = np.zeros(width)
    for n, a in [(3, 1), (7, .5), (15, .25), (40, .12), (110, .05)]:
        pts = r.random(n + 1)
        y += a * np.interp(np.linspace(0, n, width), np.arange(n + 1), pts)
    return base - amp * (y - y.min()) / (y.max() - y.min())


lyy = np.arange(H, dtype=np.float32)[:, None]
sky = grad((120, 160, 200), (232, 238, 244))


def make_layer(rid, colfn):
    m = np.clip(lyy - rid[None, :].astype(np.float32), 0, 1)
    col = colfn(m)
    rgba = np.dstack([np.clip(col, 0, 255), m * 255]).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


r_far = ridge(LW, 1050, 520, 11)
r_mid = ridge(LW, 1300, 480, 12)
r_near = ridge(LW, 1560, 160, 13)
n_far = fbm(LW, H, 21); n_mid = fbm(LW, H, 22); n_near = fbm(LW, H, 23)


def far_col(m):
    c = grad((205, 215, 230), (175, 190, 210), w=LW)
    return c + n_far[..., None] * 30


def mid_col(m):
    rock = np.array([92, 80, 74], np.float32) + n_mid[..., None] * 70
    snowline = r_mid[None, :] + 130 + n_mid * 220
    snow = np.clip((snowline - lyy) / 25, 0, 1)[..., None]
    return rock * (1 - snow) + np.array([238, 242, 248], np.float32) * snow + n_mid[..., None] * 20


def near_col(m):
    return np.array([128, 100, 74], np.float32) + n_near[..., None] * 80 + (lyy[..., None] - 1500) * -0.05


L_far = make_layer(r_far, far_col)
L_mid = make_layer(r_mid, mid_col)
L_near = make_layer(r_near, near_col)
# glacier tongue with red falls on the near layer
GX = 980
dn = ImageDraw.Draw(L_near)
gy = int(r_near[GX])
dn.polygon([(GX - 220, gy + 40), (GX - 160, gy - 120), (GX + 260, gy - 140), (GX + 300, gy + 40)],
           fill=(225, 236, 246, 255))
dn.polygon([(GX - 40, gy - 118), (GX + 10, gy - 120), (GX + 30, gy + 40), (GX - 70, gy + 40)],
           fill=(150, 25, 18, 255))
dn.ellipse((GX - 140, gy + 10, GX + 90, gy + 70), fill=(150, 25, 18, 255))
L_near = L_near.filter(ImageFilter.GaussianBlur(0.8))
SKY2 = to_img(sky)


def draw_pin(img, x, y, s=1.0):
    d = ImageDraw.Draw(img)
    r = 34 * s
    d.ellipse((x - r, y - 2.2 * r - r, x + r, y - 2.2 * r + r), fill=(230, 40, 40, 255), outline=(0, 0, 0, 255), width=4)
    d.polygon([(x - r * 0.85, y - 2.2 * r + r * 0.5), (x + r * 0.85, y - 2.2 * r + r * 0.5), (x, y)],
              fill=(230, 40, 40, 255))
    d.ellipse((x - r * 0.4, y - 2.2 * r - r * 0.4, x + r * 0.4, y - 2.2 * r + r * 0.4), fill=(255, 255, 255, 255))


def scene2(t):
    img = SKY2.copy()
    for L, sp in ((L_far, 12), (L_mid, 35), (L_near, 75)):
        off = int(40 + t * sp)
        img.alpha_composite(L.crop((off, 0, off + W, H)))
    gx = GX + 40 - int(40 + t * 75)
    if t > 1.4:
        p = ease((t - 1.4) / 0.5)
        bounce = 30 * math.sin(min(1, (t - 1.4) / 0.5) * math.pi) + 6 * math.sin(t * 4)
        draw_pin(img, gx, int(r_near[GX]) - 150 - bounce - (1 - p) * 300, 1.0)
    put_text(img, "أنتاركتيكا", W / 2, 300, 125, t, 0.3)
    put_text(img, "الوديان الجافة ديال ماكموردو", W / 2, 450, 70, t, 0.9, bold=False)
    put_text(img, "شلالات الدم", gx, int(r_near[GX]) + 120, 60, t, 2.0, color=(255, 90, 70))
    return img


# ---------------------------------------------------------------- Scene 3: 1911
g = np.asarray(Image.fromarray(np.clip(BLED, 0, 255).astype(np.uint8)).convert("L"), np.float32)
sep = np.dstack([g * 1.05 + 18, g * 0.92 + 8, g * 0.72]).clip(0, 255).astype(np.uint8)
photo = Image.fromarray(sep).crop((0, 330, 1080, 1840)).resize((720, 1007), Image.LANCZOS)
fr = Image.new("RGBA", (720 + 56, 1007 + 56), (236, 226, 204, 255))
fr.paste(photo.convert("RGBA"), (28, 28))
PHOTO = fr.rotate(-3, expand=True, resample=Image.BICUBIC)
bg3 = grad((70, 54, 38), (30, 22, 15)) * VIG


def scene3(t):
    flick = 1 + 0.04 * math.sin(t * 37) + 0.03 * math.sin(t * 13)
    small = rng.normal(0, 18, (H // 2, W // 2)).astype(np.float32)
    grain = np.repeat(np.repeat(small, 2, 0), 2, 1)[..., None]
    img = to_img(bg3 * flick + grain)
    s = 1 + 0.07 * t / 7
    ph = PHOTO.resize((int(PHOTO.width * s), int(PHOTO.height * s)), Image.BILINEAR)
    img.alpha_composite(ph, (int(W / 2 - ph.width / 2), int(930 - ph.height / 2)))
    put_text(img, "1911", W / 2, 230, 200, t, 0.2, color=(245, 228, 190))
    put_text(img, "المستكشفين كانو حاسبين بلي هادي", W / 2, 1560, 64, t, 2.0, bold=False, color=(245, 235, 215))
    put_text(img, "طحالب حمرا", W / 2, 1665, 110, t, 2.6, color=(225, 70, 50))
    if t > 4.6:
        p = ease((t - 4.6) / 0.4)
        d = ImageDraw.Draw(img)
        d.line((820, 1655, 820 - p * 560, 1675), fill=(255, 255, 255, 255), width=14)
    put_text(img, "غالطين!", 260, 1470, 70, t, 5.2, color=(255, 255, 255))
    return img


# ---------------------------------------------------------------- Scene 4: cross-section
TH = 2600
tyy = np.arange(TH, dtype=np.float32)[:, None]
tall = grad((12, 18, 38), (40, 55, 85), h=TH)
surf = ridge(W, 420, 60, 31)[None, :]
base = ridge(W, 1600, 70, 32)[None, :]
ic = grad((215, 235, 248), (70, 120, 170), h=TH)
nT = fbm(W, TH, 33)
strata = np.sin(tyy / 16 + nT * 9) * 0.5 + 0.5
ic = ic * (0.88 + 0.12 * strata[..., None]) + nT[..., None] * 30
rock = grad((70, 52, 42), (25, 18, 15), h=TH) + nT[..., None] * 60 + fbm(W, TH, 34, octs=((120, 1),))[..., None] * 40
mi = np.clip(tyy - surf, 0, 1)[..., None]
mr = np.clip(tyy - base, 0, 1)[..., None]
tall = tall * (1 - mi) + ic * mi
tall = tall * (1 - mr) + rock * mr
LCX, LCY, LA, LB = 540, 1620, 470, 150
e = ((xx - LCX) / LA) ** 2 + ((tyy - LCY) / LB) ** 2
lake_m = np.clip((1 - e) * 6, 0, 1)
glow = np.exp(-np.clip(np.sqrt(e) - 1, 0, None) * 3.5) * (1 - lake_m)
Y0, Y1 = 1250, 2000
LM = lake_m[Y0:Y1][..., None]; GL = glow[Y0:Y1][..., None]
lyr = np.arange(Y0, Y1, dtype=np.float32)[:, None]


def scene4(t):
    oy = int(ease(t / 3.0) * 620)
    T = tall.copy()
    sh = np.sin(xx / 45 + lyr / 22 - t * 3) * 0.5 + np.sin(xx / 90 - lyr / 35 + t * 2) * 0.5
    lake = np.array([155, 35, 14], np.float32) + sh[..., None] * np.array([45, 18, 6])
    pulse = 0.8 + 0.2 * math.sin(t * 3)
    seg = T[Y0:Y1]
    seg = seg * (1 - LM) + lake * LM + GL * np.array([120, 40, 10]) * pulse
    T[Y0:Y1] = seg
    img = to_img(T[oy:oy + H] * VIG)
    put_text(img, "تحت الجليد...", W / 2, 1650 - oy + 0, 82, t, 1.6, t1=3.2)
    put_text(img, "محبوسة هنا", W / 2, 240, 80, t, 3.3)
    v = int(ease((t - 3.8) / 2.6) * 1_000_000)
    put_text(img, f"{v:,}" + ("+" if v >= 1_000_000 else ""), W / 2, 390, 150, t, 3.8, pop=False,
             color=(255, 125, 85))
    put_text(img, "عام", W / 2, 545, 90, t, 3.8)
    for i, (s, x) in enumerate((("مالحة بزاف", 1340), ("عامرة بالحديد", 1440), ("بلا ضو", 1540))):
        put_text(img, s, W / 2, x, 66, t, 7.0 + 0.4 * i, color=(255, 220, 120))
    return img


# ---------------------------------------------------------------- Scene 5: rust
bg5 = grad((30, 24, 26), (8, 6, 8)) * VIG
NP = 70
P = dict(x=rng.uniform(80, W - 80, NP), y=rng.uniform(650, 1400, NP), r=rng.uniform(10, 28, NP),
         ph=rng.uniform(0, 6.28, NP), d=rng.uniform(0, 1.3, NP))
NB = 30
B = dict(x=rng.uniform(60, W - 60, NB), st=rng.uniform(1.0, 2.8, NB), sp=rng.uniform(400, 650, NB),
         r=rng.uniform(8, 20, NB))
BG5 = to_img(bg5)


def scene5(t):
    img = BG5.copy()
    gl = Image.new("RGBA", (W // 2, H // 2), (0, 0, 0, 0)); dg = ImageDraw.Draw(gl)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay)
    for i in range(NB):
        tt = t - B["st"][i]
        if tt < 0: continue
        y = 1950 - tt * B["sp"][i]
        if y < 500: continue
        x = B["x"][i] + 15 * math.sin(tt * 5 + i); r = B["r"][i]
        dl.ellipse((x - r, y - r, x + r, y + r), outline=(150, 210, 255, 200), width=3)
    for i in range(NP):
        x = P["x"][i] + 25 * math.sin(t * 0.8 + P["ph"][i]); y = P["y"][i] + 20 * math.cos(t * 0.6 + P["ph"][i])
        p = clamp((t - 2.6 - P["d"][i]) / 0.8)
        c = np.array([150, 155, 168]) * (1 - p) + np.array([205, 78, 30]) * p
        r = P["r"][i]
        dl.ellipse((x - r, y - r, x + r, y + r), fill=tuple(int(v) for v in c) + (255,))
        dl.ellipse((x - r * 0.5, y - r * 0.6, x - r * 0.1, y - r * 0.2), fill=(255, 255, 255, 90))
        gr = r * 1.6 / 2
        dg.ellipse((x / 2 - gr, y / 2 - gr, x / 2 + gr, y / 2 + gr), fill=tuple(int(v) for v in c) + (int(60 + 90 * p),))
    gl = gl.filter(ImageFilter.GaussianBlur(10)).resize((W, H), Image.BILINEAR)
    img.alpha_composite(gl); img.alpha_composite(lay)
    if t > 5.2:
        a = ease((t - 5.2) / 1.2)
        img = Image.blend(img, to_img(BLED), a)
    put_text(img, "Fe + O₂", W / 2, 280, 130, t, 0.3)
    put_text(img, "حديد + هوا", W / 2, 430, 76, t, 0.8, bold=False, t1=5.0)
    put_text(img, "راه غير...", W / 2, 1390, 110, t, 3.6)
    put_text(img, "الصدأ", W / 2, 1570, 190, t, 4.2, color=(235, 100, 45))
    return img


# ---------------------------------------------------------------- Scene 6: microbes + end card
MCX, MCY, MR = 540, 980, 470
d6 = np.sqrt((xx - MCX) ** 2 + (yy - MCY) ** 2)
circ = np.clip((MR - d6) / 3, 0, 1)
fluid = np.dstack([np.full((H, W), 18.0), np.full((H, W), 62.0), np.full((H, W), 58.0)]) * (1 - 0.6 * (d6 / MR).clip(0, 1) ** 2)[..., None]
fluid += fbm(W, H, 41)[..., None] * np.array([20, 40, 35])
ring = np.clip(1 - np.abs(d6 - MR - 10) / 12, 0, 1)[..., None]
bg6 = fluid * circ[..., None] + ring * np.array([90, 95, 100])
BG6 = to_img(bg6)
CMASK = Image.fromarray((circ * 255).astype(np.uint8))
NM = 30
M = dict(x=rng.uniform(MCX - 380, MCX + 380, NM), y=rng.uniform(MCY - 380, MCY + 380, NM),
         L=rng.uniform(45, 110, NM), w=rng.uniform(16, 26, NM), a=rng.uniform(0, 6.28, NM),
         vx=rng.normal(0, 18, NM), vy=rng.normal(0, 18, NM), ph=rng.uniform(0, 6.28, NM),
         rod=rng.random(NM) < 0.75)


def scene6(t):
    img = BG6.copy()
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(NM):
        x = M["x"][i] + M["vx"][i] * t + 8 * math.sin(t * 2 + M["ph"][i])
        y = M["y"][i] + M["vy"][i] * t + 8 * math.cos(t * 1.7 + M["ph"][i])
        w = M["w"][i]
        if M["rod"][i]:
            a = M["a"][i] + 0.3 * math.sin(t * 1.5 + M["ph"][i]); L = M["L"][i] / 2
            p1 = (x - L * math.cos(a), y - L * math.sin(a)); p2 = (x + L * math.cos(a), y + L * math.sin(a))
            for col, ww in (((90, 220, 150, 210), w), ((185, 255, 215, 150), w * 0.35)):
                d.line((p1, p2), fill=col, width=int(ww))
                for px, py in (p1, p2):
                    d.ellipse((px - ww / 2, py - ww / 2, px + ww / 2, py + ww / 2), fill=col)
        else:
            r = w * 0.8
            d.ellipse((x - r, y - r, x + r, y + r), fill=(120, 230, 190, 200))
            d.ellipse((x - r * 0.4, y - r * 0.5, x, y - r * 0.1), fill=(220, 255, 240, 150))
    lay.putalpha(ImageChops.multiply(lay.getchannel("A"), CMASK))
    img.alpha_composite(lay)
    if t < 0.9:
        img = img.filter(ImageFilter.GaussianBlur(14 * (1 - t / 0.9)))
    dd = ImageDraw.Draw(img)
    dd.line((MCX + 230, MCY + 380, MCX + 330, MCY + 380), fill=(255, 255, 255, 255), width=6)
    dd.text((MCX + 280, MCY + 410), "1 µm", font=font(30, False), fill=(255, 255, 255, 255), anchor="mm")
    put_text(img, "بلا شمس.", W / 2, 250, 92, t, 0.3)
    put_text(img, "بلا أوكسجين.", W / 2, 370, 92, t, 1.0)
    put_text(img, "ومازال حيين!", W / 2, 1560, 112, t, 2.0, color=(120, 245, 170), t1=4.1)
    put_text(img, "واش كاينة حياة", W / 2, 1530, 96, t, 4.5)
    put_text(img, "فكواكب أخرى؟", W / 2, 1660, 104, t, 4.8, color=(150, 205, 255))
    if t > 6.3:
        a = ease((t - 6.3) / 0.5)
        ov = Image.new("RGBA", (W, H), (5, 8, 15, int(225 * a)))
        img.alpha_composite(ov)
        if t > 6.4:
            p = ease((t - 6.4) / 0.4)
            gx, gy, gr = W / 2, 640, 110 * p
            dg = ImageDraw.Draw(img)
            dg.ellipse((gx - gr, gy - gr, gx + gr, gy + gr), fill=(40, 110, 200, 255), outline=(255, 255, 255, 255), width=5)
            for k in (0.35, 0.7):
                dg.ellipse((gx - gr * k, gy - gr, gx + gr * k, gy + gr), outline=(255, 255, 255, 200), width=3)
            dg.line((gx - gr, gy, gx + gr, gy), fill=(255, 255, 255, 200), width=3)
            dg.line((gx - gr * 0.85, gy - gr * 0.5, gx + gr * 0.85, gy - gr * 0.5), fill=(255, 255, 255, 160), width=3)
            dg.line((gx - gr * 0.85, gy + gr * 0.5, gx + gr * 0.85, gy + gr * 0.5), fill=(255, 255, 255, 160), width=3)
        put_text(img, "تابعنا", W / 2, 880, 150, t, 6.5)
        put_text(img, "باش تشوف أغرب\nالبلايص فالأرض", W / 2, 1080, 72, t, 6.8, color=(255, 210, 120))
    return img


SCENES = [(0, 3, scene1), (3, 8, scene2), (8, 15, scene3), (15, 25, scene4), (25, 32, scene5), (32, 40, scene6)]
XF = 0.35


def frame(t):
    for k, (s, e_, fn) in enumerate(SCENES):
        if s <= t < e_:
            img = fn(t - s)
            if k > 0 and t - s < XF:
                ps, pe, pfn = SCENES[k - 1]
                prev = pfn(t - ps)
                img = Image.blend(prev, img, ease((t - s) / XF))
            return img
    return SCENES[-1][2](DUR - SCENES[-1][0] - 0.001)


# ---------------------------------------------------------------- render
if "--preview" in sys.argv:
    os.makedirs(OUT, exist_ok=True)
    for tt in [1.5, 2.9, 5.5, 7.5, 12, 14, 18, 22, 24.5, 29, 31.5, 34, 37.5, 39.8]:
        frame(tt).convert("RGB").resize((360, 640)).save(f"{OUT}/f_{tt:05.1f}.png")
    sys.exit()

ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                       "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                       "-pix_fmt", "yuv420p", TMPV], stdin=subprocess.PIPE)
N = FPS * DUR
for i in range(N):
    ff.stdin.write(frame(i / FPS).convert("RGB").tobytes())
    if i % 150 == 0:
        print("frame", i, flush=True)
ff.stdin.close(); ff.wait()

# ---------------------------------------------------------------- audio
sr = 44100; n = sr * DUR; ta = np.arange(n) / sr
au = 0.16 * np.sin(2 * np.pi * 55 * ta) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.07 * ta))
au += 0.09 * np.sin(2 * np.pi * 82.41 * ta + 0.5 * np.sin(2 * np.pi * 0.2 * ta))
au += 0.05 * np.sin(2 * np.pi * 110 * ta) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.13 * ta + 1))
wn = np.random.default_rng(5).normal(0, 1, n)
F = np.fft.rfft(wn); fr_ = np.fft.rfftfreq(n, 1 / sr); F[fr_ > 350] = 0; F[fr_ < 30] = 0
wind = np.fft.irfft(F, n); wind /= np.abs(wind).max()
au += 0.10 * wind * (0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * ta))
for b in (0, 3, 8, 15, 25, 32):
    tt = ta - b; on = tt >= 0
    env = np.exp(-np.clip(tt, 0, None) * 2.2) * on
    fq = 38 + 70 * np.exp(-np.clip(tt, 0, None) * 6)
    ph = 2 * np.pi * np.cumsum(fq * on) / sr
    au += 0.5 * env * np.sin(ph)
hi = (ta >= 32) * np.clip((ta - 32) / 2, 0, 1)
au += hi * 0.035 * (np.sin(2 * np.pi * 659 * ta) + np.sin(2 * np.pi * 988 * ta)) * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * ta))
au *= np.clip(ta / 0.2, 0, 1) * np.clip((DUR - ta) / 1.5, 0, 1)
au = au / np.abs(au).max() * 0.6
pcm = (np.repeat(au[:, None], 2, 1) * 32767).astype(np.int16)
with wave.open(TMPA, "wb") as wf:
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", TMPV, "-i", TMPA, "-c:v", "copy", "-c:a", "aac",
                "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT], check=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", TMPV, "-c", "copy", "-movflags", "+faststart",
                OUT.replace(".mp4", "_no_music.mp4")], check=True)
os.remove(TMPV); os.remove(TMPA)
print("done")
