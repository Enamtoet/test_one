"""5 problem-solving reels for Arabs in Italy (Modern Standard Arabic), each with its own visual idea.

Usage: python3 make_problems.py OUT_DIR [--preview] [name ...]
Names: tfr, naspi, medico, patente, cittadinanza

Facts (sources in the chat; rules can change, verify before posting):
- TFR: yearly quota = annual pay / 13.5, paid at the end of employment for any reason (art. 2120 c.c.).
- NASpI: involuntary unemployment, 13 weeks of contributions in the previous 4 years, apply within 68 days
  (INPS or patronato); voluntary resignation excluded unless for just cause.
- SSN: enrol at the ASL with permesso (or renewal receipt) + codice fiscale + residence/domicile, choose a GP.
- Driving licence: foreign licence valid 1 year after taking residence; then convert if an agreement exists
  (e.g. Morocco) or take the Italian exam. Check the MIT list.
- Citizenship by residence: 10 years legal residence (non-EU) + B1 certificate (CILS, CELI, PLIDA, CERT.IT...).
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reel_common import *  # noqa


def base(bg, t, show_logo=True):
    img = bg.copy()
    if show_logo:
        img.alpha_composite(LOGO, (W - LOGO.width - 36, 36))
    return img


# =================================================================== 1) TFR - piggy bank
BG1 = make_bg((18, 70, 50), (6, 24, 18))


def piggy(fill, broken=0.0):
    im = Image.new("RGBA", (620, 520), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pink, dk = (255, 150, 180, 255), (220, 100, 140, 255)
    if broken < 0.01:
        d.ellipse((60, 110, 540, 450), fill=pink)
        d.ellipse((480, 220, 600, 330), fill=pink); d.ellipse((540, 255, 560, 275), fill=dk); d.ellipse((565, 255, 585, 275), fill=dk)
        d.polygon([(150, 140), (190, 60), (240, 130)], fill=pink)
        for x in (140, 230, 360, 440):
            d.rounded_rectangle((x, 400, x + 50, 500), 18, fill=dk)
        d.ellipse((420, 200, 445, 225), fill=(40, 30, 40, 255))
        d.rounded_rectangle((250, 120, 370, 138), 9, fill=(120, 50, 80, 255))
        # fill level window
        d.rounded_rectangle((180, 230, 420, 380), 30, fill=(255, 230, 240, 255))
        h = 150 * fill
        d.rounded_rectangle((180, 380 - h, 420, 380), 30, fill=YELLOW + (255,))
        for k in range(int(fill * 6)):
            d.ellipse((200 + (k % 3) * 70, 345 - (k // 3) * 40, 250 + (k % 3) * 70, 375 - (k // 3) * 40), outline=(200, 150, 20, 255), width=4)
    else:
        q = broken
        for k, (dx, dy, rot) in enumerate(((-140, -60, -30), (150, -40, 25), (-100, 120, 15), (120, 110, -20))):
            piece = Image.new("RGBA", (240, 180), (0, 0, 0, 0)); dp = ImageDraw.Draw(piece)
            dp.pieslice((0, 0, 240, 180), 45 + 90 * k, 135 + 90 * k, fill=pink)
            piece = piece.rotate(rot * q * 3, expand=True)
            im.alpha_composite(piece, (int(190 + dx * q * 1.6), int(170 + dy * q * 1.6)))
    return im


def coin(r=34):
    im = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, 2 * r - 1, 2 * r - 1), fill=(255, 200, 40, 255), outline=(200, 140, 20, 255), width=5)
    d.text((r, r - 2), "€", font=ImageFont.truetype(DJV, int(r * 1.1)), fill=(170, 110, 10, 255), anchor="mm")
    return im


COIN = coin()
MONTHS = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]


def f_tfr(t):
    img = base(BG1, t)
    if t < 3.0:
        a, s = appear(t, 0.1); txt(img, "تركت عملك؟", W / 2, 520, 120, WHITE, a, s)
        a, s = appear(t, 0.9); txt(img, "إيطاليا مدينة لك\nبالمال!", W / 2, 900, 120, YELLOW, a, s)
        a, s = appear(t, 1.8); txt(img, "TFR", W / 2, 1250, 200, GREEN, a, s)
    elif t < 9.0:
        tl = t - 3.0
        txt(img, "كل شهر يُدّخر جزء من راتبك", W / 2, 300, fit("كل شهر يُدّخر جزء من راتبك", 70, W - 100), WHITE)
        m = min(11, int(tl / 0.45))
        fill = min(1.0, tl / 5.4)
        paste_c(img, piggy(fill), W / 2, 980)
        for k in range(m + 1):
            p = clamp((tl - k * 0.45) / 0.4)
            if p < 1:
                paste_c(img, COIN, W / 2 - 10, 560 + 300 * ease(p), 1.0)
        txt(img, MONTHS[m], W / 2, 1380, 96, YELLOW)
        txt(img, "اسم هذا المال: TFR", W / 2, 1530, 60, (200, 230, 210), ease((tl - 1) / 0.4), 1, bold=False)
    elif t < 14.0:
        tl = t - 9.0
        a, s = appear(tl, 0.0); txt(img, "كم؟", W / 2, 330, 130, YELLOW, a, s)
        a, s = appear(tl, 0.5)
        c = card(960, 300); d = ImageDraw.Draw(c)
        d.text((480, 100), "راتبك السنوي ÷ 13.5", font=font(78), fill=DARK + (255,), anchor="mm", direction="rtl")
        d.text((480, 220), "≈ راتب شهر تقريباً عن كل سنة", font=font(54, False), fill=(0, 120, 70, 255), anchor="mm", direction="rtl")
        paste_c(img, alpha_mul(c, a), W / 2, 700, 0.9 + 0.1 * s)
        a, s = appear(tl, 1.8)
        c2 = card(960, 200, (255, 245, 210, 245)); d2 = ImageDraw.Draw(c2)
        d2.text((480, 60), "مثال", font=font(40, False), fill=(140, 110, 40, 255), anchor="mm", direction="rtl")
        d2.text((480, 135), "20.000€ ÷ 13,5 ≈ 1.481€", font=font(70), fill=DARK + (255,), anchor="mm")
        paste_c(img, alpha_mul(c2, a), W / 2, 1050, 0.9 + 0.1 * s)
        a, s = appear(tl, 3.0)
        txt(img, "(مبلغ إجمالي قبل الضرائب)", W / 2, 1230, 46, (200, 220, 210), a, 1, bold=False)
    elif t < 19.5:
        tl = t - 14.0
        a, s = appear(tl, 0.0)
        txt(img, "يُدفع لك عند نهاية العمل", W / 2, 300, fit("يُدفع لك عند نهاية العمل", 80, W - 100), WHITE, a, s)
        br = ease((tl - 0.5) / 0.6)
        paste_c(img, piggy(1.0, br), W / 2, 760)
        if br > 0:
            rng = np.random.default_rng(4)
            for k in range(26):
                ang = rng.uniform(0, 2 * math.pi); sp = rng.uniform(250, 600)
                x = W / 2 + math.cos(ang) * sp * br; y = 760 + math.sin(ang) * sp * br * 0.6 + 400 * br ** 2
                paste_c(img, COIN, x, y, 0.8)
        row(img, 1180, "استقلت؟ لك الحق في TFR", ease((tl - 1.6) / 0.35), "ok")
        row(img, 1350, "فُصلت؟ لك الحق في TFR", ease((tl - 2.2) / 0.35), "ok")
    elif t < 22.5:
        tl = t - 19.5
        a, s = appear(tl, 0.0); txt(img, "نصيحة", W / 2, 420, 110, YELLOW, a, s)
        a, s = appear(tl, 0.4)
        txt(img, "لم تستلمه؟ لا تسكت!\nاسأل نقابة (sindacato)\nأو Patronato مجاناً", W / 2, 850, 78, WHITE, a, s)
    else:
        outro(img, t - 22.5, "أرسل الفيديو لشخص\nترك عمله")
    return img


EV_TFR = [(0.1, "pop"), (0.9, "pop"), (1.8, "ding")] + [(3.0 + k * 0.45 + 0.35, "coin") for k in range(12)] + \
         [(9.0, "pop"), (9.5, "pop"), (10.8, "ding"), (14.5, "crash"), (14.6, "win"), (15.6, "ding"), (16.2, "ding"),
          (19.5, "pop"), (22.5, "ding")]

# =================================================================== 2) NASpI - hourglass 68 days
BG2 = make_bg((24, 40, 90), (8, 12, 34))


def hourglass(p):
    im = Image.new("RGBA", (440, 640), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    wood = (150, 100, 55, 255)
    d.rounded_rectangle((20, 0, 420, 50), 20, fill=wood); d.rounded_rectangle((20, 590, 420, 640), 20, fill=wood)
    glass = (210, 230, 255, 90)
    d.polygon([(60, 50), (380, 50), (232, 320), (208, 320)], fill=glass, outline=(220, 235, 255, 255))
    d.polygon([(208, 320), (232, 320), (380, 590), (60, 590)], fill=glass, outline=(220, 235, 255, 255))
    sand = (255, 205, 80, 255)
    top = 1 - p
    if top > 0.01:
        yt = 320 - 260 * top
        hw = 160 * (320 - yt) / 270
        d.polygon([(220 - hw, yt), (220 + hw, yt), (226, 318), (214, 318)], fill=sand)
    if p > 0.01:
        yb = 590 - 220 * p
        hw = 160 * (yb - 320) / 270
        d.polygon([(220 - hw, yb), (220 + hw, yb), (380, 588), (60, 588)], fill=sand)
    if 0.0 < p < 1.0:
        d.line((220, 320, 220, 590 - 220 * p), fill=sand, width=6)
    return im


def f_naspi(t):
    img = base(BG2, t)
    if t < 3.0:
        a, s = appear(t, 0.1); txt(img, "فقدت عملك؟", W / 2, 520, 120, WHITE, a, s)
        a, s = appear(t, 1.0); txt(img, "عندك 68 يوماً فقط!", W / 2, 860, 110, YELLOW, a, s)
        a, s = appear(t, 1.8); txt(img, "NASpI", W / 2, 1200, 190, BLUE, a, s)
    elif t < 9.0:
        tl = t - 3.0
        p = clamp(tl / 4.6)
        paste_c(img, hourglass(p), W / 2, 820)
        days = int(round(68 * (1 - p)))
        col = WHITE if days > 20 else (RED if days < 8 else ORANGE)
        txt(img, f"{days}", W / 2, 1300, 170, col)
        txt(img, "يوماً لتقديم الطلب", W / 2, 1450, 62, WHITE, bold=False)
        txt(img, "تعويض البطالة = NASpI", W / 2, 300, 72, YELLOW)
        if p >= 1:
            paste_c(img, stamp("قد تخسر حقك!", RED, 96, 760, 180), W / 2, 820, 2 - ease((tl - 4.6) / 0.25))
    elif t < 15.5:
        tl = t - 9.0
        a, s = appear(tl, 0.0); txt(img, "من له الحق؟", W / 2, 330, 104, YELLOW, a, s)
        row(img, 500, "فقدت العمل بدون إرادتك", ease((tl - 0.5) / 0.35), "ok", "فصل أو انتهاء العقد")
        row(img, 720, "13 أسبوعاً من الاشتراكات", ease((tl - 1.4) / 0.35), "ok", "خلال آخر 4 سنوات")
        row(img, 940, "الاستقالة العادية: لا", ease((tl - 2.3) / 0.35), "no", "إلا لسبب عادل (giusta causa)")
    elif t < 20.5:
        tl = t - 15.5
        a, s = appear(tl, 0.0); txt(img, "كيف؟", W / 2, 330, 120, YELLOW, a, s)
        row(img, 520, "قدّم الطلب على موقع INPS", ease((tl - 0.4) / 0.35), "ok")
        row(img, 700, "أو عبر Patronato مجاناً", ease((tl - 1.0) / 0.35), "ok")
        row(img, 880, "قدّم بسرعة!", ease((tl - 1.6) / 0.35), "warn", "في أول 8 أيام = يبدأ من اليوم الثامن")
    else:
        outro(img, t - 20.5, "أرسل الفيديو لشخص\nفقد عمله")
    return img


EV_NASPI = [(0.1, "pop"), (1.0, "thud"), (1.8, "ding")] + [(3.0 + k * 0.5, "tick") for k in range(10)] + \
           [(7.6, "thud"), (9.0, "pop"), (9.5, "ding"), (10.4, "ding"), (11.3, "buzz"), (15.5, "pop"), (15.9, "ding"),
            (16.5, "ding"), (17.1, "pop"), (20.5, "ding")]

# =================================================================== 3) Medico di base - folder + health card
BG3 = make_bg((10, 80, 90), (4, 26, 34))


def doc_icon(label, col):
    im = card(300, 360, (255, 255, 255, 255), 24); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 300, 70), fill=col + (255,))
    d.text((150, 36), label, font=font(fit(label, 34, 270)), fill=WHITE + (255,), anchor="mm", direction="rtl" if is_ar(label) else "ltr")
    for k in range(5):
        d.rounded_rectangle((30, 110 + k * 45, 30 + [240, 180, 220, 150, 200][k], 126 + k * 45), 8, fill=(210, 215, 225, 255))
    return im


DOCS = [doc_icon("Permesso / Ricevuta", (40, 90, 150)), doc_icon("Codice fiscale", (30, 140, 90)), doc_icon("Residenza", (200, 120, 30))]


def health_card(flip):
    w = 760
    im = card(w, 470, (230, 240, 250, 255), 34); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, 90), fill=(30, 110, 160, 255))
    d.text((w / 2, 46), "TESSERA SANITARIA", font=font(46), fill=WHITE + (255,), anchor="mm")
    d.ellipse((60, 140, 160, 240), fill=(200, 160, 40, 255))
    for k in range(4):
        d.rounded_rectangle((200, 150 + k * 60, 200 + [460, 380, 420, 300][k], 178 + k * 60), 10, fill=(190, 205, 220, 255))
    d.text((w / 2, 420), "Medico di base ✓".replace("✓", ""), font=font(44), fill=(30, 110, 160, 255), anchor="mm")
    sx = abs(math.cos(math.pi * (1 - flip))) if flip < 1 else 1
    if flip < 0.5:
        back_ = card(w, 470, (40, 90, 150, 255), 34)
        return back_.resize((max(1, int(w * sx)), 470))
    return im.resize((max(1, int(w * sx)), 470))


def doctor(r=150):
    im = Image.new("RGBA", (2 * r, 2 * r + 80), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((r * 0.25, r * 1.35, r * 1.75, 2 * r + 80), 60, fill=WHITE + (255,))
    d.ellipse((r * 0.55, r * 0.25, r * 1.45, r * 1.25), fill=(230, 185, 150, 255))
    d.chord((r * 0.5, r * 0.15, r * 1.5, r * 0.85), 180, 360, fill=(80, 60, 50, 255))
    for x in (0.82, 1.18):
        d.ellipse((r * x - 9, r * 0.72, r * x + 9, r * 0.9), fill=(40, 30, 30, 255))
    d.arc((r * 0.82, r * 0.85, r * 1.18, r * 1.1), 20, 160, fill=(150, 50, 50, 255), width=6)
    d.arc((r * 0.7, r * 1.45, r * 1.3, r * 2.0), 0, 180, fill=(60, 60, 70, 255), width=8)
    d.ellipse((r * 0.93, r * 1.92, r * 1.07, r * 2.06), fill=(60, 60, 70, 255))
    d.rectangle((r * 1.35, r * 1.55, r * 1.55, r * 1.75), fill=RED + (255,))
    return im


DOC = doctor()


def f_medico(t):
    img = base(BG3, t)
    if t < 3.0:
        a, s = appear(t, 0.1); txt(img, "مريض في إيطاليا…", W / 2, 560, 110, WHITE, a, s)
        a, s = appear(t, 1.0); txt(img, "ولا تعرف أين تذهب؟", W / 2, 760, 100, YELLOW, a, s)
        a, s = appear(t, 1.6); paste_c(img, DOC, W / 2, 1220, s)
    elif t < 8.0:
        tl = t - 3.0
        a, s = appear(tl, 0.0); txt(img, "الحل: طبيب العائلة", W / 2, 330, 96, WHITE, a, s)
        a, s = appear(tl, 0.4); txt(img, "Medico di base", W / 2, 470, 96, YELLOW, a, s)
        paste_c(img, health_card(ease((tl - 1.0) / 0.8)), W / 2, 900)
        a, s = appear(tl, 2.2); txt(img, "الزيارة عنده مجانية", W / 2, 1290, 84, GREEN, a, s)
    elif t < 14.0:
        tl = t - 8.0
        a, s = appear(tl, 0.0); txt(img, "3 وثائق فقط:", W / 2, 330, 104, YELLOW, a, s)
        for k, dimg in enumerate(DOCS):
            p = ease((tl - 0.5 - 0.9 * k) / 0.45)
            if p > 0.01:
                x = 210 + k * 330
                paste_c(img, dimg, x, 700 - (1 - p) * 500, 0.95)
        a, s = appear(tl, 3.6)
        txt(img, "الإقامة (أو الوصل) · الرقم الضريبي · السكن", W / 2, 1050,
            fit("الإقامة (أو الوصل) · الرقم الضريبي · السكن", 54, W - 100, False), WHITE, a, s, bold=False)
        a, s = appear(tl, 4.2)
        txt(img, "(residenza أو domicilio)", W / 2, 1140, 46, (190, 220, 230), a, s, bold=False)
    elif t < 19.0:
        tl = t - 14.0
        a, s = appear(tl, 0.0); txt(img, "ثم:", W / 2, 330, 110, YELLOW, a, s)
        row(img, 500, "اذهب إلى ASL", ease((tl - 0.4) / 0.35), "ok", "مكتب الصحة في مدينتك")
        row(img, 720, "اختر طبيبك", ease((tl - 1.2) / 0.35), "ok", "scelta del medico di base")
        row(img, 940, "لأطفالك: طبيب أطفال", ease((tl - 2.0) / 0.35), "ok", "Pediatra")
    elif t < 22.0:
        tl = t - 19.0
        a, s = appear(tl, 0.0); txt(img, "نصيحة", W / 2, 520, 110, YELLOW, a, s)
        a, s = appear(tl, 0.4)
        txt(img, "الوثائق قد تختلف حسب المنطقة\nاتصل بـ ASL قبل أن تذهب", W / 2, 850, 70, WHITE, a, s)
    else:
        outro(img, t - 22.0, "أرسل الفيديو لشخص\nجديد في إيطاليا")
    return img


EV_MED = [(0.1, "pop"), (1.0, "pop"), (1.6, "ding"), (3.0, "pop"), (4.0, "whoosh"), (5.2, "ding")] + \
         [(8.5 + 0.9 * k + 0.4, "thud") for k in range(3)] + [(11.6, "ding"), (14.0, "pop"), (14.4, "ding"),
                                                              (15.2, "ding"), (16.0, "ding"), (19.0, "pop"), (22.0, "ding")]

# =================================================================== 4) Patente - burning fuse + fork
BG4 = make_bg((90, 34, 20), (26, 10, 8))


def licence():
    im = card(700, 430, (245, 236, 210, 255), 30); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 700, 80), fill=(150, 60, 40, 255))
    d.text((350, 42), "DRIVING LICENCE", font=font(44), fill=WHITE + (255,), anchor="mm")
    d.rounded_rectangle((40, 120, 220, 360), 18, fill=(210, 200, 175, 255))
    d.ellipse((90, 150, 170, 230), fill=(170, 155, 130, 255)); d.chord((65, 240, 195, 380), 180, 360, fill=(170, 155, 130, 255))
    for k in range(4):
        d.rounded_rectangle((260, 140 + k * 55, 260 + [380, 300, 340, 220][k], 166 + k * 55), 10, fill=(200, 190, 165, 255))
    return im


LIC = licence()


def car_icon():
    im = Image.new("RGBA", (300, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 60, 290, 130), 30, fill=(230, 60, 60, 255))
    d.polygon([(70, 60), (110, 15), (200, 15), (240, 60)], fill=(230, 60, 60, 255))
    d.polygon([(90, 58), (118, 25), (150, 25), (150, 58)], fill=(180, 220, 250, 255))
    d.polygon([(160, 58), (160, 25), (195, 25), (222, 58)], fill=(180, 220, 250, 255))
    for x in (70, 230):
        d.ellipse((x - 30, 105, x + 30, 160), fill=(30, 30, 35, 255))
    return im


CAR = car_icon()


def f_patente(t):
    img = base(BG4, t)
    if t < 3.2:
        a, s = appear(t, 0.1); txt(img, "تسوق في إيطاليا\nبرخصة بلدك؟", W / 2, 520, 110, WHITE, a, s)
        a, s = appear(t, 1.2); paste_c(img, CAR, W / 2 + (1 - a) * 600, 1000, 1.4)
        a, s = appear(t, 2.0); txt(img, "انتبه!", W / 2, 1350, 130, YELLOW, a, s)
    elif t < 10.0:
        tl = t - 3.2
        a, s = appear(tl, 0.0)
        txt(img, "صالحة سنة واحدة فقط", W / 2, 300, 92, YELLOW, a, s)
        txt(img, "بعد تسجيل سكنك (residenza)", W / 2, 420, 60, WHITE, a, s, bold=False)
        paste_c(img, LIC, W / 2, 780)
        d = ImageDraw.Draw(img)
        x0, x1, y = 120, 960, 1110
        p = clamp((tl - 0.8) / 4.2)
        d.line((x0, y, x1, y), fill=(120, 90, 70, 255), width=10)
        xf = x0 + (x1 - x0) * p
        d.line((xf, y, x1, y), fill=(200, 170, 130, 255), width=10)
        for k in range(12):
            xm = x0 + (x1 - x0) * k / 11
            d.text((xm, y + 50), str(k + 1), font=font(34), fill=(220, 200, 180, 255) if xm > xf else (120, 90, 70, 255), anchor="mm")
        if p < 1:
            for k in range(8):
                ang = (tl * 20 + k * 0.8); r_ = 18 + 10 * math.sin(tl * 30 + k)
                d.ellipse((xf + math.cos(ang) * r_ - 7, y + math.sin(ang) * r_ - 7, xf + math.cos(ang) * r_ + 7, y + math.sin(ang) * r_ + 7), fill=(255, 200, 60, 255))
        txt(img, "شهر", W / 2, 1230, 46, (220, 200, 180), bold=False)
        if p >= 1:
            paste_c(img, stamp("SCADUTA", RED, 110), W / 2, 780, 2 - ease((tl - 5.0) / 0.25))
            a, s = appear(tl, 5.4)
            txt(img, "بعد سنة: لا يمكنك القيادة بها", W / 2, 1400, fit("بعد سنة: لا يمكنك القيادة بها", 66, W - 100), WHITE, a, s)
    elif t < 17.0:
        tl = t - 10.0
        a, s = appear(tl, 0.0); txt(img, "الحل؟ طريقان:", W / 2, 300, 100, YELLOW, a, s)
        d = ImageDraw.Draw(img)
        p = ease((tl - 0.4) / 0.8)
        d.line((W / 2, 1500, W / 2, 1500 - 300 * p), fill=(80, 80, 90, 255), width=90)
        if p >= 1:
            q = ease((tl - 1.2) / 0.8)
            d.line((W / 2, 1210, W / 2 - 260 * q, 1210 - 300 * q), fill=(80, 80, 90, 255), width=90)
            d.line((W / 2, 1210, W / 2 + 260 * q, 1210 - 300 * q), fill=(80, 80, 90, 255), width=90)
        for k, (side, title, l2, col, t0) in enumerate(((1, "بلدك عنده اتفاقية\nمع إيطاليا؟ (مثل المغرب)", "حوّل الرخصة\nبدون امتحان", GREEN, 2.0),
                                                       (-1, "لا توجد اتفاقية؟", "امتحان الرخصة\nالإيطالية", ORANGE, 3.4))):
            a, s = appear(tl, t0)
            if a > 0.01:
                c = card(470, 420); dc = ImageDraw.Draw(c)
                dc.rounded_rectangle((0, 0, 469, 30), 20, fill=col + (255,))
                dc.multiline_text((235, 140), title, font=font(42), fill=DARK + (255,), anchor="mm", align="center", direction="rtl", spacing=12)
                dc.multiline_text((235, 320), l2, font=font(50), fill=col + (255,), anchor="mm", align="center", direction="rtl", spacing=12)
                paste_c(img, alpha_mul(c, a), W / 2 + side * 255, 650, 0.9 + 0.1 * s)
    elif t < 21.0:
        tl = t - 17.0
        a, s = appear(tl, 0.0); txt(img, "القائمة المحدّثة للدول:", W / 2, 520, 86, YELLOW, a, s)
        a, s = appear(tl, 0.5); txt(img, "mit.gov.it", W / 2, 720, 110, WHITE, a, s)
        a, s = appear(tl, 1.0); txt(img, "أو Motorizzazione Civile", W / 2, 900, 70, WHITE, a, s, bold=False)
    else:
        outro(img, t - 21.0, "أرسل الفيديو لشخص\nيسوق برخصة بلده")
    return img


EV_PAT = [(0.1, "pop"), (1.2, "whoosh"), (2.0, "thud"), (3.2, "pop"), (4.0, "fuse"), (5.2, "fuse"), (6.4, "fuse"),
          (8.2, "thud"), (8.6, "buzz"), (10.0, "pop"), (10.4, "whoosh"), (11.2, "whoosh"), (12.0, "ding"), (13.4, "ding"),
          (17.0, "pop"), (17.5, "ding"), (21.0, "ding")]

# =================================================================== 5) Cittadinanza - 10-step staircase + B1 lock
BG5 = make_bg((50, 24, 80), (14, 8, 28))


def padlock(open_p, label="B1"):
    im = Image.new("RGBA", (260, 320), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    lift = 50 * open_p
    d.arc((50, 10 - lift, 210, 170 - lift), 180, 360, fill=(200, 200, 210, 255), width=26)
    d.line((63, 90 - lift, 63, 140), fill=(200, 200, 210, 255), width=26) if open_p < 0.3 else None
    d.line((197, 90 - lift, 197, 140), fill=(200, 200, 210, 255), width=26)
    d.rounded_rectangle((20, 130, 240, 310), 30, fill=YELLOW + (255,))
    d.text((130, 222), label, font=font(90), fill=(90, 60, 10, 255), anchor="mm")
    return im


def f_citt(t):
    img = base(BG5, t)
    if t < 3.0:
        a, s = appear(t, 0.1); txt(img, "تحلم بالجنسية الإيطالية؟", W / 2, 560, fit("تحلم بالجنسية الإيطالية؟", 100, W - 100), WHITE, a, s)
        a, s = appear(t, 1.2); txt(img, "انتبه لهذا الشرط!", W / 2, 860, 100, YELLOW, a, s)
        a, s = appear(t, 1.8); paste_c(img, padlock(0), W / 2, 1250, s)
    elif t < 10.5:
        tl = t - 3.0
        a, s = appear(tl, 0.0); txt(img, "1) عشر سنوات إقامة قانونية", W / 2, 300, fit("1) عشر سنوات إقامة قانونية", 76, W - 100), WHITE, a, s)
        d = ImageDraw.Draw(img)
        sw, sh = 86, 78
        x0, y0 = 90, 1600
        year = min(10, int(tl / 0.55))
        for k in range(10):
            x = x0 + k * sw; y = y0 - k * sh
            col = (120, 90, 170) if k >= year else (255, 200, 50)
            d.rectangle((x, y - sh, x + sw, y0 + 20), fill=col + (255,))
            d.text((x + sw / 2, y - sh / 2), str(k + 1), font=font(40), fill=DARK + (255,), anchor="mm")
        k = max(0, year - 1)
        bx, by = x0 + k * sw + sw / 2, y0 - k * sh - sh - 40 - 20 * abs(math.sin(tl * 8))
        d.ellipse((bx - 30, by - 30, bx + 30, by + 30), fill=WHITE + (255,), outline=GREEN + (255,), width=6)
        # door at the top
        dx, dy = 900, y0 - 10 * sh - 290
        d.rounded_rectangle((dx - 90, dy, dx + 90, dy + 240), 16, fill=(130, 70, 40, 255))
        d.text((dx, dy - 40), "IT", font=font(40), fill=WHITE + (255,), anchor="mm")
        if year >= 10:
            paste_c(img, padlock(0), dx, dy + 120, 0.5)
    elif t < 16.0:
        tl = t - 10.5
        a, s = appear(tl, 0.0); txt(img, "2) الشرط الذي ينساه الكثيرون:", W / 2, 320, fit("2) الشرط الذي ينساه الكثيرون:", 72, W - 100), WHITE, a, s)
        op = ease((tl - 3.0) / 0.5)
        paste_c(img, padlock(op), W / 2, 760, 1.6)
        a, s = appear(tl, 1.0); txt(img, "شهادة لغة إيطالية B1", W / 2, 1150, 92, YELLOW, a, s)
        a, s = appear(tl, 1.8); txt(img, "نسخة خاصة بالجنسية (Cittadinanza)", W / 2, 1300, fit("نسخة خاصة بالجنسية (Cittadinanza)", 58, W - 100), WHITE, a, s, bold=False)
    elif t < 21.0:
        tl = t - 16.0
        a, s = appear(tl, 0.0); txt(img, "من أين؟ جهات معترف بها:", W / 2, 320, fit("من أين؟ جهات معترف بها:", 80, W - 100), YELLOW, a, s)
        for k, nm in enumerate(("CILS", "CELI", "PLIDA", "CERT.IT")):
            p = ease((tl - 0.5 - 0.4 * k) / 0.35)
            if p > 0.01:
                c = card(440, 170, (255, 255, 255, 245)); dc = ImageDraw.Draw(c)
                dc.text((220, 85), nm, font=font(70), fill=(80, 40, 130, 255), anchor="mm")
                paste_c(img, alpha_mul(c, p), W / 2 + (-235 if k % 2 == 0 else 235), 600 + (k // 2) * 210, 0.9 + 0.1 * back(p))
        a, s = appear(tl, 2.4)
        txt(img, "السعر مثلاً: حوالي 100€ (CILS)", W / 2, 1100, fit("السعر مثلاً: حوالي 100€ (CILS)", 60, W - 100), WHITE, a, s, bold=False)
        a, s = appear(tl, 3.0)
        txt(img, "بعض الحالات معفاة: اسأل الـ Prefettura", W / 2, 1230, fit("بعض الحالات معفاة: اسأل الـ Prefettura", 52, W - 100), (210, 190, 240), a, s, bold=False)
    else:
        outro(img, t - 21.0, "تابعنا لتصل إلى B1\nبالعربي!", "أرسل الفيديو لشخص يحلم بالجنسية")
    return img


EV_CITT = [(0.1, "pop"), (1.2, "pop"), (1.8, "thud")] + [(3.0 + k * 0.55, "tick") for k in range(10)] + \
          [(8.6, "ding"), (10.5, "pop"), (11.5, "ding"), (13.5, "win"), (16.0, "pop")] + \
          [(16.5 + 0.4 * k, "pop") for k in range(4)] + [(18.4, "ding"), (21.0, "ding")]

VIDEOS = {
    "tfr": (f_tfr, 25.5, EV_TFR, [3.0 + 2.0, 6.0, 9.0 + 2.8, 14.0 + 3.0, 19.5 + 1.5, 23.5]),
    "naspi": (f_naspi, 23.5, EV_NASPI, [2.5, 6.0, 8.0, 9.0 + 3.5, 15.5 + 2.5, 22.0]),
    "medico": (f_medico, 25.0, EV_MED, [2.5, 3.0 + 3.0, 8.0 + 4.6, 14.0 + 3.0, 19.0 + 1.5, 23.5]),
    "patente": (f_patente, 24.0, EV_PAT, [2.6, 3.2 + 2.5, 3.2 + 6.2, 10.0 + 4.5, 17.0 + 2.0, 22.5]),
    "cittadinanza": (f_citt, 24.0, EV_CITT, [2.6, 3.0 + 3.0, 3.0 + 6.5, 10.5 + 4.0, 16.0 + 3.6, 22.5]),
}

if __name__ == "__main__":
    od = sys.argv[1]; os.makedirs(od, exist_ok=True)
    names = [a for a in sys.argv[2:] if not a.startswith("--")] or list(VIDEOS)
    for i, nm in enumerate(names):
        fn, dur, ev, pts = VIDEOS[nm]
        if "--preview" in sys.argv:
            preview(os.path.join(od, f"prev_{nm}.png"), fn, pts, cols=6)
        else:
            render(os.path.join(od, f"ciao_khoya_{nm}.mp4"), fn, dur, ev, seed=i + 3)
            print("done", nm, flush=True)
