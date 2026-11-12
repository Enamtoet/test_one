"""Timeline + audio for kids.html (colorful animal-sounds episode for kids 9-10).

Usage: python3 build_kids.py <voice_dir> <out_dir>
Reads kids_lines.json (Kokoro: 'heart' English, 'sara' Italian; 24 kHz wavs).
"""
import sys, os, json, math
import numpy as np, soundfile as sf

VO, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
LN = {l["id"]: l for l in json.load(open(f"{HERE}/kids_lines.json"))}
SR = 24000
clips, caps, segs, events = [], [], [], []


def load(i):
    x, sr = sf.read(f"{VO}/{i}.wav", dtype="float32")
    nz = np.where(np.abs(x) > 0.02 * np.abs(x).max())[0]
    x = x[max(0, nz[0] - 500): nz[-1] + 1000]
    return x / np.abs(x).max() * 0.9


def say(t, i, cap_until=None):
    x = load(i); d = len(x) / SR
    clips.append({"id": i, "t": round(t, 3), "e": round(t + d, 3), "x": x})
    l = LN[i]
    caps.append({"t0": round(t - 0.05, 3), "t1": None, "en": l["text"] if l["lang"] == "en" else None,
                 "it": l.get("tr") if l["lang"] == "en" else l["text"], "lang": l["lang"]})
    return t + d


t = 0.05
s0 = t
t = say(t, "k01") + 0.25
t = say(t, "k02") + 0.35
segs.append({"scene": "intro", "t0": 0, "t1": t})
SOUNDS = {"dog": ("BAU BAU", "WOOF WOOF"), "cat": ("MIAO", "MEOW"), "duck": ("QUA QUA", "QUACK QUACK"), "cow": ("MUU", "MOO")}
for a in ["dog", "cat", "duck", "cow"]:
    a0 = t
    events.append({"k": "pop", "t": a0})
    t = say(t + 0.25, f"s_{a}")
    it_end = t
    t = say(t + 0.35, f"e_{a}")
    en_start = [c for c in clips if c["id"] == f"e_{a}"][0]["t"]
    t += 0.9
    segs.append({"scene": a, "t0": round(a0, 3), "t1": round(t, 3), "it": SOUNDS[a][0], "en": SOUNDS[a][1],
                 "itAt": round(a0 + 0.25 + (it_end - a0 - 0.25) * 0.55, 3), "enAt": round(en_start + (t - 0.9 - en_start) * 0.5, 3)})
    events += [{"k": "pop", "t": segs[-1]["itAt"]}, {"k": "pop2", "t": segs[-1]["enAt"]}]
q0 = t
events.append({"k": "pop", "t": q0})
t = say(t + 0.2, "q1") + 0.3
t = say(t, "s_roo")
it_at = t - 0.9
t = say(t + 0.3, "q2") + 0.2
opts_at = t
count_at = t + 0.6
for k in range(3):
    events.append({"k": "tick", "t": count_at + k})
reveal = count_at + 3.0
events.append({"k": "chime", "t": reveal})
t = say(reveal + 0.1, "ans") + 0.8
segs.append({"scene": "rooster", "t0": round(q0, 3), "t1": round(t, 3), "it": "CHICCHIRICHÌ", "itAt": round(it_at, 3),
             "opts": round(opts_at, 3), "count": round(count_at, 3), "reveal": round(reveal, 3)})
e0 = t
t = say(t + 0.1, "end") + 2.2
segs.append({"scene": "end", "t0": round(e0, 3), "t1": round(t, 3)})
total = round(t, 3)
# caption end = next caption start (or segment end)
for a, b in zip(caps, caps[1:]): a["t1"] = b["t0"]
caps[-1]["t1"] = total
# keep the quiz question on screen during the countdown
for c in caps:
    if c["en"] == LN["q2"]["text"]: c["t1"] = round(reveal, 3)

tl = {"total": total, "segs": segs, "caps": caps, "events": events,
      "speak": [{"id": c["id"], "t": c["t"], "e": c["e"]} for c in clips]}
json.dump(tl, open(f"{OUT}/timeline.json", "w"), ensure_ascii=False)

# ---- audio
n = int(math.ceil(total * SR)); k = np.arange(n) / SR
voice = np.zeros(n, "float32")
for c in clips:
    s = int(c["t"] * SR); voice[s:s + len(c["x"])] += c["x"][: n - s]
rng = np.random.default_rng(9)


def put(buf, t0, x, g=1.0):
    s = int(t0 * SR)
    if s >= n: return
    e = min(n, s + len(x)); buf[s:e] += g * x[: e - s]


def pluck(f, d=0.45, b=7):
    kk = np.arange(int(d * SR)) / SR
    return ((np.sin(2*np.pi*f*kk) + .5*np.sin(2*np.pi*2*f*kk) + .25*np.sin(2*np.pi*3*f*kk)) * np.exp(-kk * b)).astype("float32")


music = np.zeros(n, "float32")
# happy ukulele-ish loop: C G Am F, eighth-note arpeggios at 112 bpm
bpm = 112; eighth = 60 / bpm / 2
chords = [[261.6, 329.6, 392.0, 523.3], [196.0, 246.9, 293.7, 392.0], [220.0, 261.6, 329.6, 440.0], [174.6, 220.0, 261.6, 349.2]]
pattern = [0, 1, 2, 3, 2, 1, 2, 3]
i = 0; tt = 0.0
while tt < total - 0.5:
    ch = chords[(i // 8) % 4]
    in_count = reveal - 3.6 < tt < reveal
    put(music, tt, pluck(ch[pattern[i % 8]]), 0.0 if in_count else 0.5)
    if i % 8 == 0 and not in_count: put(music, tt, pluck(ch[0] / 2, 0.9, 3), 0.6)
    tt += eighth; i += 1

fx = np.zeros(n, "float32")
for e in events:
    if e["k"] in ("pop", "pop2"):
        kk = np.arange(int(.12 * SR)) / SR; f0 = 600 if e["k"] == "pop" else 800
        put(fx, e["t"], (np.sin(2*np.pi*(f0 + 900*kk/.12)*kk) * np.exp(-kk*30)).astype("float32"), 0.5)
    if e["k"] == "tick":
        kk = np.arange(int(.15 * SR)) / SR
        put(fx, e["t"], (np.sin(2*np.pi*1000*kk) * np.exp(-kk*35)).astype("float32"), 0.6)
    if e["k"] == "chime":
        for j, f in enumerate([523.3, 659.3, 784.0, 1046.5]):
            put(fx, e["t"] + j * .08, pluck(f, 1.0, 4), 0.5)

fade = np.clip(np.minimum(k / 0.3, (total - k) / 1.2), 0, 1).astype("float32")
mix = voice + 0.16 * music * fade + fx
mix = mix / np.abs(mix).max() * 0.92
sf.write(f"{OUT}/mix.wav", mix, SR)
print("total", total)
