# 🧠 ملف معرفة النظام — "تعليق سريع / وثائقي / مانغا"
> كل معرفة النظام في مكان واحد: الفلسفة، المعادلات، الأوامر المُختبرة، الدروس المؤلمة.
> الكود المصدري يعيش في `vtsys/` و `vt/` (مصدر وحيد للحقيقة — لا نسخ مكررة هنا).
> آخر تحديث: 2026-09-14 · البيئة المرجعية: Linux sandbox (Python 3.13، 2 cores، ~2GB RAM، Snapshot سقف ~128MB)

---

## 0) الفكرة الأم (الإيجاز التنفيذي)
النظام يحول أي فيديو ترند (أو قصة نصية) إلى **باكج نشر كامل** عبر ثلاثة خطوط إنتاج:

| الخط | المدخل | المخرج | الموديول |
|---|---|---|---|
| 🅰 شورت تعليق | فيديو يوتيوب مترجم | 9:16 فويس-أوفر خليجي + ثامبنيل + تعليقات جاهزة | `vt/pipeline.py` |
| 🅱 وثائقي صامت | فيديو بلا كلام (بناء/طبيعة/ASMR) | 16:9 حلقة مروية بفصحى درامية | `vt/documentary.py` |
| 🅲 مانغا صوتيّة | قصة نصية | Motion comic من لوحات مولّدة | `vtsys/manga.py` + `vtsys/render.py::render_manga_panels` |

**المبدأ الحاكم لكل الخطوط:** *الصوت يقود التايم-لاين.* مدة كل جملة صوتية مقاسة فعلياً = مدة لقطتها/نافذتها. لا تخمين.

---

## 1) محرّك القرار — "إمتى أعلّق؟"
### 1.1 المدخلات (مجانية، بدون API)
`yt-dlp --dump-json` يعطي: `upload_date, view_count, like_count, comment_count, duration, tags, categories, automatic_captions`.

### 1.2 معادلة النقاط (0–100، الحد 70)
```
age_h    = ساعات منذ النشر
velocity = views / max(age_h,1)
conv_r   = comments / views
eng_r    = likes / views

s_age  = 30 إن age_h≤6 | 24 ≤24 | 16 ≤72 | 8 ≤168 | 3 ≤720 | 0 غير ذلك
s_vel  = clamp(25 * log10(velocity+1) / log10(20000), 0, 25)
s_conv = clamp(conv_r * 2500, 0, 20)
s_eng  = clamp(eng_r * 400, 0, 15)
s_niche= min(10, 5 * عدد كلمات النيش الموجودة في title+tags+categories)
total  = s_age+s_vel+s_conv+s_eng+s_niche
الحكم: ≥70 "انشر الحين 🔥" | ≥50 "مناسب بس مو أولوية 🟡" | غير ذلك "تجاوزه ❌"
```
التنفيذ: `vtsys/decision.py::score` (الموحّد) و `vt/decision_engine.py::score_video` (الأصلي).

### 1.3 قراءة النتائج (حكمة ميدانية)
- فيديو قديم (>أسبوع) بنقاط منخفضة = **نافذة التعليق فاتت**، لكن قد يكون ممتازاً كـ*مصدر لمحتوى مشتق* (فيديو/مانغا). القرار منخفض ≠ محتوى سيء.
- مثال مسجل: فيديو 2.1M مشاهدة عمره 39 يوم → 40/100 "تجاوزه" للتعليق، لكنه أنتج شورت ناجح.

### 1.4 طبقة السلوك البشري (إلزامية قبل أي نشر فعلي)
- تأخير `random.gauss(µ,σ)` قبل النشر — البوتات تنشر بدقة مشبوهة.
- حصة ≤ 5 تعليقات/يوم/حساب، فواصل 40–90 دقيقة.
- ساعات جمهورك فقط (خليجي: 16:00–24:00).
- قاعدة `video_id+account` لمنع التكرار.
- تنويع كلمات الافتتاح (النمط المتكرر يُكشف).
- **قانون المنصات:** نشر تلقائي على يوتيوب = Data API + OAuth فقط. تيك توك لا يملك API عام للنشر → النظام يجهّز والنشر بضغطة بشرية.
- التنفيذ: `vtsys/queue.py`.

