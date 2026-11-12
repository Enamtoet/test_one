"""Subtle sound design for pro.html (no voice). Usage: python3 build_pro_audio.py out.wav"""
import sys, numpy as np, soundfile as sf
SR = 44100; HOOK, MIS, OUT = 3.4, 8.6, 5.2; TOTAL = HOOK + 3 * MIS + OUT
n = int(TOTAL * SR); mix = np.zeros(n, "float32"); rng = np.random.default_rng(7)

def put(t, x, g):
    s = int(t * SR); e = min(n, s + len(x)); mix[s:e] += g * x[: e - s]

def whoosh(d=0.7):
    x = rng.standard_normal(int(d * SR)).astype("float32")
    # sweep a one-pole low-pass for an airy "swish"
    a = np.linspace(0.02, 0.35, len(x)) ** 1.5; y = np.zeros_like(x); acc = 0.0
    for i in range(len(x)): acc += a[i] * (x[i] - acc); y[i] = acc
    return y * np.sin(np.linspace(0, np.pi, len(y))) ** 2

def hit():   # soft cinematic low hit
    k = np.arange(int(1.6 * SR)) / SR
    return (np.sin(2 * np.pi * (55 - 15 * k) * k) * np.exp(-k * 2.8)).astype("float32")

def tick():
    k = np.arange(int(0.08 * SR)) / SR
    return (np.sin(2 * np.pi * 2400 * k) * np.exp(-k * 70)).astype("float32")

def bell(f=880):
    k = np.arange(int(1.4 * SR)) / SR
    return ((np.sin(2*np.pi*f*k) + .4*np.sin(2*np.pi*2*f*k) + .2*np.sin(2*np.pi*3.01*f*k)) * np.exp(-k * 3.5)).astype("float32")

put(0.0, hit(), 0.9); put(0.3, whoosh(0.9), 0.5)
for i in range(3):
    s = HOOK + i * MIS
    put(s - 0.35, whoosh(), 0.55)
    put(s + 0.1, hit(), 0.45)
    put(s + 1.7, tick(), 0.35)            # strike-through
    put(s + 4.0, bell(880), 0.22)         # correct underline
put(HOOK + 3 * MIS - 0.35, whoosh(), 0.55); put(HOOK + 3 * MIS + 0.1, hit(), 0.6)
# gentle low drone bed for atmosphere
k = np.arange(n) / SR
bed = (np.sin(2*np.pi*73.4*k) + .5*np.sin(2*np.pi*110*k)) * (0.5 + 0.5*np.sin(2*np.pi*k/9)) * 0.05
fade = np.minimum(1, np.minimum(k / 1.5, (TOTAL - k) / 1.5))
mix += (bed * fade).astype("float32")
mix = mix / np.abs(mix).max() * 0.8
sf.write(sys.argv[1], np.stack([mix, mix], 1), SR)
