"""Generate vertical (1080x1920) TikTok text videos about dogs, in Italian.

Usage: python3 make_videos.py            -> renders every video in VIDEOS
Requires: Pillow, ffmpeg. Output: ./out/*.mp4
Add a trending sound inside the TikTok app when posting.
"""
import math
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
FONT_BLACK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FONT_EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

# Each video: theme colours, hook slide, tip slides (emoji, title, body), outro.
VIDEOS = [
    {
        "slug": "01_cibi_vietati",
        "bg": ((255, 94, 87), (255, 159, 67)),
        "hook": ("🚫🐶", "5 cibi che il tuo cane NON deve mai mangiare"),
        "tips": [
            ("🍫", "Cioccolato", "Contiene teobromina: è tossica per i cani, soprattutto quello fondente."),
            ("🍇", "Uva e uvetta", "Anche poca può danneggiare i reni."),
            ("🧅", "Cipolla e aglio", "Crudi o cotti, danneggiano i globuli rossi."),
            ("🍬", "Xilitolo", "Il dolcificante di gomme e caramelle senza zucchero: molto pericoloso."),
            ("🥜", "Noci di macadamia", "Possono causare debolezza, vomito e tremori."),
        ],
        "outro": ("📌", "Salva il video e mandalo a chi ha un cane", "Se li ingerisce, chiama subito il veterinario"),
    },
    {
        "slug": "02_ti_ama",
        "bg": ((108, 92, 231), (232, 67, 147)),
        "hook": ("🐶❤️", "5 segnali che il tuo cane ti ama davvero"),
        "tips": [
            ("👣", "Ti segue ovunque", "Anche in bagno. Sì, è amore."),
            ("🧸", "Ti porta i suoi giochi", "Sta condividendo con te le sue cose preziose."),
            ("🏠", "Festa quando torni", "Anche se sei uscito solo 5 minuti."),
            ("🤗", "Si appoggia a te", "Cerca il contatto perché con te si sente al sicuro."),
            ("😴", "Dorme vicino a te", "Dormire accanto a qualcuno è segno di fiducia totale."),
        ],
        "outro": ("💬", "Quanti segnali fa il tuo cane?", "Scrivilo nei commenti 👇"),
    },
    {
        "slug": "03_inverno",
        "bg": ((9, 132, 227), (0, 206, 201)),
        "hook": ("❄️🐕", "Inverno: 4 consigli per il tuo cane"),
        "tips": [
            ("🧥", "Cappottino", "Utile per cani piccoli, anziani o a pelo corto."),
            ("🐾", "Asciuga le zampe", "Sale e ghiaccio irritano i cuscinetti: puliscile dopo ogni uscita."),
            ("🚶", "Passeggiate brevi", "Meglio più uscite corte che una lunga al gelo."),
            ("🛏️", "Cuccia calda", "Lontana da spifferi e pavimenti freddi."),
        ],
        "outro": ("➕", "Segui per altri consigli sui cani", "Ogni giorno un nuovo video 🐶"),
    },
]

HOOK_SEC, TIP_SEC, OUTRO_SEC, ANIM_SEC = 2.8, 3.6, 3.2, 0.45

_font_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


_emoji_cache = {}


