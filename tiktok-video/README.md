# TikTok video: 8 Italian phrases you'll need every day

- `italian-8-phrases-voice.mp4`: **final video with Italian + Arabic voice-over**, 1080x1920, about 60 s
- `italian-8-phrases.mp4`: silent version (sound effects only), 40 s
- `video.html`: the source. Change the `PHRASES` list and re-render to make new episodes.

## Suggested caption
8 كلمات إيطالية ستحتاجها كل يوم 🇮🇹 احفظ الفيديو وارجع له 📌
اكتب جواب الاختبار في التعليقات 👇

#تعلم_الإيطالية #اللغة_الإيطالية #ايطاليا #italiano #imparareitaliano #عرب_ايطاليا #fyp

## Optional voice-over (record it in TikTok over the video)
- 0–3 s: «ثماني كلمات إيطالية ستحتاجها كل يوم، احفظها معي!»
- Each card (every 4 s): say the Italian word twice, slowly, then the Arabic meaning.
- Quiz (35 s): «كيف تقول شكراً بالإيطالية؟ اكتب جوابك في التعليقات!»

## How the voiced version is built
1. `voice_lines.json`: every spoken line (Arabic with diacritics for correct pronunciation)
2. `make_voice.py`: makes each line 8 times with offline voices and keeps the take Whisper understands best
3. `build_voiceover.py`: times every card to its audio and mixes voice and sound effects
4. `render_frames.js` + ffmpeg: renders `video.html` frame by frame with that timeline

## Episode 2: "Ahmed in Italy: Sono caldo 😳" (`ahmed-sono-caldo.mp4`, 40 s)
A story-format video: a chat on a hot bus in Rome, Ahmed's embarrassing mistake, STOP and explanation,
the "Ho + noun" rule (caldo/freddo/fame/sete), a retry, then a comment question and a Part 2 teaser.
Italian voices: Kokoro `if_sara` (Signora Maria) and `im_nicola` (Ahmed). Subtitles: Italian + Moroccan Darija.
Build: `make_voice.py` with `story_voice_lines.json` → `build_story.py` → `render_frames.js story.html` → ffmpeg.

Caption:
أحمد قال جملة وحدة فإيطاليا… والطوبيس كامل شاف فيه 😳🚌 واش نتا كنتي غادي تقولها؟ 👇
#تعلم_الإيطالية #ايطاليا #مغاربة_ايطاليا #عرب_ايطاليا #italiano #imparareitaliano #fyp

## Episode 3 (cinematic, no voice): "3 mistakes Arabs make in Italian" (`italian-3-mistakes.mp4`, 34 s)
Minimal premium look: dark background, film grain, Playfair Display + IBM Plex Sans Arabic, masked text reveals,
strike-through on the wrong phrase, underline on the correct one. Sound design only (`build_pro_audio.py`).
Build: `node render_frames.js pro.html <frames>` → ffmpeg with `-crf 20 -maxrate 10M`.

Caption:
3 أخطاء يقع فيها كل العرب في الإيطالية 🇮🇹 أيّ خطأ كنت تقع فيه؟ اكتب الرقم 👇
#تعلم_الإيطالية #ايطاليا #عرب_ايطاليا #italiano #imparareitaliano #learnitalian

## Episode 4: "Due ragazzi" stickman explainer (`due-ragazzi-voice.mp4` / `due-ragazzi-music.mp4`, 43 s)
Minimal black and white explainer: white pictogram figures, split-screen comparison, Italian narration (Kokoro `im_nicola`),
word-by-word Italian captions with glowing key words, and an Arabic translation under every line.
Build: `make_voice.py` with `story2_lines.json` → `build_story2.py` (add `--no-voice` for the music-only mix) → `render_frames.js story2.html` → ffmpeg.

Caption:
شابّان وصلا إلى إيطاليا بنفس الحلم… بعد سنة، واحد فقط نجح. الفرق؟ 10 دقائق في اليوم 🇮🇹
#تعلم_الإيطالية #ايطاليا #عرب_ايطاليا #مغاربة_ايطاليا #italiano #imparareitaliano