---

## 2) الخط 🅰 — شورت التعليق (فيديو مترجم)
### 2.1 الخطوات
1. `--dump-json` → القرار.
2. ترجمة: `--skip-download --write-auto-subs --sub-langs "en.*,ar" --sub-format json3` → parser (`vtsys/youtube.py::load_json3`) يدمج الأسطر المكررة ويحتفظ بالتوقيتات.
3. سكريبت 6 مقاطع بأنواع: `hook, summary, insight, opinion, detail, cta`.
   - بدون مفتاح LLM: قوالب خليجية (أنظر §2.4). مع `OPENROUTER_API_KEY`: prompt يرجع JSON من 6 مقاطع.
4. TTS لكل مقطع → `durations.json` (المدة الحقيقية) → concat بـ concat-demuxer = `vo.mp3`.
5. قص نافذة من المصدر: تحميل كامل بـ yt-dlp ثم `-ss START -t DUR+1.5 -c copy` محلياً (⚠️ §7.3).
6. كابشنز ASS + بانر PNG + شريط تقدم + ميكس → تصدير 1080×1920@30.

### 2.2 سلسلة ffmpeg المُختبرة (9:16)
```
[0:v]fps=30,scale=3840:2160:flags=lanczos,
     zoompan=z='1+0.12*on/1800':x='(iw-iw/zoom)*(0.20+0.60*on/1800)':y='(ih-ih/zoom)/2':d=1:s=1080x1920:fps=30,setsar=1[base];
[base][2:v]overlay=0:36[tmp];
[tmp]ass=captions.ass[t2];
[t2]drawbox=x=0:y=1906:w='min(t/TOTAL,1)*1080':h=14:color=0xFFC93C@0.95:t=fill[vout];
[0:a]volume=0.12[bg]; [1:a]volume=1.0[vc];
[vc][bg]amix=inputs=2:duration=first:normalize=0,afade=t=out:st=END-1.5:d=1.4[aout]
```
تصدير: `libx264 -crf 20 -pix_fmt yuv420p -profile:v high -level 4.1 -c:a aac -b:a 160k -ar 48000 -ac 2 -movflags +faststart`
التنفيذ: `vtsys/render.py::render_short`.

### 2.3 أسلوب التعليق الخليجي (نبرة)
جمل قصيرة، ضمير متكلّم، رأي صريح، سؤال ختامي. ممنوع: الفصحى الإعلامية، الإطالة، نسخ وصف الفيديو.

### 2.4 قوالب السكريبت (Fallback بدون LLM)
```
hook:    "لقيت فيديو جاب {views} مشاهدة، وقعدت له {dur} دقيقة كاملة. والصراحة؟ يستاهل."
summary: "القناة {channel} سوّت فكرة بسيطة بس عبقرية: {gist}"
insight: "وأهم شي: الفيديو ما يعلّمك بالنظرية، يخليك تطبق وأنت تشوف، خطوة خطوة."
opinion: "وهنا النقطة اللي وقفتني: الأسلوب يخلي المعلومة تثبت بمخك من غير ما تحس إنك تذاكر."
detail:  "وفيه لحظة بالنص تعطيك قاعدة عملية تنفعك كل يوم، بس ما أبغى أحرقها عليك."
cta:     "إذا مجالك قريب من الموضوع، أعطه فرصة وقولي وش صار. والرابط بالتعليق المثبت."
```
(`{gist}` = أول ~14 كلمة من التفريغ) — التنفيذ: `vtsys/scriptwriter.py::GULF`.

---

