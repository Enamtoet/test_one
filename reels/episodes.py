"""Episode data for make_italiano_reel.py.

Each word is (top, bottom, pill, sub):
  top    - big word on the upper half of the card
  bottom - big word on the lower half (after the arrow)
  pill   - orange pill text (prefixed with "label_pr: " when label_pr is set)
  sub    - optional small grey line under the top word (None to hide)
it_index - which of top/bottom is the Italian word (used for optional voice-over)

Italian checked against dictionaries / usage guides; pronunciations are written
in Moroccan-style Arabic letters (ڤ = v, گ = hard g, پ = p).
"""

COMMON = dict(
    out2="كتبها فالكومنتير",
    follow="تابعني",
    follow2="باش تتعلم الطاليانية\nبالدارجة",
)

EPISODES = {
    1: dict(COMMON,
            hook1="إلا كنتي مغربي\nفإيطاليا...",
            hook2="راك كتهضر الطاليانية\nبلا ما تعرف!",
            count_txt="8 كلمات كتعرفهم من قبل",
            label_top="فالدارجة كنقولو", label_it="بالطاليانية", label_pr="كيتنطق",
            it_index=1,
            words=[
                ("كوزينة", "CUCINA", "كوتشينا", None),
                ("سبيطار", "OSPEDALE", "أوسپيدالي", None),
                ("بانيو", "BAGNO", "بانْيو", None),
                ("كاميو", "CAMION", "كاميون", None),
                ("طابلة", "TAVOLO", "تاڤولو", None),
                ("طوموبيل", "AUTOMOBILE", "أوتوموبيلي", None),
                ("فاميلا", "FAMIGLIA", "فاميلْيا", None),
                ("كارطة", "CARTA", "كارتا", None),
            ],
            out1="شمن كلمة فيهم\nما كنتيش عارفها؟",
            tag="EPISODIO 1"),

    2: dict(COMMON,
            hook1="أول نهار فالخدمة\nفإيطاليا؟",
            hook2="حفظ هاد 8 الجمل\nوماتخافش!",
            count_txt="جمل غادي تحتاجهم كل نهار",
            label_top="بالدارجة", label_it="بالطاليانية", label_pr="كيتنطق",
            it_index=1,
            words=[
                ("صباح الخير", "BUONGIORNO", "بوونجورنو", None),
                ("ما فهمتش", "NON HO CAPITO", "نون أو كاپيتو", None),
                ("عاودها عافاك", "PUÒ RIPETERE,\nPER FAVORE?", "پوو ريپيتيري، پير فاڤوري", None),
                ("فوقاش نبدا؟", "A CHE ORA\nCOMINCIO?", "أ كي أورا كومينتشو", None),
                ("فين نحطو؟", "DOVE LO METTO?", "دوڤي لو ميتّو", None),
                ("ساليت", "HO FINITO", "أو فينيتو", None),
                ("راني مريض اليوم", "OGGI STO MALE", "أودجي ستو مالي", None),
                ("شكرا بزاف", "GRAZIE MILLE", "گراتسيي ميلّي", None),
            ],
            out1="شمن جملة فيهم\nكتحتاجها بزاف؟",
            tag="EPISODIO 2"),

    3: dict(COMMON,
            hook1="كتعرف الفرنسية؟",
            hook2="رد بالك من هاد الكلمات\nفالطاليانية!",
            count_txt="كيتشابهو... ولكن المعنى مختلف",
            label_top="بالطاليانية", label_it="معناها", label_pr=None,
            it_index=0,
            words=[
                ("CAMERA", "بيت", "ماشي caméra", "كيتنطق: كاميرا"),
                ("SALIRE", "طلع", "ماشي salir (وسّخ)", "كيتنطق: ساليري"),
                ("FERMATA", "لاريت ديال الطوبيس", "ماشي fermé (مسدود)", "كيتنطق: فيرماتا"),
                ("PARENTI", "الأقارب", "ماشي parents (الوالدين)", "كيتنطق: پارينتي"),
                ("FIRMA", "التوقيع", "ماشي firme (شركة)", "كيتنطق: فيرما"),
                ("MACCHINA", "طوموبيل", "ماشي machine (ماكينة)", "كيتنطق: ماكّينا"),
                ("GUARDARE", "شوف", "ماشي garder (حضي)", "كيتنطق: گوارداري"),
                ("CANTINA", "لاكاڤ", "ماشي cantine (لاكانتين)", "كيتنطق: كانتينا"),
            ],
            out1="شمن كلمة\nكانت كتغلطك؟",
            tag="EPISODIO 3"),

    4: dict(COMMON,
            hook1="غادي للكويستورا؟",
            hook2="خاصك تعرف\nهاد 8 الكلمات!",
            count_txt="كلمات مهمة للأوراق ديالك",
            label_top="بالدارجة", label_it="بالطاليانية", label_pr="كيتنطق",
            it_index=1,
            words=[
                ("ورقة الإقامة", "PERMESSO\nDI SOGGIORNO", "پيرميسّو دي سودجورنو", None),
                ("الرقم الضريبي", "CODICE FISCALE", "كوديتشي فيسكالي", None),
                ("التجديد", "RINNOVO", "رينّوڤو", None),
                ("الوصل", "RICEVUTA", "ريتشيڤوتا", None),
                ("الموعد", "APPUNTAMENTO", "أپّونتامينتو", None),
                ("البصمات", "IMPRONTE\nDIGITALI", "إمپرونتي ديجيتالي", None),
                ("السكنى", "RESIDENZA", "ريزيدينتسا", None),
                ("عقد الخدمة", "CONTRATTO\nDI LAVORO", "كونتراتّو دي لاڤورو", None),
            ],
            out1="شمن كلمة\nكانت صعيبة عليك؟",
            tag="EPISODIO 4"),
}
