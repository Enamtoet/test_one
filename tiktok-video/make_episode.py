"""Build one cinqueminuti episode from series/<name>.json.

JSON: {"name": "...", "lines": [ ...narration lines with "scene", "text", "tr", "key", optional "pause_after"/"stamp"... ],
       "scenes": { "A": {"type": "dialog"|"versus"|"round"|"native"|"big", ...}, ... } }
Usage: python3 make_episode.py series/<name>.json <work_dir> <models_dir> [--preview t1,t2,...]
Outputs <name>-voice.mp4 and <name>-music.mp4 next to this script (or preview frames in <work_dir>/preview).
"""
import sys, os, json, subprocess, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
spec_path, work, models = sys.argv[1], sys.argv[2], sys.argv[3]
ep = json.load(open(spec_path)); name = ep["name"]
vo, tl_dir = f"{work}/{name}/voice", f"{work}/{name}/tl"
os.makedirs(vo, exist_ok=True); os.makedirs(tl_dir, exist_ok=True)
lines_file = f"{work}/{name}/lines.json"
lines = [dict(l, lang="en", voice=l.get("voice", "george"), speed=l.get("speed", 0.95)) for l in ep["lines"]]
json.dump(lines, open(lines_file, "w"), ensure_ascii=False, indent=1)
# voices (only lines whose wav is missing or whose text changed)
todo = [l for l in lines if not (os.path.exists(f"{vo}/{l['id']}.json") and
        json.load(open(f"{vo}/{l['id']}.json")) == {"text": l["text"], "speed": l["speed"]})]
if todo:
    tmp = f"{work}/{name}/todo"; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
    json.dump(todo, open(f"{tmp}/lines.json", "w"), ensure_ascii=False)
    out = subprocess.run([sys.executable, "-I", f"{HERE}/make_voice.py", models, tmp, "1"], capture_output=True, text=True).stdout
    print("\n".join(l for l in out.splitlines() if l[:1].isalnum() and "|" in l))
    for l in todo:
        shutil.copy(f"{tmp}/{l['id']}.wav", f"{vo}/{l['id']}.wav")
        json.dump({"text": l["text"], "speed": l["speed"]}, open(f"{vo}/{l['id']}.json", "w"))
for nv in ([], ["--no-voice"]):
    subprocess.run([sys.executable, f"{HERE}/build_story2.py", vo, tl_dir, "--lines", lines_file, "--t0", "0.05", *nv], check=True, capture_output=True)
tl = json.load(open(f"{tl_dir}/timeline.json")); tl["spec"] = ep["scenes"]
json.dump(tl, open(f"{tl_dir}/timeline.json", "w"), ensure_ascii=False)
print(name, "total", tl["total"])
html = f"{HERE}/episode.html"
if "--preview" in sys.argv:
    pv = f"{work}/{name}/preview"; shutil.rmtree(pv, ignore_errors=True); os.makedirs(pv)
    subprocess.run(["node", f"{HERE}/render_frames.js", html, pv, f"{tl_dir}/timeline.json", "--preview", sys.argv[sys.argv.index("--preview") + 1]], check=True, capture_output=True)
    sys.exit()
fr = f"{work}/{name}/frames"; shutil.rmtree(fr, ignore_errors=True); os.makedirs(fr)
subprocess.run(["node", f"{HERE}/render_frames.js", html, fr, f"{tl_dir}/timeline.json"], check=True, capture_output=True)
for mix, suffix in (("mix", "voice"), ("mix_novoice", "music")):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", "30", "-i", f"{fr}/f%05d.jpg", "-i", f"{tl_dir}/{mix}.wav",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
                    "-shortest", "-movflags", "+faststart", f"{HERE}/{name}-{suffix}.mp4"], check=True)
shutil.rmtree(fr)
print("done", name)