def emoji_img(text, height):
    """Render colour emoji (Noto only works at size 109) then scale."""
    key = (text, height)
    if key in _emoji_cache:
        return _emoji_cache[key]
    f = ImageFont.truetype(FONT_EMOJI, 109)
    tmp = Image.new("RGBA", (140 * len(text) + 40, 160), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((20, 10), text, font=f, embedded_color=True)
    tmp = tmp.crop(tmp.getbbox())
    scale = height / tmp.height
    img = tmp.resize((max(1, int(tmp.width * scale)), height), Image.LANCZOS)
    _emoji_cache[key] = img
    return img


def wrap(draw, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def gradient(c1, c2, t):
    """Diagonal gradient that slowly drifts with time t (seconds)."""
    shift = 0.15 * math.sin(t * 0.8)
    small = Image.new("RGB", (2, 64))
    px = small.load()
    for y in range(64):
        a = min(1, max(0, y / 63 + shift))
        col = tuple(int(c1[i] + (c2[i] - c1[i]) * a) for i in range(3))
        px[0, y] = px[1, y] = col
    return small.resize((W, H), Image.BILINEAR)


def ease(x):
    x = min(1, max(0, x))
    return 1 - (1 - x) ** 3


def text_block(layer, lines, fnt, y, alpha, fill=(255, 255, 255), line_gap=1.18, shadow=True):
    d = ImageDraw.Draw(layer)
    lh = int(fnt.size * line_gap)
    for i, line in enumerate(lines):
        tw = d.textlength(line, font=fnt)
        x = (W - tw) / 2
        if shadow:
            d.text((x + 5, y + i * lh + 6), line, font=fnt, fill=(0, 0, 0, int(70 * alpha)))
        d.text((x, y + i * lh), line, font=fnt, fill=fill + (int(255 * alpha),))
    return y + len(lines) * lh


def card(layer, box, alpha):
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle(box, radius=48, fill=(255, 255, 255, int(235 * alpha)))


def render_slide(base_t, local_t, slide, video, idx, total):
    c1, c2 = video["bg"]
    img = gradient(c1, c2, base_t).convert("RGBA")
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    p = ease(local_t / ANIM_SEC)
    p2 = ease((local_t - 0.25) / ANIM_SEC)
    dy = int((1 - p) * 120)
    max_w = W - 220  # keep clear of TikTok's right-side buttons

    kind = slide[0]
    if kind == "hook":
        _, emo, title = slide
        e = emoji_img(emo, int(230 * (0.6 + 0.4 * p)))
        layer.alpha_composite(e, ((W - e.width) // 2, 420 + dy))
        f = font(FONT_BLACK, 104)
        lines = wrap(d, title.upper(), f, max_w)
        text_block(layer, lines, f, 760 + dy, p)
    elif kind == "tip":
        _, n, emo, title, body = slide
        # number badge
        bf = font(FONT_BLACK, 64)
        d.ellipse((W / 2 - 70, 300 + dy, W / 2 + 70, 440 + dy), fill=(255, 255, 255, int(255 * p)))
        lbl = str(n)
        d.text((W / 2 - d.textlength(lbl, font=bf) / 2, 330 + dy), lbl, font=bf, fill=c1 + (int(255 * p),))
        # card
        tf, bf2 = font(FONT_BLACK, 92), font(FONT_BOLD, 56)
        tlines = wrap(d, title, tf, max_w - 80)
        blines = wrap(d, body, bf2, max_w - 80)
        card_h = 300 + len(tlines) * 110 + len(blines) * 72
        top = 500 + dy
        card(layer, (90, top, W - 90, top + card_h), p)
        e = emoji_img(emo, 180)
        e2 = e.copy()
        e2.putalpha(e.getchannel("A").point(lambda a: int(a * p)))
        layer.alpha_composite(e2, ((W - e.width) // 2, top + 50))
        y = text_block(layer, tlines, tf, top + 260, p, fill=(30, 30, 40), shadow=False)
        text_block(layer, blines, bf2, y + 20 + int((1 - p2) * 40), p2, fill=(80, 80, 95), shadow=False)
    else:  # outro
        _, emo, title, sub = slide
        e = emoji_img(emo, int(200 * (0.6 + 0.4 * p)))
        layer.alpha_composite(e, ((W - e.width) // 2, 480 + dy))
        f, sf = font(FONT_BLACK, 92), font(FONT_BOLD, 58)
        y = text_block(layer, wrap(d, title, f, max_w), f, 760 + dy, p)
        text_block(layer, wrap(d, sub, sf, max_w), sf, y + 40, p2)

    # progress bar at the top
    prog = (idx + min(1, local_t / slide_len(slide))) / total
    d.rounded_rectangle((90, 140, W - 90, 156), radius=8, fill=(255, 255, 255, 80))
    d.rounded_rectangle((90, 140, 90 + int((W - 180) * prog), 156), radius=8, fill=(255, 255, 255, 230))

    img.alpha_composite(layer)
    return img.convert("RGB")


def slide_len(slide):
    return {"hook": HOOK_SEC, "tip": TIP_SEC, "outro": OUTRO_SEC}[slide[0]]


def build(video):
    slides = [("hook",) + video["hook"]]
    for i, (emo, title, body) in enumerate(video["tips"], 1):
        slides.append(("tip", i, emo, title, body))
    slides.append(("outro",) + video["outro"])

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, video["slug"] + ".mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t = 0.0
    for idx, s in enumerate(slides):
        n = int(slide_len(s) * FPS)
        for f in range(n):
            frame = render_slide(t, f / FPS, s, video, idx, len(slides))
            proc.stdin.write(frame.tobytes())
            t += 1 / FPS
    proc.stdin.close()
    proc.wait()
    print("wrote", path, f"({t:.1f}s)")


if __name__ == "__main__":
    for v in VIDEOS:
        build(v)