## 3) الخط 🅱 — الوضع الوثائقي (فيديو بلا كلام)
### 3.1 الاستبدال الجوهري: لا ترجمة ⇒ النظام "يشوف"
| العين | الأداة | الخرج |
|---|---|---|
| مونتير | `select='gt(scene,0.30)',showinfo` → `pts_time` + دمج قطع <6ث | قائمة مشاهد |
| مهندس صوت | `volumedetect` لكل مشهد | mean/max dB → تصنيف |
| راوٍ/وكيل بصري | إطار وسط كل مشهد → إنسان أو نموذج Vision | سرد مطابق للحدث |

تصنيف الصوت: `max>-6dB` = صخب عمل (فأس/نشر) | `>-12` = عمل متوسط | غير ذلك = همس طبيعة.
التنفيذ: `vtsys/scenes.py`.

### 3.2 قواعد السرد الوثائقي (غير قابلة للتفاوض)
1. **التنفّس:** تغطية السرد 40–60% من النافذة. المشهد الصاخب ≤35% حتى يُسمع الصوت الأصلي.
2. **lead-in** أول سطر 2.5–3.0ث (عنوان/تنفّس)، وبين الجمل 0.6–0.8ث.
3. يُسمح بصبّ جملة 1–2ث في المشهد التالي (طبيعي)، ويُمنع تراكب جملتين.
4. الجدولة: `start_i = max(scene_start+lead, end_{i-1}+gap)`.
5. الصوت: `ar-SY-LaithNeural` (نبرة الدبلجة الشامية الكلاسيكية) `rate=-8% pitch=-4Hz`.
6. فصحى درامية موجزة؛ الجملة ≤ سطرين؛ لا حرق تفاصيل يكتشفها المشاهد بنفسه.

### 3.3 سلسلة ffmpeg المُختبرة (16:9 1080p25)
```
[d_i]adelay=MS|MS … amix=8:normalize=0,asplit=2[vo1][vo2]
[0:a]volume=0.9[amb]
[amb][vo1]sidechaincompress=threshold=0.03:ratio=6:attack=25:release=400[ambd]   ← Ducking
[ambd][vo2]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[aout]
[0:v]fps=25,scale=2304:1296:flags=bicubic,
     zoompan=z='1+0.10*on/FRAMES':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:s=1920x1080:fps=25,setsar=1
     ,drawbox=y=0:h=110:color=black:t=fill,drawbox=y=970:h=110:color=black:t=fill   ← داكنة سينمائية
     ,ass=doc_captions.ass          ← السبتايتل داخل الشريط السفلي (Noto Naskh)
     ,drawbox=…black@0.55:enable='gte(t,END-4.2)'   ← تعتيم بطاقة الختام
overlays: title.png (fade in/out alpha) + end.png (fade in)
```
التنفيذ: `vtsys/render.py::render_doc`.

### 3.4 بطاقات العنوان/الختام
Pillow PNG شفافة 1920×1080 + `fade=…:alpha=1` + `overlay enable=between(...)`. التنفيذ: `vtsys/captions.py::card`.

---

## 4) الخط 🅲 — المانغا الصوتيّة (Motion Comic)
### 4.1 هيكل القصة (8 نبضات مجرّبة)
وصول ← اكتشاف ← عتبة/قرار ← عمل ← ذروة تقنية ← دفء ← تهديد ليلي مضاد ← خاتمة أمل + "يتبع".
(نفس هيكل رحلة البطل مصغّرة؛ كل نبضة = لوحة واحدة.) — المثال الكامل: `examples/story.json`.

