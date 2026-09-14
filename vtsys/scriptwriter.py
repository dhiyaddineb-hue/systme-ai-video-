# -*- coding: utf-8 -*-
"""المخ (§2.3/§2.4/§3.2): قوالب خليجية + قوالب وثائقية + خطاف LLM."""
import json, os, urllib.request

GULF = [
    ("hook",     "لقيت فيديو جاب {views} مشاهدة، وقعدت له {dur} دقيقة كاملة. والصراحة؟ يستاهل."),
    ("summary",  "القناة {channel} سوّت فكرة بسيطة بس عبقرية: {gist}"),
    ("insight",  "وأهم شي: الفيديو ما يعلّمك بالنظرية، يخليك تطبق وأنت تشوف، خطوة خطوة."),
    ("opinion",  "وهنا النقطة اللي وقفتني: الأسلوب يخلي المعلومة تثبت بمخك من غير ما تحس إنك تذاكر."),
    ("detail",   "وفيه لحظة بالنص تعطيك قاعدة عملية تنفعك كل يوم، بس ما أبغى أحرقها عليك."),
    ("cta",      "إذا مجالك قريب من الموضوع، أعطه فرصة وقولي وش صار. والرابط بالتعليق المثبت."),
]

DOC = {
    "open":  "هنا، حيث لا تصل الضوضاء… يبدأ الإنسان عمله القديم.",
    "work":  "يداه تعرفان الطريق: لا عجلة، لا تردد… فقط إيقاع الغابة.",
    "quiet": "وفي الصمت، تفصيلٌ صغير يصنع الفرق بين البقاء والضياع.",
    "close": "وهكذا، يوماً بعد يوم… تولد من العدم مأوىً دافئة.",
}

def gulf(meta, segs):
    words = " ".join(s["text"] for s in segs[:40]).split()
    fmt = dict(views=f"{meta['view_count']:,}".replace(",", "،"),
               dur=round(meta["duration"] / 60),
               channel=meta["channel"].strip(), gist=" ".join(words[:14]) + "…")
    return [{"id": i + 1, "type": t, "text": txt.format(**fmt)}
            for i, (t, txt) in enumerate(GULF)]

def doc_fallback(scene_classes):
    """scene_classes: قائمة cls لكل مشهد → سرد تقريبي بدون وكيل بصري."""
    seq = []
    for i, c in enumerate(scene_classes):
        if i == 0:
            seq.append(DOC["open"])
        elif i == len(scene_classes) - 1:
            seq.append(DOC["close"])
        else:
            seq.append(DOC["work"] if c == "work_loud" else DOC["quiet"])
    return [{"scene": i, "text": t} for i, t in enumerate(seq)]

def llm(prompt, model=None):
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    body = json.dumps({"model": model or os.environ.get("LLM_MODEL", "openai/gpt-4o-mini"),
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", body,
                                 {"Authorization": f"Bearer {key}",
                                  "Content-Type": "application/json"})
    try:
        res = json.load(urllib.request.urlopen(req, timeout=90))
        return res["choices"][0]["message"]["content"]
    except Exception as e:
        print("⚠️ LLM غير متاح:", e)
        return None

GULF_SCRIPT_PROMPT = (
    "اكتب تعليق فيديو بأسلوب شاب خليجي عفوي (مو رسمي).\nالعنوان: {title}\nالقناة: {channel}\n"
    "مقتطف تفريغ: {sample}\nأرجع JSON فقط: قائمة 6 مقاطع بأنواع "
    "hook,summary,insight,opinion,detail,cta — جملة-جملتان لكل مقطع.")

DOC_SCRIPT_PROMPT = (
    "اكتب سرداً وثائقياً بالفصحى الدرامية لمشاهد فيديو صامت (بناء/طبيعة).\n"
    "وصف المشاهد (توقيت+بصمة صوت): {scenes}\n"
    "أرجع JSON: قائمة {{scene, text}} — جملة-جملتان لكل مشهد، تغطية ≤60%.")

# ── 🅲-B ملخصات مصرية (أسلوب المرجع Q35IXj5qYnY) ──────────────
RECAP_BEATS = ("hook", "hero", "humiliation", "awakening", "power", "cliffhanger")

EGYPTIAN_RECAP_TEMPLATES = [
    ("hook",        "النهارده… في {place}… {hero} {hook_event}. إزاي؟ اقعد واسمع الحكاية من الأول."),
    ("hero",        "اسمه {hero}… {age} سنة… من {origin}. ودخل {place} إزاي؟ بالعافية… {entry}."),
    ("humiliation", "يوم الاختبار… {villain}… {shame_event} قدام الكل. والكل ضحك… إلا واحد."),
    ("awakening",   "وفي نفس الليلة… {hero} هرب لـ{secret_place}… وهناك… {artifact}… نادى عليه باسمه."),
    ("power",       "أول ما لمس {artifact}… {power_event}. ضربة واحدة… و{power_proof}."),
    ("cliffhanger", "وتاني يوم الصبح… {villain} طلب {duel}… قدام الكل. و{hero}؟ ما ردش… ابتسم بس. يتبع."),
]

RECAP_SCRIPT_PROMPT = (
    "اكتب ملخص حلقة مانهوا بالعامية المصرية السريعة (أسلوب قنوات الملخصات).\n"
    "البطل: {hero} | الخصم: {villain} | العالم: {world}\n"
    "القواعد: زمن مضارع حي + جمل قصيرة متلاحقة + قفشة ساخرة على الخصم + "
    "جسر فلاشباك واحد + كليفهانغر ختامي + كلمة 'يتبع'.\n"
    "أرجع JSON فقط: قائمة 6 مقاطع بأنواع "
    "hook,hero,humiliation,awakening,power,cliffhanger — 15-30 كلمة للمقطع.")

def recap_title(title, part_from, part_to, hook_words):
    """صيغة عناوين الملخصات: ملخص كامل 1~8 | … 🔥"""
    return f"ملخص كامل {part_from}~{part_to} | {title} {' '.join(hook_words)}"

# ── §4.5 قاعدة الجملة-مشهد ──────────────────────────────────
import re as _re

def split_sentences(text):
    """تقسيم السرد إلى جُمل: كل جملة = مشهد خاص.
    الفواصل: [.؟?!] + سطر جديد. (… تبقى داخل الجملة كوقفة نطق طبيعية)."""
    parts = _re.split(r"(?<=[.!؟?!])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]

def expand_to_sentences(lines):
    """lines: [{text, ...}] → وحدات جُمل تحمل beat/panel الأصل."""
    units = []
    for l in lines:
        for s in split_sentences(l["text"]):
            u = dict(l)
            u["text"] = s
            units.append(u)
    return units
