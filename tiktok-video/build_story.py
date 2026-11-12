"""Timeline + audio mix for story.html ("Ahmed in Italy" episode).

Usage: python3 build_story.py <voice_dir> <out_dir>
Voice clips (Kokoro Italian, 24 kHz): v1 v2 v3 v4 r1 r2 r3 r4 v9 v10 (.wav)
Writes <out_dir>/timeline.json and <out_dir>/mix.wav
"""
import sys, json, math
import numpy as np, soundfile as sf

VO, OUT = sys.argv[1], sys.argv[2]
SR = 24000
clips, sfx = [], []
el, scenes, speak = {}, {}, {}


def dur(name):
    return sf.info(f"{VO}/{name}.wav").duration


def say(t, name, hl=None):
    """Place a voice clip at t; optionally highlight element id `hl` while it plays."""
    x, sr = sf.read(f"{VO}/{name}.wav", dtype="float32")
    assert sr == SR, (name, sr)
    clips.append((t, x / (np.abs(x).max() + 1e-9) * 0.9))
    d = len(x) / SR
    if hl:
        speak[hl] = [round(t, 3), round(t + d, 3)]
    return t + d


# 1. hook
el.update(hk0=0.0, hk1=0.15, hk2=0.95, hk3=1.9)
sfx.append((0.0, "whoosh"))
scenes["hook"] = [0, 3.1]
t = 3.1

# 2. chat story
S = t
el["ch0"] = S + 0.05
el["b1"] = S + 0.5;  sfx.append((S + 0.5, "msg"))
e = say(S + 0.6, "v1", "sb1")
el["b2"] = e + 0.35; sfx.append((e + 0.35, "msg"))
e = say(e + 0.45, "v2", "sb2")
el["b3"] = e + 0.3;  sfx.append((e + 0.3, "boom"))
s3 = e + 0.4
e = say(s3, "v3", "sb3")
el["rx"] = s3 + 0.3
shake = [round(e - 1.6, 3), round(e - 0.2, 3)]
scenes["chat"] = [S, e + 0.9]
t = e + 0.9

# 3. STOP / explanation
S = t
flash = S
sfx.append((S, "scratch"))
el.update(st0=S + 0.05, st1=S + 0.35, st2=S + 0.9)
el["st3"] = S + 3.6
el["st4"] = S + 4.0; sfx.append((S + 4.0, "ding"))
e = say(S + 4.1, "v4", "sbox")
el["st5"] = e + 0.2
scenes["stop"] = [S, e + 2.0]
t = e + 2.0

# 4. rule
S = t
el["ru0"] = S + 0.05
c = S + 1.9
for k in (1, 2, 3, 4):
    el[f"r{k}"] = c; sfx.append((c, "pop"))
    c = say(c + 0.12, f"r{k}", f"sr{k}") + 0.45
scenes["rule"] = [S, c + 0.8]
t = c + 0.8

# 5. retry
S = t
el["rt0"] = S + 0.05
el["b4"] = S + 0.6; sfx.append((S + 0.6, "msg"))
e = say(S + 0.7, "v9", "sb4")
el["b5"] = e + 0.3; sfx.append((e + 0.3, "msg"))
e = say(e + 0.4, "v10", "sb5")
el["ok"] = e + 0.05; sfx.append((e + 0.05, "chime"))
scenes["retry"] = [S, e + 1.1]
t = e + 1.1

# 6. CTA
S = t
el.update(q1=S + 0.05, q2=S + 0.4, q3=S + 1.6, q4=S + 2.4)
sfx.append((S, "whoosh"))
total = round(S + 5.5, 3)
scenes["cta"] = [S, total + 1]

tl = {"total": total, "scenes": {k: [round(a, 3), round(b, 3)] for k, (a, b) in scenes.items()},
      "el": {k: round(v, 3) for k, v in el.items()}, "speak": speak, "shake": shake, "flash": round(flash, 3)}
json.dump(tl, open(f"{OUT}/timeline.json", "w"), indent=1)

# ---- audio
n = int(math.ceil((total + 1) * SR))
voice = np.zeros(n, "float32")
for t0, x in clips:
    s = int(t0 * SR); voice[s:s + len(x)] += x


def tone(f0, f1, d, decay, kind="sin"):
    k = np.arange(int(d * SR)) / SR
    ph = 2 * np.pi * np.cumsum(f0 + (f1 - f0) * k / d) / SR
    w = np.sin(ph) if kind == "sin" else np.sign(np.sin(ph)) * 0.5
    return (w * np.exp(-k * decay)).astype("float32")


rng = np.random.default_rng(1)
FX = {
    "msg":    [(0, tone(880, 1320, 0.12, 30)), (0.07, tone(1320, 1760, 0.12, 30))],
    "pop":    [(0, tone(500, 1100, 0.15, 25))],
    "whoosh": [(0, (rng.standard_normal(int(.35 * SR)) * np.hanning(int(.35 * SR)) * .35).astype("float32"))],
    "boom":   [(0, tone(120, 45, 0.6, 5) * 1.4)],
    "scratch": [(0, tone(1400, 200, 0.28, 4, "sq")), (0.0, (rng.standard_normal(int(.28 * SR)) * .25).astype("float32"))],
    "ding":   [(0, tone(1568, 1568, 0.5, 7))],
    "chime":  [(k * .09, tone(f, f, .6, 6) * .7) for k, f in enumerate([1046.5, 1318.5, 1568])],
}
fx = np.zeros(n, "float32")
for t0, kind in sfx:
    for dt, x in FX[kind]:
        s = int((t0 + dt) * SR); fx[s:s + len(x)] += x[: max(0, n - s)]

mix = voice + 0.25 * fx
mix = mix / (np.abs(mix).max() + 1e-9) * 0.95
sf.write(f"{OUT}/mix.wav", mix[: int(total * SR)], SR)
print("total", total)