### 4.2 قالب برومبت اللوحة (ثبات الأسلوب والشخصية)
```
Black-and-white Japanese manga panel, seinen style, detailed ink hatching and screentones.
[لقطة سينمائية: زاوية + فعل + ضوء + طقس]
Young bearded man in a dark hooded coat and green beanie.   ← بند ثبات الشخصية (يُكرر حرفياً)
High-contrast monochrome, no text, no speech bubbles, no watermark, no logo.
```
- نوّع الزوايا قصدياً: wide / close / low-angle / split-composition / final-wide.
- المخرج 1536×1024؛ للفيديو: `crop=1536:864:0:80` ثم Ken Burns.
- البرومبتات الثمانية كاملة: `prompts/manga_panels.md`.

### 4.3 قواعد صوت/كاميرا المانغا
- تغطية سرد 60–75% (حكاية مربّية أعلى من وثائقي مراقب).
- سرير خلفي مركّب: رياح + drone (أنظر §5.3).
- لكل لوحة: `zoompan z 1→1.12` باتجاه pan متناوب (0.18 / 0.82) + `noise=alls=4:allf=t` (حبيبات ورق) + `vignette=PI/5`.
- قطع اللوحات concat-demuxer بـ `-c copy` (نفس بارامترات الترميز) — أو الأفضل: **صفر وسائط** عبر `concat filter` داخل رندر واحد (`render_manga_panels`).

---

### 4.4 مرجع الأسلوب (2026-09-14): قناة ملخصات المانهوا
- **المرجع:** https://youtu.be/Q35IXj5qYnY (قناة عالم المانجا — ملخص مانهوا 3 ساعات، ~77K مشاهدة) — البطاقة الكاملة: `examples/manga_reference_Q35IXj5qYnY.md`.
- **الخلاصة:** المرجع = **عامية مصرية سريعة + مانهوا ملونة + حلقات طويلة/تجميع**، بينما خطنا الحالي = فصحى + B&W سينمائي + قصير.
- **القرار المعماري (2026-09-14 — المستخدم):** خطان فرعيان — 🅲-A سينمائي (الحالي) و🅲-B ملخصات (أسلوب المرجع: `ar-EG-ShakirNeural` + قوالب مصرية + حلقات).
- **الحلقة التجريبية 🅲-B:** `package_manga_recap_pilot/` — قصة أصلية (لا panels مقتبسة — §8) + لوحات ملوّنة مولّدة + سرد مصري.
- **قاعدة الترميز:** أي مرجع أسلوب جديد يُوثّق كبطاقة في `examples/` (بيانات + تحليل + عينات + checklist ترميز) قبل أي بناء.

## 5) هندسة الصوت (مشتركة)
### 5.1 الأصوات (edge-tts)
| الاستخدام | الصوت | إعداد |
|---|---|---|
| تعليق خليجي عفوي | `ar-KW-FahedNeural` | rate −4% |
| راوٍ وثائقي/حكاية | `ar-SY-LaithNeural` | rate −8%, pitch −4Hz |
| بدائل ذكورية | SA-Hamed, JO-Taim, AE-Hamdan, EG-Shakir | — |
### 5.2 المزج
- شورت: أصل 12% + VO 100%.
- وثائقي/مانغا: أصل/سرير 90–100% مع **sidechaincompress** (السرير ينخفض تحت الراوي).
- `loudnorm=I=-16:TP=-1.5:LRA=11` دائماً (معيار يوتيوب).
### 5.3 أسرّة صوتية مُخلّقة (حين لا يوجد أصل)
```
رياح شتاء: anoisesrc=color=pink:amplitude=0.55:d=D,lowpass=f=420,tremolo=f=0.1:d=0.6,volume=0.45
Drone:     sine=frequency=55:d=D,volume=0.05  +  sine=frequency=82.41:d=D,volume=0.025
دمج:       amix=inputs=3:normalize=0,pan=stereo|c0=c0|c1=c0
```
(⚠️ `tremolo` حده الأدنى f=0.1؛ و`sine` ليس له خيار amplitude — استخدم `volume` بعده.)
التنفيذ: `vtsys/render.py::beds`.

---

