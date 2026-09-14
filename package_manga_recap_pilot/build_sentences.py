#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""بناء v2 من الحلقة التجريبية بقاعدة الجملة-مشهد (§4.5).
الاستخدام: python3 package_manga_recap_pilot/build_sentences.py
المدخل: sentences.json (15 وحدة) + panels/ + vo_sent/ — المدد تُقاس فعلياً.
المخرج: sief_eldel_ep1_v2.mp4 (v1 الأصلية تبقى كما هي).
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from vtsys import config, env, captions, render, tts  # noqa: E402
from vtsys.scenes import duration  # noqa: E402

PKG = os.path.dirname(os.path.abspath(__file__))
story = json.load(open(os.path.join(PKG, "story.json"), encoding="utf-8"))
units = json.load(open(os.path.join(PKG, "sentences.json"), encoding="utf-8"))["units"]
cfg = config.load(ROOT)
ff = env.ensure_ffmpeg(ROOT)
fp = {k: (v if os.path.isabs(v) else os.path.join(ROOT, v)) for k, v in cfg["fonts"].items()}

print(f"🎙️ قياس مدد الجُمل ({len(units)} مشهد)…")
lines, panels = [], []
for u in units:
    f = os.path.join(PKG, u["vo"])
    assert os.path.exists(f), f"مقطع ناقص: {u['vo']}"
    d = round(duration(ff, f), 2)
    print(f"   s{u['id']:02d} = {d}s  [{u['beat']}]")
    lines.append(dict(text=u["text"], file=f, dur=d, base=u.get("base", 6)))
    panels.append(os.path.join(PKG, u["panel"]))

sched, t = [], 0.0
for i, l in enumerate(lines):
    sd = round(max(l["base"], l["dur"] + 2.0), 1)
    st = round(t + (2.0 if i == 0 else 0.4), 2)
    sched.append(dict(idx=i, text=l["text"], file=l["file"],
                      dur_narr=l["dur"], start=st, scene_dur=sd))
    t = st + sd
win = round(t, 2)
print(f"🎬 المدة الكلية: {win}s | التغطية: {tts.coverage(sched, win)}%")
json.dump(sched, open(os.path.join(PKG, "sched_v2.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("📝 سبتايتل وبطاقات…")
ass = captions.ass_doc(os.path.join(PKG, "manga_v2.ass"), sched, 0.0)
captions.card(os.path.join(PKG, "title.png"),
              [(story["title"], "naskh", 150, 290, (255, 255, 255, 255), 6),
               (story.get("subtitle", ""), "naskh", 64, 500, (230, 214, 160, 255), 3),
               (story.get("part", ""), "naskh", 56, 590, (230, 214, 160, 255), 3)], fp)
captions.card(os.path.join(PKG, "end.png"),
              [(story.get("endcard", "يتبع"), "naskh", 120, 430, (255, 255, 255, 255), 6),
               (story.get("endcard2", ""), "naskh", 50, 600, (230, 214, 160, 255), 3)], fp)

print("🎞️ الرندر النهائي (ترميز واحد)…")
out = os.path.join(PKG, "sief_eldel_ep1_v2.mp4")
render.render_manga_panels(ff, panels, sched, win, ass,
                           os.path.join(PKG, "title.png"), os.path.join(PKG, "end.png"), out)
print("✅", out)
