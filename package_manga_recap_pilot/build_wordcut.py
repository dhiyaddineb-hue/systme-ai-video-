#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""بناء v4 (من storyboard معتمد): تقطيع على إيقاع الكلمات من sprite sheets (§4.6).
الاستخدام: python3 package_manga_recap_pilot/build_wordcut.py
المداخل: sentences.json (المدد المقاسة) + sheets/sheet1..6.jpg + vo_sent/
المخرج: sief_eldel_ep1_v4.mp4 — قطع كل ~2s + كابشن بوب كلمة-بكلمة.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from vtsys import config, env, captions, render  # noqa: E402
from vtsys.tts import word_times  # noqa: E402
from vtsys.storyboard import split_beats, LEAD as SB_LEAD  # noqa: E402
from vtsys.manga import extract_regions, QUADRANTS  # noqa: E402
from vtsys.scenes import duration  # noqa: E402

BEAT_MIN, GAP_SENT, LEAD = 1.8, 0.4, SB_LEAD  # مطابقة vtsys/storyboard (مصدر وحيد)
BEAT_SHEET = {"hook": 0, "hero": 1, "humiliation": 2, "awakening": 3,
              "power": 4, "cliffhanger": 5}
REGS = ["q1", "q2", "q3", "q4"]

PKG = os.path.dirname(os.path.abspath(__file__))
story = json.load(open(os.path.join(PKG, "story.json"), encoding="utf-8"))
units = json.load(open(os.path.join(PKG, "sentences.json"), encoding="utf-8"))["units"]
cfg = config.load(ROOT)
ff = env.ensure_ffmpeg(ROOT)
fp = {k: (v if os.path.isabs(v) else os.path.join(ROOT, v)) for k, v in cfg["fonts"].items()}

print("🎙️ مدد الجُمل + توزيع الكلمات…")
sents = []
for u in units:
    f = os.path.join(PKG, u["vo"])
    assert os.path.exists(f), f"مقطع ناقص: {u['vo']}"
    d = round(duration(ff, f), 2)
    wt = word_times(u["text"], d)
    sents.append(dict(file=f, dur=d, beat=u["beat"], words=wt))
    print(f"   s{u['id']:02d} = {d}s / {len(wt)} كلمات")

print("✂️ قص الـ sprite sheets…")
stills = {}
for b in range(6):
    p = os.path.join(PKG, "sheets", f"sheet{b + 1}.jpg")
    assert os.path.exists(p), f"شيت ناقص: {p}"
    stills[b] = extract_regions(ff, p, QUADRANTS, os.path.join(ROOT, "build", "wordcut"),
                                f"sh{b + 1}")
print(f"   {6 * 4} stills جاهزة")

print("🎞️ تجميع الـ beats (~2s)…")
raw = split_beats([s["words"] for s in sents])
beats, ri = [], 0  # {sheet, still, dur, sent}
for b in raw:
    sh = BEAT_SHEET[sents[b["sent"]]["beat"]]
    beats.append(dict(sheet=sh, still=stills[sh][REGS[ri % 4]], dur=b["dur"], sent=b["sent"]))
    ri += 1
SB = os.path.join(PKG, "storyboard.json")
if os.path.exists(SB):
    shots = json.load(open(SB, encoding="utf-8"))["shots"]
    assert len(shots) == len(beats), "الـ storyboard لا يطابق الـ beats!"
    for b, s_ in zip(beats, shots):
        st = s_["still"]
        b["still"] = (stills[st["sheet"]][st["region"]] if st["kind"] == "quad"
                       else os.path.join(PKG, st["file"]))
    print("   📋 يُبنى من الـ storyboard المعتمد ✅")
print(f"   {len(beats)} beat بصري")

t = LEAD
v_sched, a_sched, sent_start = [], [], {}
for i, b in enumerate(beats):
    if b["sent"] not in sent_start:
        sent_start[b["sent"]] = round(t, 2)
    v_sched.append(dict(idx=i, scene_dur=b["dur"], start=round(t, 2)))
    t += b["dur"]
win = round(t, 2)
for si, s in enumerate(sents):
    a_sched.append(dict(idx=si, text="", file=s["file"], dur_narr=s["dur"],
                        start=sent_start[si], scene_dur=None))
narr = sum(s["dur"] for s in sents)
print(f"🎬 المدة: {win}s | التغطية: {round(narr / win * 100)}% | beats: {len(beats)}")
json.dump(v_sched, open(os.path.join(PKG, "sched_v4.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("📝 كابشن البوب + بطاقات…")
pop = [dict(start=sent_start[i], words=s["words"]) for i, s in enumerate(sents)]
ass = captions.ass_wordpop(os.path.join(PKG, "manga_v4.ass"), pop, 0.0)
captions.card(os.path.join(PKG, "title.png"),
              [(story["title"], "naskh", 150, 290, (255, 255, 255, 255), 6),
               (story.get("subtitle", ""), "naskh", 64, 500, (230, 214, 160, 255), 3),
               (story.get("part", ""), "naskh", 56, 590, (230, 214, 160, 255), 3)], fp)
captions.card(os.path.join(PKG, "end.png"),
              [(story.get("endcard", "يتبع"), "naskh", 120, 430, (255, 255, 255, 255), 6),
               (story.get("endcard2", ""), "naskh", 50, 600, (230, 214, 160, 255), 3)], fp)

print("🎞️ الرندر النهائي (ترميز واحد)…")
out = os.path.join(PKG, "sief_eldel_ep1_v4.mp4")
render.render_wordcut(ff, [b["still"] for b in beats], v_sched, a_sched,
                      win, ass, os.path.join(PKG, "title.png"),
                      os.path.join(PKG, "end.png"), out)
print("✅", out)