## 6) قواعد النص العربي (درس مؤلم #1)
| الوجهة | القاعدة |
|---|---|
| **Pillow** | إن `PIL.features.check("raqm")==True` → مرّر النص **خاماً** (Pillow يشكّل داخلياً؛ التشكيل اليدوي يكسره). وإلا → `arabic_reshaper + bidi`. استخدم `ar_text()` دائماً. |
| **libass/ASS** | يشكّل بنفسه (HarfBuzz)؛ ملفّاتنا الحالية تمرر نصاً مشكّلاً مسبقاً ونجح — للأنظمة الجديدة فضّل الخام. |
| **الرموز** | تحقّق قبل الاستخدام: إيموجي (🔥👇) و`—` و`…` قد تكون Tofu في Noto Arabic. تحذير `fontselect: failed to find any fallback with glyph 0x…` = دليل Tofu. استبدل بـ `/` أو احذف. |
| **الخطوط** | overlays/Banners: `NotoSansArabic-Bold.ttf` · كابشنز وثائقية وبطاقات حكاية: `NotoNaskhArabic.ttf` (سيريف = هيبة) · لاتيني: `DejaVuSans-Bold`. سطر مختلط عربي+لاتيني: ارسم كل جزء بخطه ورتّبهما يدوياً (العربي يمين). |
| ترتيب RTL يدوي | العربي يمين اللاتيني: `x_lat = x0`, `x_ar = x0 + w_lat + gap`. |

التنفيذ: `vtsys/textutil.py` و `vt/textutil.py`.

---

## 7) دروس البنية التحتية (المؤلمة)
### 7.1 الجلسة الجديدة تفقد الحزم
كل جلسة: `pip install -r requirements.txt` ثم `python3 -m vtsys selftest`
(لا apt-root؛ ffmpeg يأتي من imageio-ffmpeg static 7.0.2 عبر symlink في `bin/`.)

### 7.2 الذاكرة 2GB
- لا وسائط 4K (3840×2160) في zoompan → OOM/قتل 137. استخدم ≤2304×1296 لخرج 1080p، و≤2560×1440 لخرج 720p.
- **لا ترميزين متزامنيين أبداً** (قتل 137 مؤكد). رندر طويل → عملية خلفية + انتظار الخروج.
- preset `fast` كافٍ؛ `-threads 2` عند الضغط.

### 7.3 ffmpeg Static ينهار على روابط https (Segfault فوري)
الحل: التحميل عبر yt-dlp (Python) دائماً، والقص/المعالجة محلياً على ملفات. لا `-i URL` مباشرة.

### 7.4 يوتيوب 403 (حظر مؤقت بعد تحميل كثيف)
خطة: حلقة إعادة محاولة كل دقيقتين (خلفية) ← `--extractor-args "youtube:player_client=android"` (يكشف format 18 مدمج) ← صيغ m3u8 ← وأخيراً: **إعادة بناء من الأصول الناجية** (إطارات/بطاقات/سرد) بدل الاستسلام.

### 7.5 Snapshot التخزين (~128MB) يحذف الملفات الكبيرة بين الجلسات
- المخرجات النهائية ≤ ~30MB وفي `package_*`.
- المصادر والوسائط في **`build/src` على القرص** (مستثنى من Snapshot، 25GB). ⚠️ **ليس `/tmp`:** في هذه البيئة `/tmp`=tmpfs بسعة ~1GB فقط (درس 2026-09-14: امتلأ بوسائط رندر ومات TTS بـ ENOSPC).
- نظّف بعد كل رندر: `seg/`, `base_*.mp4`, `vfull*`, `afull*`, `clip*`, إطارات الفحص.
- تحقق: `du -sh /home/user` يجب < 110MB قبل نهاية الجلسة (`python3 -m vtsys status --clean`).
- إن ضاع فيديو: الأصول الصغيرة (json/ass/png/narr) تنجو ⇒ إعادة البناء ممكنة دائماً.

