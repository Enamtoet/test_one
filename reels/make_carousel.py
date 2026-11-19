"""Carousel post (Instagram 4:5 / TikTok photo mode): 8 mistakes Arabs make in Italian.

Usage: python3 make_carousel.py OUT_DIR
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FB, FS = os.path.join(HERE, "Cairo-Black.ttf"), os.path.join(HERE, "Cairo-SemiBold.ttf")
W, H = 1080, 1350
GREEN, RED, WHITE = (0, 140, 70), (210, 40, 50), (255, 255, 255)
YELLOW, DARK, CREAM = (255, 205, 70), (28, 30, 40), (250, 245, 234)
NAVY = (16, 34, 64)

MISTAKES = [
    dict(title="حرف P", wrong="Vorrei una basta", right="Vorrei una pasta",
         note="العربية ليس فيها P\nفتقول BASTA (كفى!) بدل PASTA", tip="P = B بدون صوت"),
    dict(title="العُمر", wrong="Sono 25 anni", right="Ho 25 anni",
         note="في الإيطالية العُمر بفعل \"أملك\" (avere)\nوليس بفعل \"أكون\" (essere)", tip="Quanti anni hai?  =  كم عمرك؟"),
    dict(title="الجوع", wrong="Sono fame", right="Ho fame",
         note="الجوع والعطش والبرد بفعل avere:", tip="Ho fame · Ho sete · Ho freddo"),
    dict(title="الشدّة!", wrong="Il mio nono", right="Il mio nonno",
         note="الحرف المضاعف يغيّر المعنى:\nnono = التاسع · nonno = جدّي", tip="استعمل الشدّة: نونّو"),
    dict(title="حرف Z", wrong="Grasie", right="Grazie",
         note="z في الإيطالية تُنطق غالباً \"تس\"", tip="گراتسيه"),
    dict(title="المذكر والمؤنث", wrong="La problema", right="Il problema",
         note="كلمات تنتهي بـ a لكنها مذكّرة:", tip="il problema · il sistema · il tema"),
    dict(title="مع المدير", wrong="Ciao capo!", right="Buongiorno!",
         note="Ciao للأصدقاء فقط\nمع المدير والغرباء: Buongiorno / Salve", tip="ومعهم استعمل Lei وليس tu"),
    dict(title="كاميرا؟", wrong="La camera = كاميرا", right="La camera = الغرفة",
         note="الكاميرا بالإيطالية:", tip="la macchina fotografica"),
]

_fc = {}


def font(sz, bold=True):
    k = (max(8, int(sz)), bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FB if bold else FS, k[0])
    return _fc[k]


def is_ar(s):
    return any("؀" <= c <= "ۿ" for c in s)


_D = ImageDraw.Draw(Image.new("L", (1, 1)))


def measure(s, size, bold=True):
    bb = _D.multiline_textbbox((0, 0), s, font=font(size, bold), align="center", spacing=8,
                               direction="rtl" if is_ar(s) else "ltr")
    return bb[2] - bb[0]


def fit(s, size, maxw, bold=True):
    while size > 20 and max(measure(x, size, bold) for x in s.split("\n")) > maxw:
        size -= 2
    return size


def text(d, xy, s, size, col, bold=True, anchor="mm", spacing=10):
    lines = s.split("\n")
    lh = size * 1.45
    x, y = xy
    y0 = y - lh * (len(lines) - 1) / 2
    for i, ln in enumerate(lines):
        d.text((x, y0 + i * lh), ln, font=font(size, bold), fill=tuple(col) + (255,), anchor=anchor,
               direction="rtl" if is_ar(ln) else "ltr")


def shadowed(base, im, xy, blur=16, off=10, alpha=70):
    sh = Image.new("RGBA", (im.width + 4 * blur, im.height + 4 * blur), (0, 0, 0, 0))
    sh.paste((0, 0, 0, alpha), (2 * blur, 2 * blur + off, 2 * blur + im.width, 2 * blur + im.height + off), im.getchannel("A"))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(sh, (xy[0] - 2 * blur, xy[1] - 2 * blur))
    base.alpha_composite(im, xy)


LOGO = Image.open(os.path.join(HERE, "logo", "ciao_khoya_watermark.png")).convert("RGBA")


def logo(sz):
    return LOGO.resize((sz, int(LOGO.height * sz / LOGO.width)), Image.LANCZOS)


def base_slide(dark=False):
    img = Image.new("RGBA", (W, H), (NAVY if dark else CREAM) + (255,))
    d = ImageDraw.Draw(img)
    for i, c in enumerate(((0, 146, 70), WHITE, (206, 43, 55))):
        d.rectangle((i * W / 3, 0, (i + 1) * W / 3, 16), fill=c + (255,))
    return img


def footer(img, page, total, dark=False):
    d = ImageDraw.Draw(img)
    lg = logo(120)
    img.alpha_composite(lg, (60, H - lg.height - 40))
    col = (200, 210, 230) if dark else (120, 115, 105)
    d.text((W - 60, H - 80), "احفظ المنشور 💾".replace("💾", "").strip(), font=font(36), fill=col + (255,), anchor="rm",
           direction="rtl")
    d.text((W / 2, H - 80), f"{page}/{total}", font=font(34), fill=col + (255,), anchor="mm")


def swipe_arrow(d, cx, cy, col):
    d.line((cx + 70, cy, cx - 60, cy), fill=col + (255,), width=14)
    d.polygon([(cx - 90, cy), (cx - 45, cy - 32), (cx - 45, cy + 32)], fill=col + (255,))


def cover(total):
    img = base_slide(dark=True)
    d = ImageDraw.Draw(img)
    text(d, (W / 2, 250), "8 أخطاء", 170, YELLOW)
    text(d, (W / 2, 470), "يقع فيها كل العرب\nفي الإيطالية", 92, WHITE)
    # wrong vs right teaser
    for k, (s, col, mark) in enumerate((("Sono 25 anni", RED, "✗"), ("Ho 25 anni", GREEN, "✓"))):
        y = 720 + k * 170
        box = Image.new("RGBA", (760, 140), (0, 0, 0, 0)); db = ImageDraw.Draw(box)
        db.rounded_rectangle((0, 0, 759, 139), 40, fill=WHITE + (255,))
        db.rounded_rectangle((0, 0, 139, 139), 40, fill=col + (255,))
        db.rectangle((100, 0, 139, 139), fill=col + (255,))
        db.text((70, 70), mark, font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80),
                fill=WHITE + (255,), anchor="mm")
        db.text((450, 70), s, font=font(66), fill=col + (255,), anchor="mm")
        if k == 0:
            db.line((200, 72, 700, 72), fill=RED + (255,), width=8)
        shadowed(img, box, (160, y), alpha=120)
    text(d, (W / 2, 1110), "هل تقع فيها أنت؟ اسحب", 64, WHITE)
    swipe_arrow(d, W / 2, 1200, YELLOW)
    lg = logo(130)
    img.alpha_composite(lg, (W - lg.width - 50, 40))
    return img


def mistake_slide(i, m, total):
    img = base_slide()
    d = ImageDraw.Draw(img)
    # header
    d.rounded_rectangle((60, 60, W - 60, 190), 50, fill=NAVY + (255,))
    d.ellipse((W - 200, 70, W - 90, 180), fill=YELLOW + (255,))
    d.text((W - 145, 125), str(i + 1), font=font(70), fill=NAVY + (255,), anchor="mm")
    d.text((W - 240, 125), "خطأ: " + m["title"], font=font(fit("خطأ: " + m["title"], 64, 700)), fill=WHITE + (255,),
           anchor="rm", direction="rtl")
    # wrong / right boxes
    mk = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
    for k, (s, col, mark, lab) in enumerate(((m["wrong"], RED, "✗", "خطأ"), (m["right"], GREEN, "✓", "صحيح"))):
        y = 260 + k * 250
        box = Image.new("RGBA", (960, 210), (0, 0, 0, 0)); db = ImageDraw.Draw(box)
        db.rounded_rectangle((0, 0, 959, 209), 46, fill=WHITE + (255,), outline=col + (255,), width=6)
        db.rounded_rectangle((760, 0, 959, 209), 46, fill=col + (255,))
        db.rectangle((760, 0, 800, 209), fill=col + (255,))
        db.text((860, 90), mark, font=mk, fill=WHITE + (255,), anchor="mm")
        db.text((860, 170), lab, font=font(34), fill=WHITE + (255,), anchor="mm", direction="rtl")
        fs = fit(s, 76, 680)
        db.text((380, 105), s, font=font(fs), fill=col + (255,), anchor="mm", direction="rtl" if is_ar(s) and not s[0].isascii() else "ltr")
        if k == 0:
            tw = measure(s, fs)
            db.line((380 - tw / 2 - 10, 108, 380 + tw / 2 + 10, 108), fill=RED + (230,), width=7)
        shadowed(img, box, (60, y))
    # explanation
    text(d, (W / 2, 880), m["note"], fit(m["note"], 54, 940, False), DARK, bold=False)
    # tip pill
    tip = m["tip"]
    ts = fit(tip, 58, 880)
    tw = measure(tip, ts) + 100
    pill = Image.new("RGBA", (int(tw), 120), (0, 0, 0, 0)); dp = ImageDraw.Draw(pill)
    dp.rounded_rectangle((0, 0, tw - 1, 119), 60, fill=YELLOW + (255,))
    dp.text((tw / 2, 58), tip, font=font(ts), fill=NAVY + (255,), anchor="mm", direction="rtl" if is_ar(tip) and not tip[0].isascii() else "ltr")
    shadowed(img, pill, (int(W / 2 - tw / 2), 1050))
    footer(img, i + 2, total)
    return img


def last_slide(total):
    img = base_slide(dark=True)
    d = ImageDraw.Draw(img)
    text(d, (W / 2, 260), "كم خطأ كنت\nتقع فيه؟", 110, WHITE)
    text(d, (W / 2, 520), "اكتب الرقم في التعليقات", 72, YELLOW)
    nums = "0 1 2 3 4 5 6 7 8".split()
    for k, nn in enumerate(nums):
        cx = 140 + k * 100
        d.ellipse((cx - 40, 640 - 40, cx + 40, 640 + 40), fill=WHITE + (255,))
        d.text((cx, 636), nn, font=font(50), fill=NAVY + (255,), anchor="mm")
    lg = logo(340)
    img.alpha_composite(lg, (int(W / 2 - lg.width / 2), 760))
    text(d, (W / 2, 1110), "تابعنا لتتعلم الإيطالية بالعربي", 62, WHITE)
    text(d, (W / 2, 1200), "وأرسل المنشور لصديق عربي في إيطاليا", 48, (200, 210, 230), bold=False)
    return img


if __name__ == "__main__":
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    total = len(MISTAKES) + 2
    slides = [cover(total)] + [mistake_slide(i, m, total) for i, m in enumerate(MISTAKES)] + [last_slide(total)]
    for k, s in enumerate(slides):
        s.convert("RGB").save(os.path.join(od, f"{k + 1:02d}.png"))
    sheet = Image.new("RGB", (270 * 5, 338 * 2), (0, 0, 0))
    for k, s in enumerate(slides):
        sheet.paste(s.convert("RGB").resize((270, 338)), ((k % 5) * 270, (k // 5) * 338))
    sheet.save(os.path.join(od, "preview.png"))
    print("ok", len(slides))
