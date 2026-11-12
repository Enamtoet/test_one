"""Build the voice-over timeline + audio mix for video.html.

Usage: python3 build_voiceover.py <voice_dir> <out_dir>
  <voice_dir> holds hook.wav, c1_it.wav, c1_ar.wav ... c8_ar.wav, quiz.wav, answer_it.wav, outro.wav
Writes <out_dir>/timeline.json (passed to setTimeline() in video.html) and <out_dir>/mix.wav.
"""
import sys, json, math
import numpy as np, soundfile as sf

VO, OUT = sys.argv[1], sys.argv[2]
SR = 22050
N_CARDS = 8


def load(name):
    x, sr = sf.read(f"{VO}/{name}.wav", dtype="float32")
    assert sr == SR, (name, sr)
    return x / (np.abs(x).max() + 1e-9) * 0.9


clips = []  # (time, samples, gain)
sfx = []    # (time, kind)


def place(t, name, gain=1.0):
    x = load(name)
    clips.append((t, x, gain))
    return len(x) / SR


# --- hook
hook_audio_at = 0.4
d = place(hook_audio_at, "hook")
hook = {"start": 0.0, "dur": round(hook_audio_at + d + 0.5, 3),
        "delay": {"a1": 0.05, "a2": 0.6, "a3": round(hook_audio_at + d * 0.62, 3)}}
sfx.append((0.0, "whoosh"))
t = hook["dur"]

# --- cards: Italian -> Arabic -> Italian again
cards = []
for i in range(1, N_CARDS + 1):
    S = t
    it1 = 0.35
    d_it = place(S + it1, f"c{i}_it")
    a = it1 + d_it + 0.45
    d_ar = place(S + a, f"c{i}_ar")
    b = a + d_ar + 0.45
    place(S + b, f"c{i}_it")
    dur = b + d_it + 1.1
    cards.append({"start": round(S, 3), "dur": round(dur, 3),
                  "delay": {"a0": 0.0, "a1": 0.05, "a2": it1, "a3": round(a, 3), "a4": round(b, 3)},
                  "speak": [[it1, round(it1 + d_it, 3)], [round(b, 3), round(b + d_it, 3)]]})
    sfx.append((S, "pop"))
    t = S + dur

# --- quiz
Q = t
q_at = 0.3
d_q = place(Q + q_at, "quiz")
reveal = q_at + d_q + 1.3          # short "think" pause before the answer
place(Q + reveal + 0.15, "answer_it")
d_o = place(Q + reveal + 1.1, "outro")
end = reveal + 1.1 + d_o + 0.6
sfx += [(Q, "whoosh"), (Q + reveal, "chime")]
total = round(Q + end, 3)
quiz = {"start": round(Q, 3), "dur": round(end + 1, 3),
        "delay": {"a1": 0.0, "a2": 0.3, "a3": 1.8, "a4": round(reveal + 1.0, 3)},
        "reveal": round(reveal, 3)}

timeline = {"hook": hook, "cards": cards, "quiz": quiz, "total": total}
json.dump(timeline, open(f"{OUT}/timeline.json", "w"), indent=1)

# --- mix
n = int(math.ceil(total * SR)) + SR
voice = np.zeros(n, "float32")
for t0, x, g in clips:
    s = int(t0 * SR)
    voice[s:s + len(x)] += x * g


def tone(f0, f1, dur, decay):
    k = np.arange(int(dur * SR)) / SR
    f = f0 + (f1 - f0) * k / dur
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-k * decay)


fx = np.zeros(n, "float32")
for t0, kind in sfx:
    if kind == "pop":
        parts = [(0, tone(500, 1100, 0.15, 25))]
    elif kind == "whoosh":
        parts = [(0, tone(300, 900, 0.25, 14))]
    else:  # chime
        parts = [(k * 0.09, tone(f, f, 0.6, 6) * 0.7) for k, f in enumerate([1046.5, 1318.5, 1568])]
    for dt, x in parts:
        s = int((t0 + dt) * SR)
        fx[s:s + len(x)] += x

mix = voice + 0.22 * fx
mix = mix / (np.abs(mix).max() + 1e-9) * 0.95
sf.write(f"{OUT}/mix.wav", mix[: int(total * SR)], SR)
print("total", total, "s")
