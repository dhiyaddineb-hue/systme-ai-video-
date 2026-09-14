#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""بناء الحلقة التجريبية 🅲-B «سيف الظل / الحلقة الأولى» من لوحات + سرد جاهزين.
الاستخدام: python3 package_manga_recap_pilot/build.py
(يعيد البناء كاملاً من story.json + panels/ + vo/ — المدد تُقاس فعلياً، لا تخمين.)
"""
import json, os, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from vtsys import config, env, captions, render, tts, thumb  # noqa: E402
from vtsys.scenes import duration  # noqa: E402

PKG = os.path.dirname(os.path.abspath(__file__))
story = json.load(open(os.path.join(PKG, "story.json"), encoding="utf-8"))
cfg = config.load(ROOT)
ff = env.ensure_ffmpeg(ROOT)
fp = {k: (v if os.path.isabs(v) else os.path.join(ROOT, v)) for k, v in cfg["fonts"].items()}

panels = sorted(glob.glob(os.path.join(PKG, "panels", "*.jpg")) +
                glob.glob(os.path.join(PKG, "panels", "*.png")))
assert len(panels) >= len(story["lines"]), "لوحات أقل من النبضات!"

print("🎙️ قياس مدد السرد الفعلية…")
lines = []
for i, l in enumerate(story["lines"]):
    f = os.path.join(PKG, "vo", f"n{i}.mp3")
    d = round(duration(ff, f), 2)
    lines.append(dict(text=l["text"], file=f, dur=d, panel=l["panel"]))
    print(f"   n{i}.mp3 = {d}s")

sched, t = [], 0.0
for i, (l, bd) in enumerate(zip(lines, story.get("base_durs", [12] * len(lines)))):
    sd = round(max(bd, l["dur"] + 3.0), 1)
    st = round(t + (2.5 if i == 0 else 0.6), 2)
    sched.append(dict(idx=i, panel=l["panel"], text=l["text"], file=l["file"],
                      dur_narr=l["dur"], start=st, scene_dur=sd))
    t = st + sd
win = round(t, 2)
print(f"🎬 المدة الكلية: {win}s | التغطية: {tts.coverage(sched, win)}%")
json.dump(sched, open(os.path.join(PKG, "sched.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("📝 سبتايتل وبطاقات…")
ass = captions.ass_doc(os.path.join(PKG, "manga.ass"), sched, 0.0)
captions.card(os.path.join(PKG, "title.png"),
              [(story["title"], "naskh", 150, 300, (255, 255, 255, 255), 6),
               (story.get("subtitle", ""), "naskh", 56, 500, (230, 214, 160, 255), 3)], fp)
captions.card(os.path.join(PKG, "end.png"),
              [(story.get("endcard", "يتبع"), "naskh", 120, 430, (255, 255, 255, 255), 6),
               (story.get("endcard2", ""), "naskh", 50, 600, (230, 214, 160, 255), 3)], fp)

print("🎞️ الرندر النهائي (ترميز واحد)…")
out = os.path.join(PKG, "sief_eldel_ep1.mp4")
render.render_manga_panels(ff, panels, sched, win, ass,
                           os.path.join(PKG, "title.png"), os.path.join(PKG, "end.png"), out)

print("🖼️ الثامبنيل…")
thumb.thumb_text(panels[0], os.path.join(PKG, "thumb.jpg"),
                 [(story["title"], "naskh", 120, 40, (255, 255, 255)),
                  (story.get("subtitle", ""), "naskh", 60, 200, (255, 201, 60))],
                 fp, chip=story.get("part", ""))
print("✅", out)