### 7.6 مصائد ffmpeg المسجلة
| العرض | السبب | الحل |
|---|---|---|
| `Error evaluating expression 'ih/(1+..t..)'` في crop | w/h في crop تُقيّم مرة واحدة (t=NaN) | Ken Burns عبر `zoompan` فقط |
| `Invalid stream specifier / matches no streams` عند استخدام label مرتين | مخرج الفلتر يُستهلك مرة واحدة | `asplit=2[a][b]` |
| `Numerical result out of range` tremolo | f<0.1 مرفوض | f=0.1 |
| `Option not found: amplitude` في sine | الخيار غير موجود | `sine=…,volume=X` |
| Tofu مربع في النص | رمز غائب بالخط | §6 |
| قص `--download-sections` يفشل | يحتاج ffmpeg سليم + قد segfault | تحميل كامل ثم `-ss/-t -c copy` |
| وسائط وسطية عملاقة (30Mbps/seg) | حبيبات `noise` + حبر مانغا كثيف + ultrafast/crf17 | الحبيبات في الرندر النهائي فقط؛ الوسائط الوسيطة crf≥18 preset fast — أو الأفضل: **صفر وسائط** (concat filter داخل رندر واحد) |
| `ENOSPC` في `/tmp` | tmpfs ~1GB | scratch على القرص: `build/` (§7.5) |
| Tofu مكان `/` في بطاقة Naskh | نسخة الخط قد لا تحوي اللاتيني الأساسي | تجنّب أي حرف لاتيني في نصوص Naskh — سطور عربية منفصلة بدل الفواصل |

---

## 8) القواعد القانونية/السلامة
- **التحويل الجوهري:** تعليقك/سردك هو المحتوى الأساسي؛ الاقتباس قصير ومنسوب (بانر "المصدر: …").
- لا إعادة رفع كاملة لمحتوى الغير؛ نافذة الاقتباس ≤ ثوانٍ لكل لقطة.
- حصص النشر §1.4؛ الحسابات الشخصية تُدار يدوياً عبر طابور جاهز.
- المحتوى المولّد (صور/صوت) يُذكر في الوصف عند الطلب/السياسة.

---

## 9) خريطة الملفات والحزم
```
vtsys/
  cli.py        CLI: selftest|scan|decide|short|doc|manga|queue|status
  config.py     config.json: threshold, niche, voices, quota, coverage, storage_budget
  env.py        تثبيت الحزم + ffmpeg symlink + فحص خطوط/raqm (selftest)
  decision.py   محرّك النقاط + flag silent_candidate
  youtube.py    meta/search/subs/download(→build/src)/cut
  scenes.py     كشف مشاهد + بصمة صوت + إطارات
  scriptwriter.py قوالب خليجية/وثائقية + prompts LLM + خطاف OpenRouter
  tts.py        synth + concat_vo + schedule(anchors/gap/lead) + coverage
  captions.py   ass_short / ass_doc / card (PNG شفافة)
  render.py     render_short / render_doc / render_manga_panels (صفر وسائط) + beds + duck_mix
  manga.py      build_base (legacy) — يُفضّل render_manga_panels
  thumb.py      banner_short + thumb_text
  queue.py      طابور بشري: حصص/فواصل gauss/ساعات نشاط/منع تكرار (queue.json)
  storage.py    ميزانية Workspace + clean()
vt/
  pipeline.py        الخط 🅰 كامل (قرار→ترجمة→سكريبت→TTS→قص→رندر)
  documentary.py     الخط 🅱 (مشاهد→صوت→سرد→جدولة→رندر)
  decision_engine.py محرّك النقاط (الأصلي)
  transcript.py      json3 → مقاطع بتوقيتات
  textutil.py        ar_text() (§6)
examples/          story.json + narration.json + comment_variants.txt + queue.example.json
prompts/           manga_panels.md + thumbnails.md
assets/fonts/      NotoSansArabic-Bold + NotoNaskhArabic (عبر download.sh)
memory/            الذاكرة السجلية: STATE (يُقرأ أولاً) + LOG + decisions + sessions + log.py
queue.json         حالة الطابور (متتبَّعة في git — تنجو بين الجلسات)
package_*/         باكجات التسليم النهائية فقط (فيديو ≤30MB + ثامبنيل + نصوص)
```
مواصفات التصدير الموحدة: H.264 High، yuv420p، AAC 48k stereo، `+faststart`، 720p/1080p، −16 LUFS.

