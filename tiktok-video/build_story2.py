"""Timeline + audio for story2.html (stickman explainer, Italian narration + IT/AR captions).

Usage: python3 build_story2.py <voice_dir> <out_dir> [--no-voice] [--lines other_lines.json]
Reads story2_lines.json (or --lines) and <voice_dir>/<id>.wav (Kokoro, 24 kHz).
Lines may carry their own "scene" letter and a translation in "ar" or "tr".
Writes <out_dir>/timeline.json and <out_dir>/mix.wav (or mix_novoice.wav).
"""
import sys, os, json, re, math
import numpy as np, soundfile as sf

VO, OUT = sys.argv[1], sys.argv[2]
NO_VOICE = "--no-voice" in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
LF = sys.argv[sys.argv.index("--lines") + 1] if "--lines" in sys.argv else f"{HERE}/story2_lines.json"
LINES = json.load(open(LF))
SR = 24000

# which sentences belong to which visual scene
SCENES_DEFAULT = [("A", ["s01", "s02"]), ("B", ["s03", "s04"]), ("C", ["s05", "s06"]), ("D", ["s07"]),
          ("E", ["s08", "s09"]), ("F", ["s10", "s11"]), ("G", ["s12"]), ("H", ["s13"]), ("I", ["s14"])]
if all("scene" in l for l in LINES):
    SCENES = []
    for l in LINES:
        if not SCENES or SCENES[-1][0] != l["scene"]: SCENES.append((l["scene"], []))
        SCENES[-1][1].append(l["id"])
else:
    SCENES = SCENES_DEFAULT
scene_of = {sid: sc for sc, ids in SCENES for sid in ids}

clips, sents, stamps, ticks, reveals = [], [], [], [], []
t = float(sys.argv[sys.argv.index("--t0") + 1]) if "--t0" in sys.argv else 0.6
prev_scene = None
for ln in LINES:
    sc = scene_of[ln["id"]]
    if prev_scene and sc != prev_scene:
        t += 0.45                      # breathing room at scene changes
    x, sr = sf.read(f"{VO}/{ln['id']}.wav", dtype="float32")
    assert sr == SR
    # trim leading/trailing near-silence so word timing is tighter
    nz = np.where(np.abs(x) > 0.02 * np.abs(x).max())[0]
    x = x[max(0, nz[0] - 600): nz[-1] + 1200]
    d = len(x) / SR
    clips.append((t, x / np.abs(x).max() * 0.9))
    words = ln["text"].split()
    # word onset ~ proportional to characters before it (+ pauses after punctuation)
    weights = [len(re.sub(r"\W", "", w)) + 2 + (4 if re.search(r"[.,:?]$", w) else 0) for w in words]
    tot = sum(weights); acc = 0; wl = []; keyed = False
    for w, k in zip(words, weights):
        is_key = (not keyed) and bool(ln.get("key")) and re.sub(r"\W", "", w).lower() == ln["key"]
        keyed = keyed or is_key
        wl.append({"w": w, "t": round(t + d * acc / tot * 0.95, 3), "key": is_key})
        acc += k
    if "stamp" in ln: stamps.append(t + ln["stamp"])
    sents.append({"id": ln["id"], "scene": sc, "start": round(t, 3), "end": round(t + d, 3), "ar": ln.get("ar") or ln.get("tr"), "words": wl, "stamp": ln.get("stamp")})
    t += d + 0.35
    if ln.get("pause_after"):          # silent countdown: one tick per second
        for k in range(int(round(ln["pause_after"]))):
            ticks.append(t + k)
        sents[-1]["countdown"] = [round(t, 3), round(t + ln["pause_after"], 3)]
        t += ln["pause_after"]
        reveals.append(t)
    prev_scene = sc

total = round(t + 1.6, 3)
scenes = []
for sc, ids in SCENES:
    ss = [s for s in sents if s["scene"] == sc]
    scenes.append({"id": sc, "start": ss[0]["start"] - 0.25, "end": ss[-1]["end"] + 0.4})
for a, b in zip(scenes, scenes[1:]):
    a["end"] = b["start"]             # contiguous scenes
scenes[-1]["end"] = total
for s in scenes:
    s["start"] = round(max(0, s["start"]), 3); s["end"] = round(s["end"], 3)
scenes[0]["start"] = 0
# caption for a sentence stays until the next sentence starts
for a, b in zip(sents, sents[1:]):
    a["hold"] = b["start"]
sents[-1]["hold"] = total

json.dump({"total": total, "sentences": sents, "scenes": scenes}, open(f"{OUT}/timeline.json", "w"),
          ensure_ascii=False, indent=1)

# ---------------- audio
n = int(math.ceil(total * SR))
mix = np.zeros(n, "float32")
if not NO_VOICE:
    for t0, x in clips:
        s = int(t0 * SR); mix[s:s + len(x)] += x[: n - s]
rng = np.random.default_rng(3)
k = np.arange(n) / SR

def put(t0, x, g):
    s = int(t0 * SR); e = min(n, s + len(x)); mix[s:e] += g * x[: e - s]

def whoosh(d=0.6):
    x = rng.standard_normal(int(d * SR)).astype("float32")
    y = np.convolve(x, np.ones(24) / 24, mode="same")
    return y * np.sin(np.linspace(0, np.pi, len(y))) ** 2

def pluck(f, d=1.2):
    kk = np.arange(int(d * SR)) / SR
    return ((np.sin(2*np.pi*f*kk) + .35*np.sin(2*np.pi*2*f*kk)) * np.exp(-kk * 3)).astype("float32")

for s in scenes[1:]:
    put(s["start"] - 0.25, whoosh(), 0.45)
def thump():
    kk = np.arange(int(0.7 * SR)) / SR
    body = np.sin(2 * np.pi * (45 + 120 * np.exp(-kk * 25)) * kk) * np.exp(-kk * 6)
    crack = rng.standard_normal(len(kk)) * np.exp(-kk * 40) * 0.5
    return (body + crack).astype("float32")
for st in stamps:
    put(st, thump(), 0.9)
def tick():
    kk = np.arange(int(0.12 * SR)) / SR
    return (np.sin(2 * np.pi * 1100 * kk) * np.exp(-kk * 40)).astype("float32")
def ding():
    kk = np.arange(int(1.0 * SR)) / SR
    return sum(np.sin(2 * np.pi * f * kk) * np.exp(-kk * 5) for f in (880, 1320)).astype("float32") * 0.5
for tk in ticks:
    put(tk, tick(), 0.7)
for rv in reveals:
    put(rv - 0.05, ding(), 0.5)
# soft "piano" motif: one pluck per sentence start, gentle minor arpeggio
notes = [220.0, 261.6, 329.6, 392.0, 329.6, 261.6]
for i, s in enumerate(sents):
    put(s["start"] - 0.05, pluck(notes[i % len(notes)]), 0.10 if not NO_VOICE else 0.22)
# warm pad bed
bed = (np.sin(2*np.pi*110*k) + .6*np.sin(2*np.pi*164.8*k) + .4*np.sin(2*np.pi*220.5*k)) * (0.6 + 0.4*np.sin(2*np.pi*k/7))
fade = np.minimum(1, np.minimum(k / 2, (total - k) / 1.5))
mix += (bed * fade * (0.035 if not NO_VOICE else 0.07)).astype("float32")
mix = mix / np.abs(mix).max() * 0.92
sf.write(f"{OUT}/{'mix_novoice' if NO_VOICE else 'mix'}.wav", mix, SR)
print("total", total)
