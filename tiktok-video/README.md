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