---

## 10) Bootstrap نظام كامل في بيئة جديدة (Quick Start)
```bash
pip install -r requirements.txt
bash assets/fonts/download.sh
python3 -m vtsys selftest
# شورت:      python3 -m vtsys short <URL>
# وثائقي:    python3 -m vtsys doc <URL> --window S E --narration examples/narration.json
# مانغا:     python3 -m vtsys manga --story examples/story.json --panels DIR/
# قرار+طابور: python3 -m vtsys decide <URL> --enqueue && python3 -m vtsys queue next
```

---

## 11) خارطة طريق مقترحة
1. **Vision-LLM narration:** إطارات المشاهد → نموذج بصري يكتب السرد تلقائياً (يستبدل الوكيل البشري في 🅱/🅲).
2. **جالب ترندات صامتة:** بحث دوري `ytsearch` عن ASMR/building صاعد → Decision Engine → طابور إنتاج.
3. **طابور نشر بشري-نصف-آلي:** واجهة تعرض الباكج + زر نشر (يوتيوب OAuth).
4. **موسيقى تصويرية مولّدة** بدل/فوق الـdrone (طبقة ثالثة في السرير).
5. **A/B ثامبنيل:** توليد نسختين وقياس CTR عبر YouTube Analytics API.

---

## 12) النظام الموحّد `vtsys` (الإصدار 1.0 — 2026-09-14)
### أوامر سريعة
```bash
python3 -m vtsys selftest
python3 -m vtsys scan --query "..." --limit 6 --niche asmr --enqueue
python3 -m vtsys decide <URL> --enqueue
python3 -m vtsys short  <URL> [--script s.json]
python3 -m vtsys doc    <URL> --window S E --narration n.json [--res 720]
python3 -m vtsys manga  --story story.json --panels DIR/
python3 -m vtsys queue list|next|mark --video-id ID --status published
python3 -m vtsys status [--clean]
```
### دروس معمارية من بناء vtsys
- **concat filter بدل وسائط**: 8 لوحات كمدخلات `-loop 1 -t` + `concat=n=8:v=1:a=0` = جيل ترميز واحد وحجم معقول.
- **إزاحة مدخلات**: اللوحات 0..n-1، السرد n..2n-1، البطاقات 2n, 2n+1 — انزلاق فهرسة واحد = "Error binding filtergraph".
- **selftest أولاً في كل جلسة** يكشف الحزم الناقصة وraqm والخطوط قبل أي رندر.
- مخرجات الاختبارات تروح `build/`؛ الـ`package_*` للمسلّمات فقط وبعد فحص الميزانية.

---

## الملحق أ — الكود الكامل
الكود يعيش في هذا المستودع كمصدر وحيد للحقيقة (لا نسخ مكررة داخل هذا الملف):
- `vt/textutil.py` ← أ.1 · `vt/decision_engine.py` ← أ.2 · `vt/transcript.py` ← أ.3
- `vt/pipeline.py` ← أ.4 · `vt/documentary.py` ← أ.5
- `vtsys/*.py` (18 موديول) ← أ.6

