#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""بناء v5: الإصدار السينمائي من storyboard معتمد (§4.8).
الاستخدام: python3 package_manga_recap_pilot/build_cine.py
يرفض العمل إن لم يكن البورد معتمداً (قانون البوابة §4.7).
المخرج: sief_eldel_ep1_v5.mp4 — حركة نوعية + فلاش + SFX + كاريوكي ذهبي + تدرج مزاجي.
"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from vtsys import config, env, captions, render  # noqa: E402
from vtsys.tts import word_times  # noqa: E402
from vtsys.manga import extract_regions, QUADRANTS  # noqa: E402
from vtsys.scenes import duration  # noqa: E402

PKG = os.path.dirname(os.path.abspath(__file__))
story = json.load(open(os.path.join(PKG, "story.json"), encoding="utf-8"))
units = json.load(open(os.path.join(PKG, "sentences.json"), encoding="utf-8"))["units"]
board = json.load(open(os.path.join(PKG, "storyboard.json"), encoding="utf-8"))
assert board["status"].startswith("معتمد"), "⛔ البورد غير معتمد — ممنوع الإنتاج (§4.7)"
assert board["stats"]["v4_violations"] == 0, "⛔ البورد فيه مخالفات — ممنوع الإنتاج"
shots = board["shots"]
print(f"📋 بورد معتمد: {len(shots)} لقطة ✅")
cfg = config.load(ROOT)
ff = env.ensure_ffmpeg(ROOT)
fp = {k: (v if os.path.isabs(v) else os.path.join(ROOT, v)) for k, v in cfg["fonts"].items()}

print("🎙️ مدد الجُمل + كلماتها…")
sents = []
for u in units:
    f = os.path.join(PKG, u["vo"])
    d = round(duration(ff, f), 2)
    sents.append(dict(file=f, dur=d, words=word_times(u["text"], d)))

print("✂️ stills البورد…")
stills = {}
for b in range(6):
    stills[b] = extract_regions(ff, os.path.join(PKG, "sheets", f"sheet{b + 1}.jpg"),
                                QUADRANTS, os.path.join(ROOT, "build", "wordcut"), f"sh{b + 1}")

def still_of(st):
    return stills[st["sheet"]][st["region"]] if st["kind"] == "quad" else os.path.join(PKG, st["file"])

v_sched = [dict(idx=i, scene_dur=s["dur"], start=s["time"],
                shot={"type": s["type"], "mood": s["mood"]}) for i, s in enumerate(shots)]
win = round(shots[-1]["time"] + shots[-1]["dur"], 2)
sent_start = {}
for s in shots:
    sent_start.setdefault(s["sent"] - 1, s["time"])
a_sched = [dict(idx=i, text="", file=s["file"], dur_narr=s["dur"],
                start=sent_start[i], scene_dur=None) for i, s in enumerate(sents)]
print(f"🎬 المدة: {win}s")

print("🔊 توليد SFX (whoosh/impact/riser)…")
sfxd = os.path.join(ROOT, "build", "sfx")
os.makedirs(sfxd, exist_ok=True)
WAV = {}
specs = {
    "whoosh": (["-f", "lavfi", "-i", "anoisesrc=color=pink:d=0.4"],
               "highpass=f=400,lowpass=f=5000,afade=t=in:st=0:d=0.28,afade=t=out:st=0.28:d=0.12,volume=0.5"),
    "riser": (["-f", "lavfi", "-i", "anoisesrc=color=pink:d=1.2"],
              "highpass=f=900,afade=t=in:st=0:d=1.2,volume=0.35"),
}
for name, (inp, af) in specs.items():
    o = os.path.join(sfxd, f"{name}.wav")
    if not os.path.exists(o):
        subprocess.run([ff, "-hide_banner", "-loglevel", "error", *inp, "-af", af,
                        "-ar", "48000", "-ac", "2", "-y", o], check=True, capture_output=True)
    WAV[name] = o
o = os.path.join(sfxd, "impact.wav")
if not os.path.exists(o):
    subprocess.run([ff, "-hide_banner", "-loglevel", "error",
                    "-f", "lavfi", "-i", "sine=frequency=55:duration=0.7",
                    "-f", "lavfi", "-i", "anoisesrc=color=brown:duration=0.12",
                    "-filter_complex", "[0:a]volume=0.7,afade=t=out:st=0.3:d=0.4[th];"
                                       "[1:a]lowpass=f=800,volume=0.6[cr];"
                                       "[th][cr]amix=inputs=2:normalize=0",
                    "-ar", "48000", "-ac", "2", "-y", o], check=True, capture_output=True)
WAV["impact"] = o

key_starts = [s["time"] for s in shots if s["type"] == "key_action"]
power_start = next(s["time"] for s in shots if units[s["sent"] - 1]["beat"] == "power")
sfx = dict(whoosh=[s["time"] for s in shots],
           impact=[round(t + 0.05, 2) for t in key_starts],
           riser=[round(power_start - 1.2, 2)],
           flash=[round(t + 0.03, 2) for t in key_starts],
           whoosh_file=WAV["whoosh"], impact_file=WAV["impact"], riser_file=WAV["riser"])
print(f"   whoosh×{len(sfx['whoosh'])} impact×{len(sfx['impact'])} riser×1 flash×{len(sfx['flash'])}")

print("📝 كاريوكي ذهبي + بطاقات…")
pop = [dict(start=sent_start[i], words=s["words"]) for i, s in enumerate(sents)]
ass = captions.ass_kinetic(os.path.join(PKG, "manga_v5.ass"), pop, 0.0)
captions.card(os.path.join(PKG, "title.png"),
              [(story["title"], "naskh", 150, 290, (255, 255, 255, 255), 6),
               (story.get("subtitle", ""), "naskh", 64, 500, (230, 214, 160, 255), 3),
               (story.get("part", ""), "naskh", 56, 590, (230, 214, 160, 255), 3)], fp)
captions.card(os.path.join(PKG, "end.png"),
              [(story.get("endcard", "يتبع"), "naskh", 120, 430, (255, 255, 255, 255), 6),
               (story.get("endcard2", ""), "naskh", 50, 600, (230, 214, 160, 255), 3)], fp)

print("🎞️ الرندر السينمائي (ترميز واحد)…")
out = os.path.join(PKG, "sief_eldel_ep1_v5.mp4")
render.render_dynamic(ff, [still_of(s["still"]) for s in shots], v_sched, a_sched,
                      sfx, win, ass, os.path.join(PKG, "title.png"),
                      os.path.join(PKG, "end.png"), out)
print("✅", out)
