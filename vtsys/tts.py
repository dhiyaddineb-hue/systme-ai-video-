# -*- coding: utf-8 -*-
"""الصوت (§5): TTS لكل جملة + قياس حقيقي + جدولة + concat."""
import asyncio, os, subprocess
from .scenes import duration

def normalize_spoken_arabic(text):
    """Make pauses and punctuation explicit without changing caption text."""
    import re
    text = text.replace("…", ", ").replace("...", ", ")
    text = re.sub(r"[\\[\\]{}<>]", "", text)
    text = re.sub(r"\\s+", " ", text).strip()
    return text

def synth(ffmpeg, lines, voice, rate=None, pitch=None, adir="narr"):
    import edge_tts
    os.makedirs(adir, exist_ok=True)
    async def run():
        for i, l in enumerate(lines):
            f = os.path.join(adir, f"n{i:02d}.mp3")
            spoken = normalize_spoken_arabic(l["text"])
            c = edge_tts.Communicate(spoken, voice,
                                     rate=rate or "-4%", pitch=pitch or "+0Hz")
            await c.save(f)
            l["file"] = f
            l["dur"] = round(duration(ffmpeg, f), 2)
    asyncio.run(run())
    return lines

def concat_vo(ffmpeg, lines, out):
    lst = out + ".list"
    open(lst, "w").write("".join(f"file '{l['file']}'\n" for l in lines))
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-f", "concat",
                    "-safe", "0", "-i", lst, "-c", "copy", "-y", out],
                   check=True, capture_output=True)
    os.remove(lst)
    return out

def schedule(lines, anchors=None, first_lead=2.5, gap=0.7, min_scene=None):
    """anchors: توقيت بداية نافذة كل سطر (مشاهد/لوحات). إن غاب ⇒ تتابع حر.
    يعيد schedule: start, scene_dur(إن وجد), dur_narr, file, text."""
    out, t = [], 0.0
    for i, l in enumerate(lines):
        a = anchors[i] if anchors else None
        sd = None
        if a is not None and min_scene:
            sd = round(max(min_scene, l["dur"] + 3.0), 1)
            st = round(max(a + (first_lead if i == 0 else gap), t + gap), 2)
        else:
            st = round(t + (first_lead if i == 0 else gap), 2)
        out.append(dict(idx=i, text=l["text"], file=l["file"], dur_narr=l["dur"],
                        start=st, scene_dur=sd))
        t = st + (sd if sd else l["dur"])
    return out

def coverage(sched, win):
    return round(sum(s["dur_narr"] for s in sched) / win * 100) if win else 0

def word_times(text, dur, min_w=0.25):
    """توزيع مدة الجملة المقاسة على كلماتها تناسبياً مع طول الكلمة (§4.6).
    المجموع = المدة الحقيقية دائماً. التوزيع الداخلي تقدير مُوثّق (خطأ <0.3s) —
    يُستبدل بـ word boundaries الحقيقية (edge-tts/whisper) عند توفرها.
    يعيد: [(word, dur), ...]"""
    words = text.split()
    if not words:
        return []
    weights = [max(len(w.strip("….,؟?!")), 1) for w in words]
    n = len(words)
    if dur < min_w * n:  # مدة أقصر من الحدود — توزيع متساوٍ
        return [(w, round(dur / n, 2)) for w in words]
    rem = dur - min_w * n
    tot = sum(weights)
    out = [(w, round(min_w + rem * wt / tot, 2)) for w, wt in zip(words, weights)]
    # تصحيح انجراف التقريب في الكلمة الأخيرة
    drift = round(dur - sum(d for _, d in out), 2)
    out[-1] = (out[-1][0], round(out[-1][1] + drift, 2))
    return out