## Episode 5: cartoon skit "L'italiano è facile?" (`italiano-facile-trentatre.mp4`, 37 s)
A bored professor in an armchair: "الإيطالية سهلة، صح؟" He answers each Arabic prompt with an Italian word, then raps the
tongue-twister «Trentatré trentini entrarono a Trento, tutti e trentatré trotterellando» at a mic while a student dances.
The mouth follows the voice loudness. Original characters drawn in SVG. Italian voice: Kokoro `im_nicola`. Generated beat in the finale.
Build: `make_voice.py` with `twister_lines.json` → `build_twister.py` → `render_frames.js twister.html` → ffmpeg.

Caption:
الإيطالية سهلة؟ 😏 جرّب تقول هادي بسرعة 😂🇮🇹 سجّل ديو ووريني 🎤
#تعلم_الإيطالية #ايطاليا #scioglilingua #italiano #عرب_ايطاليا #fyp

## Episode 6 (Italians learning English): "Marco froze" stickman explainer (`marco-froze-voice.mp4` / `marco-froze-music.mp4`, 38 s)
Same stickman style as "Due ragazzi", for an Italian audience: British English narration (Kokoro `bm_george`),
English word-by-word captions with glowing key words, and an Italian translation under every line.
Build: `make_voice.py` with `story_en_lines.json` → `build_story2.py --lines story_en_lines.json` (add `--no-voice`) → `render_frames.js story_en.html` → ffmpeg.

Caption (IT):
10 anni di inglese a scuola… e a Londra non riesci a dire una parola? 😶 Il problema non sei tu. 🇬🇧
#inglese #imparareinglese #ingleseperitaliani #learnenglish #englishtips #fyp

## Episode 7 (cinqueminuti): "False friends: Giulia in London" (`false-friends-voice.mp4` / `false-friends-music.mp4`, 43 s)
Stickman style. Giulia says she grew up "in a factory" (fattoria = farm), that her "camera" is small (camera = room),
and goes to the "library" to buy a book (libreria = bookshop). Each mistake gets a split-screen ✗/✓ explanation, then a "Part 2" teaser.
Build: `make_voice.py` with `story_ff_lines.json` → `build_story2.py --lines story_ff_lines.json` (add `--no-voice`) → `render_frames.js story_ff.html` → ffmpeg.

Caption (IT):
"Sono cresciuta in una factory" 😳 3 falsi amici che TUTTI gli italiani sbagliano in inglese 🇬🇧 Quale sbagliavi tu? 👇
#inglese #falsiamici #imparareinglese #ingleseperitaliani #learnenglish #fyp

## Episode 8 (cinqueminuti): "One word cost Luca a job" (`one-word-job-voice.mp4` / `one-word-job-music.mp4`, 47 s)
Built for retention: narration starts at 0.0 s, the first sentence is fully visible on frame 1, a red REJECTED stamp
slams at 1 s (with a hit sound), then an open loop ("Guess which one, before the end") with three mystery cards that stay
on screen and flip ✓ ✓ ✗ as the story goes. False friends: sensible, parents, eventually (the real culprit, revealed last).
Build: `make_voice.py` with `story_job_lines.json` → `build_story2.py --lines story_job_lines.json --t0 0.05` (add `--no-voice`) → `render_frames.js story_job.html` → ffmpeg.

Caption (IT):
Una parola gli è costata il lavoro 😳 Indovina quale prima della fine 👀 1, 2 o 3?
#inglese #falsiamici #colloquiodilavoro #imparareinglese #ingleseperitaliani #fyp

## Episode 9 (kids 9-10, colorful): "Animals speak English too!" (`kids-animal-sounds.mp4`, 36 s)
Bright cartoon scene (sky, sun, clouds, hills, flowers) with five original animals that bounce and open their mouths when talking.
Italian voice (Kokoro `if_sara`) says the Italian sound, cheerful English voice (`af_heart`) says the English one:
bau bau → woof woof, miao → meow, qua qua → quack quack, muu → moo. Quiz: rooster (chicchirichì → ?) with A/B/C options,
3-2-1 countdown and confetti, then a "+ FOLLOW" button. Happy plucked music loop.
Build: `make_voice.py` with `kids_lines.json` → `build_kids.py` → `render_frames.js kids.html` → ffmpeg.

Caption (IT):
Lo sapevi? Anche gli animali parlano inglese! 🐶🐱🦆🐮 E il gallo come fa? Scrivi A, B o C 👇
#inglesepergiocare #ingleseperbambini #imparareinglese #animali #englishforkids