> إصلاحات موثقة عند النقل إلى المستودع (2026-09-14):
> 1. `vt/pipeline.py::fetch_meta`: كان يجلب البيانات مرتين (استدعاء مكرر) — أصبح استدعاءً واحداً مع فحص الخطأ.
> 2. `vtsys/cli.py::cmd_scan`: وسم `🎬 وثائقي؟` كان ميتاً (`.get("")`) — أصبح يقرأ `silent_candidate` فعلياً.
> 3. `vtsys/render.py::render_manga_panels`: إزالة فرع ميت (`if False`) — نفس الناتج.
> 4. `vtsys/render.py::render_doc`: توحيد متغير الدقة `RES` بدل تكرار الشرط.
> 5. `vtsys/youtube.py::download`: التخزين المؤقت الافتراضي `build/src` (على القرص) بدل `/tmp` — التزاماً بدرس §7.5.
> 6. `vt/documentary.py`: إصلاح `SyntaxError` في سطر بناء مدخلات السرد (`["-i", s["file"] for s ...]` غير صالح) — أصبح `[x for s in sched for x in ("-i", s["file"])]`.

---

## الملحق ب — الأصول التشغيلية
تعيش في `examples/`: `story.json` (ب.2) · `narration.json` (ب.3) · `comment_variants.txt` (ب.4) · `queue.example.json` (ب.5) — و`config.json` في الجذر (ب.1).

## الملحق ج — مكتبة البرومبتات الكاملة (مجربة 2026-09-13/14)
تعيش في `prompts/`: `manga_panels.md` (ج.1: اللوحات الثمانية) · `thumbnails.md` (ج.2 ثامبنيل الشورت + ج.3 قاعدة الوثائقي).

## الملحق د — الخطوط والأصول الثنائية
```bash
bash assets/fonts/download.sh
# لاتيني: /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf (موجود غالباً)
```

## الملحق هـ — سجل الاختبارات الحيّة (إثبات عمل)
| الاختبار | النتيجة |
|---|---|
| `selftest` | ffmpeg 7.0.2-static · raqm=true · 3 خطوط OK · python 3.13 |
| `scan` (4 ترندات ASMR) | نقاط 33/10/26/18 → لا إضافة للطابور (صحيح) |
| `decide --enqueue` + `queue next` | planned 16:07 ضمن ساعات النشاط |
| `manga` e2e عبر CLI | 110.1s · تغطية 67% · خرج 32MB · سلامة OK |
| شورت lwAG7bBg4n8 | 60.09s · 1080×1920 · بانر/كابشن سليمين بعد إصلاح raqm |
| وثائقي WCD9b4US224 | 147.4s · تغطية 55% · ducking + loudnorm −16 LUFS |

### 7.7 قيود شبكة هذه البيئة (Arena sandbox — درس 2026-09-14)
- البيئة تسمح بـ TLS لبعض المضيفين فقط: `pypi.org`, `github.com`, `api.github.com`, `codeload.github.com` ✅
- محجوب: `raw.githubusercontent.com`, `cdn.jsdelivr.net`, `fonts.googleapis.com`, `speech.platform.bing.com` (edge-tts), `youtubei` (yt-dlp) ❌
- النتائج العملية:
  - الخطوط تُنزّل عبر **GitHub API** (base64) كبديل تلقائي — التنفيذ في `assets/fonts/download.sh`.
  - `edge-tts` و`yt-dlp` (يوتيوب) **لا يعملان داخل هذه البيئة** — الاختبار الحي للصوت والجلب يحتاج بيئة بشبكة مفتوحة.
  - ما يمكن اختباره هنا بدون شبكة: `selftest`, `decision` (ببيانات وهمية), `scriptwriter`, `captions`, `thumb`, `card`, `queue`, `storage`, وتوليد ASS/PNG.
- `pip install` يحتاج `--break-system-packages` هنا (PEP 668).
- `Pillow` هنا **بدون raqm** (`raqm=false`) — مسار `arabic_reshaper+bidi` الاحتياطي يعمل وتم التحقق منه بصرياً (بانر سليم، RTL صحيح).

*نهاية ملف المعرفة — كل ما يُبنى لاحقاً يُضاف هنا كدرس جديد (§7).*
