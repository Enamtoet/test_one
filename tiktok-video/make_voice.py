"""Generate each voice line N times with Piper voices (sherpa-onnx 1.x) and keep the take Whisper transcribes best.
Usage: python3 make_voice.py <models_dir> <voice_dir containing lines.json> <N>
Models (GitHub releases of k2-fsa/sherpa-onnx): tts-models/vits-piper-ar_JO-kareem-medium,
tts-models/vits-piper-it_IT-paola-medium, asr-models/sherpa-onnx-whisper-base
"""
import sys, json, re, difflib, unicodedata, numpy as np, soundfile as sf, sherpa_onnx
M, vo, N = sys.argv[1], sys.argv[2], int(sys.argv[3])
V = {'ar':'vits-piper-ar_JO-kareem-medium/ar_JO-kareem-medium','it':'vits-piper-it_IT-paola-medium/it_IT-paola-medium',
     'dii':'vits-piper-ar_JO-SA_dii-high/ar_JO-SA_dii-high','miro':'vits-piper-ar_JO-SA_miro-high/ar_JO-SA_miro-high',
     'miro2':'vits-piper-ar_JO-SA_miro_V2-high/ar_JO-SA_miro_V2-high'}
LANG = {'it':'it'}  # every other voice is Arabic
KOKORO = {'sara': 35, 'nicola': 36, 'michael': 16, 'george': 26, 'heart': 3}  # kokoro-multi-lang-v1_0 speaker ids
KLANG = {'sara': 'it', 'nicola': 'it', 'michael': 'en-us', 'george': 'en', 'heart': 'en-us'}
def mk_tts(lang):
    if lang in KOKORO:
        d=f"{M}/kokoro-multi-lang-v1_0"
        return sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
            kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(model=d+'/model.onnx',voices=d+'/voices.bin',tokens=d+'/tokens.txt',
                data_dir=d+'/espeak-ng-data',dict_dir=d+'/dict',lexicon=(d+'/lexicon-gb-en.txt' if lang=='george' else d+'/lexicon-us-en.txt'),lang=KLANG[lang]),num_threads=4)))
    b=f"{M}/{V[lang]}"; d=b.rsplit('/',1)[0]
    return sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=b+'.onnx',tokens=d+'/tokens.txt',data_dir=d+'/espeak-ng-data'),num_threads=4)))
W=f"{M}/sherpa-onnx-whisper-base"
def mk_asr(lang):
    return sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f"{W}/base-encoder.onnx",decoder=f"{W}/base-decoder.onnx",
        tokens=f"{W}/base-tokens.txt",language=lang,task="transcribe",num_threads=4)
T={}; A={l:mk_asr(l) for l in ('ar','it','en')}
def norm(s):
    s=''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c))
    s=s.replace("33","trentatre")
    s=s.replace("10","ten").replace("5","five").replace("3","three")
    s=s.replace('أ','ا').replace('إ','ا').replace('ة','ه').replace('ى','ي').lower()
    return re.sub(r"[^\w]","",s)
for it in json.load(open(f"{vo}/lines.json")):
    best=None
    for k in range(N):
        v=it.get('voice',it['lang'])
        if v not in T: T[v]=mk_tts(v)
        a=T[v].generate(it['text'],sid=KOKORO.get(v,0),speed=it.get('speed',1.0))
        x=np.array(a.samples,dtype='float32'); sr=a.sample_rate
        pad=np.concatenate([np.zeros(int(sr*.3),'float32'),x,np.zeros(int(sr*.5),'float32')])
        s=A[it['lang']].create_stream(); s.accept_waveform(sr,pad); A[it['lang']].decode_stream(s)
        txt=s.result.text.strip(); score=difflib.SequenceMatcher(None,norm(it['text']),norm(txt)).ratio()
        if best is None or score>best[0]: best=(score,x,sr,txt)
        if score>=0.99: break
    sf.write(f"{vo}/{it['id']}.wav",best[1],best[2])
    print(f"{it['id']:10} {best[0]:.2f} {len(best[1])/best[2]:.2f}s | {best[3]}",flush=True)
