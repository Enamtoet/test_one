"""Timeline + audio for twister.html ("L'italiano è facile, vero?" tongue-twister skit).

Usage: python3 build_twister.py <voice_dir> <out_dir>
Voice clips (Kokoro Italian, 24 kHz): w1..w6 (single words), f1..f4 (finale lines).
Writes timeline.json (captions, scenes, expressions, per-frame mouth openness) and mix.wav.
"""
import sys, json, math
import numpy as np, soundfile as sf

VO, OUT = sys.argv[1], sys.argv[2]
SR, FPS = 24000, 30
clips, caps, ev = [], [], []          # ev: expression events
sfx = []


def load(name):
    x, sr = sf.read(f"{VO}/{name}.wav", dtype="float32")
    nz = np.where(np.abs(x) > 0.02 * np.abs(x).max())[0]
    x = x[max(0, nz[0] - 500): nz[-1] + 1000]
    return x / np.abs(x).max() * 0.9


def say(t, name):
    x = load(name); clips.append((t, x)); return t + len(x) / SR


def cap(t0, t1, text, kind="ar", pos="top", sub=None):
    caps.append({"t0": round(t0, 3), "t1": round(t1, 3), "text": text, "kind": kind, "pos": pos, "sub": sub})


# ---- part 1: armchair
t = 0.3
cap(t, t + 2.2, "الإيطالية سهلة، صح؟"); ev.append({"t": t, "e": "talk_gesture", "d": 2.0}); t += 2.2
cap(t, t + 1.3, "……"); ev.append({"t": t, "e": "closed", "d": 1.3}); t += 1.3
cap(t, t + 1.0, "كيف تقول"); t += 1.0
cap(t, t + 1.3, "«33» بالإيطالية؟"); ev.append({"t": t, "e": "sideeye", "d": 1.3}); t += 1.3

WORDS = [("w1", None, "Trentatré"),
         ("w2", "أهل ترينتو", "Trentini"),
         ("w3", "دخلوا", "Entrarono"),
         ("w4", "إلى ترينتو", "a Trento"),
         ("w5", "كلهم الثلاثة والثلاثون", "tutti e trentatré"),
         ("w6", "وهم يهرولون", "trotterellando")]
for i, (wid, ar, it) in enumerate(WORDS):
    if ar:
        cap(t, t + 1.05, ar)
        if i in (2, 4): ev.append({"t": t, "e": "sideeye", "d": 1.0})
        t += 1.05
    e = say(t + 0.05, wid)
    cap(t, e + 0.5, it, kind="it")
    if i == 5: ev.append({"t": t, "e": "eyebrow", "d": e - t + 0.5})
    t = e + 0.5
ev.append({"t": t, "e": "closed", "d": 0.5})
cap(t, t + 1.2, "…سهلة؟ 😐"); t += 1.4
part2 = t
sfx.append((part2 - 0.05, "scratch"))

# ---- part 2: mic + beat
BPM = 100; beat = 60 / BPM
t2 = part2 + 2 * beat                  # one bar of intro groove
lines = [("f1", "Trentatré trentini", "ثلاثة وثلاثون من أهل ترينتو"),
         ("f2", "entrarono a Trento,", "دخلوا إلى ترينتو،"),
         ("f3", "tutti e trentatré", "كلهم الثلاثة والثلاثون"),
         ("f4", "trotterellando!", "وهم يهرولون!")]
for fid, it, ar in lines:
    e = say(t2, fid)
    cap(t2, t2 + 4 * beat - 0.05, it, kind="it", pos="top", sub=ar)
    t2 += 4 * beat
end_music = t2 + 2 * beat
outro = t2
total = round(end_music + 2.4, 3)
cap(outro, total, "جرّب تقولها بسرعة 😂", kind="ar", pos="outro", sub="سجّل ديو ووريني 🎤")

tl = {"total": total, "part2": round(part2, 3), "outro": round(outro, 3), "beat": beat, "beat0": round(part2, 3),
      "caps": caps, "ev": [{**x, "t": round(x["t"], 3), "d": round(x["d"], 3)} for x in ev]}

# ---- audio
n = int(math.ceil((total + 0.5) * SR))
voice = np.zeros(n, "float32")
for t0, x in clips:
    s = int(t0 * SR); voice[s:s + len(x)] += x[: n - s]
# per-frame mouth openness from voice loudness
hop = SR // FPS
rms = np.array([np.sqrt(np.mean(voice[i:i + hop] ** 2)) for i in range(0, n - hop, hop)])
mouth = np.clip(rms / (np.percentile(rms[rms > 1e-4], 90) + 1e-9), 0, 1)
tl["mouth"] = [round(float(v), 2) for v in mouth]
json.dump(tl, open(f"{OUT}/timeline.json", "w"), ensure_ascii=False)

k = np.arange(n) / SR
music = np.zeros(n, "float32")
rng = np.random.default_rng(5)


def put(buf, t0, x, g=1.0):
    s = int(t0 * SR)
    if s >= n: return
    e = min(n, s + len(x)); buf[s:e] += g * x[: e - s]


def kick():
    kk = np.arange(int(.35 * SR)) / SR
    return (np.sin(2 * np.pi * (50 + 90 * np.exp(-kk * 30)) * kk) * np.exp(-kk * 9)).astype("float32")


def snare():
    kk = np.arange(int(.22 * SR)) / SR
    return ((rng.standard_normal(len(kk)) * .6 + np.sin(2 * np.pi * 190 * kk) * .5) * np.exp(-kk * 18)).astype("float32")


def hat():
    kk = np.arange(int(.05 * SR)) / SR
    x = rng.standard_normal(len(kk)); x = x - np.convolve(x, np.ones(4) / 4, "same")
    return (x * np.exp(-kk * 80) * .5).astype("float32")


def bass(f, d):
    kk = np.arange(int(d * SR)) / SR
    return (np.tanh(2 * np.sin(2 * np.pi * f * kk)) * np.exp(-kk * 2.5) * .5).astype("float32")


# groove: from part2 to end_music
bassline = [55.0, 55.0, 65.4, 49.0]   # A, A, C, G (one note per bar)
b = part2; i = 0
while b < end_music - 1e-6:
    bar, pos = divmod(i, 4)
    if pos in (0, 2): put(music, b, kick(), .9)
    if pos in (1, 3): put(music, b, snare(), .55)
    put(music, b, hat(), .5); put(music, b + beat / 2, hat(), .35)
    if pos == 0: put(music, b, bass(bassline[bar % 4], beat * 4), .6)
    b += beat; i += 1

fx = np.zeros(n, "float32")
for t0, kind in sfx:
    if kind == "scratch":
        kk = np.arange(int(.35 * SR)) / SR
        put(fx, t0, (np.sign(np.sin(2 * np.pi * (900 - 2000 * kk) * kk)) * np.exp(-kk * 6) * .25).astype("float32"))
# room tone in part 1 so it isn't dead silent
room = np.convolve(rng.standard_normal(n), np.ones(60) / 60, "same").astype("float32") * 0.02
room[int(part2 * SR):] = 0

mix = voice + 0.45 * music + fx + room
fade = np.clip((total - k) / 1.2, 0, 1).astype("float32")
mix = mix * fade
mix = mix / np.abs(mix).max() * 0.92
sf.write(f"{OUT}/mix.wav", mix[: int(total * SR)], SR)
print("total", total, "part2", round(part2, 2))
