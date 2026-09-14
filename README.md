# 🎬 نظام AI Video — تعليق سريع / وثائقي / مانغا

> ⛔ **قانون مقدس: ممنوع منعاً باتاً عمل `merge` لهذا الفرع** (`arena/01a09f70-systme-ai-video`) — راجع `LAWS.md`.
> 🧠 هذا المستودع هو **الجسد والعقل**: المعرفة في `SYSTEM_KNOWLEDGE.md`، والتنفيذ في `vtsys/` + `vt/`.

نظام يحوّل أي فيديو ترند (أو قصة نصية) إلى **باكج نشر كامل** عبر ثلاثة خطوط إنتاج.
**المبدأ الحاكم:** *الصوت يقود التايم-لاين* — مدة كل جملة صوتية مقاسة فعلياً = مدة لقطتها.

| الخط | المدخل | المخرج | الأمر |
|---|---|---|---|
| 🅰 شورت تعليق | فيديو يوتيوب مترجم | 9:16 فويس-أوفر خليجي + ثامبنيل + تعليقات | `python3 -m vtsys short <URL>` |
| 🅱 وثائقي صامت | فيديو بلا كلام | 16:9 حلقة مروية بفصحى درامية | `python3 -m vtsys doc <URL> --window S E --narration n.json` |
| 🅲 مانغا صوتية | قصة نصية + لوحات | Motion comic من لوحات مولّدة | `python3 -m vtsys manga --story story.json --panels DIR/` |

## 🚀 تشغيل سريع

```bash
pip install -r requirements.txt
bash assets/fonts/download.sh
python3 -m vtsys selftest        # فحص البيئة أولاً في كل جلسة
python3 -m vtsys decide <URL> --enqueue
python3 -m vtsys queue next
python3 -m vtsys status
```

## 📁 الخريطة

```
SYSTEM_KNOWLEDGE.md   العقل — كل الفلسفة والمعادلات والدروس (مصدر الحقيقة)
LAWS.md                القوانين غير القابلة للمخالفة (منع الدمج…)
memory/                الذاكرة السجلية — اقرأ STATE.md أول كل جلسة
vtsys/                 النظام الموحّد (CLI: selftest|scan|decide|short|doc|manga|queue|status)
vt/                    الوحدات الأصلية (pipeline.py + documentary.py)
examples/              story.json + narration.json + comment_variants.txt + queue.example.json
prompts/               مكتبة البرومبتات المجرّبة (مانغا/ثامبنيل)
assets/fonts/          خطوط Noto العربية (عبر download.sh)
config.json            الإعدادات (العتبة، النيش، الأصوات، الحصص…)
```

## ⚠️ قواعد البيئة (ملخص §7)

- التحميل عبر `yt-dlp` دائماً — لا `-i URL` في ffmpeg (ينهار).
- المصادر الثقيلة في `build/src` على القرص — **ليس `/tmp`** (tmpfs ~1GB).
- لا ترميزين متزامنين أبداً (OOM).
- المخرجات النهائية ≤ ~30MB، و`du -sh` الكلي < 110MB قبل نهاية الجلسة.
