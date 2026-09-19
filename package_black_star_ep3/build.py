#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generic sheet-6 builder (§4.11). Copied into each story package as build.py.
Reads story.json + sentences.json + identity.json from its own folder.
Pipeline: VO schedule -> extract sixths -> no-repeat audit -> board files ->
SFX -> karaoke -> render_dynamic. Any audit failure refuses to render.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from vtsys import config, env, captions, render  # noqa: E402
from vtsys.tts import word_times  # noqa: E402
from vtsys.scenes import duration  # noqa: E402
from vtsys.sheets import extract_sixths, load_individual_panels, audit_norepeat, extract_film_subs, audit_shots  # noqa: E402

FILM = "--film" in sys.argv

try:
    from vtsys.dynamics import MOTION, MOOD_GRADE  # noqa: E402
except Exception:
    MOTION, MOOD_GRADE = {}, {}

BEAT_STYLE = {
    "hook": ("establishing", "تشويق"), "question": ("reaction", "توتر"),
    "hero": ("establishing", "دفء"), "turn": ("detail", "تشويق"),
    "shock": ("key_action", "رهبة"), "power": ("key_action", "انفجار"),
    "threat": ("detail", "رهبة"), "cliff": ("reaction", "انكسار"),
}

# §4.12 FILM MODE — فريم بفريم كالفيلم: كل معنى (مقطع بين …) = لقطة مستقلة
# بقصّتها وحركتها. الأولى wide تأسيسية، الأخيرة punch ذروة، الوسط يتناوب.
HOT_BEATS = ("shock", "power", "threat", "cliff")
MID_TYPES = ("detail", "reaction")
MID_FRAMES = ("left", "right", "top", "low")
MAX_SHOT = 2.2  # إيقاع سينمائي: لا لقطة ثابتة أطول من نحو ثانيتين


def split_meanings(text):
    parts = [p.strip() for p in text.replace("...", "…").split("…") if p.strip()]
    return parts or [text]


def plan_sentence_film(text, words, beat):
    """words: [(word,dur)] من word_times. يعيد [(seg_text, dur, type, frame)]."""
    segs = split_meanings(text)
    out, wi = [], 0
    for seg in segs:
        nw = len(seg.split())
        wd = words[wi:wi + nw]
        wi += nw
        out.append([seg, round(sum(x[1] for x in wd), 2)])
    if wi < len(words):  # كلمات شاردة (ترقيم) → تُلحق بآخر مقطع
        out[-1][1] = round(out[-1][1] + sum(x[1] for x in words[wi:]), 2)
    final = []
    for seg, d in out:
        # لغة الفيلم: حتى المعنى القصير يأخذ انتقالاً داخلياً إذا سمح الصوت.
        # لا نكرر صورة واحدة؛ كل انتقال يستخدم crop مختلفاً من نفس البانل.
        ws = seg.split()
        pieces = max(1, int((d + MAX_SHOT - 0.01) // MAX_SHOT))
        if pieces == 1 and len(ws) >= 4 and d >= 1.35:
            pieces = 2
        pieces = min(pieces, 6)
        if pieces == 1 or len(ws) < pieces:
            final.append((seg, d))
        else:
            base = len(ws) // pieces
            rem = len(ws) % pieces
            at = 0
            for j in range(pieces):
                take = base + (1 if j < rem else 0)
                part = " ".join(ws[at:at + take])
                dd = round(d * take / len(ws), 2)
                final.append((part, dd))
                at += take
    n = len(final)
    res = []
    for k, (seg, d) in enumerate(final):
        if n == 1:
            typ = BEAT_STYLE.get(beat, ("establishing", "تشويق"))[0]
            frm = "punch"
        elif k == 0:
            typ, frm = "establishing", "wide"
        elif k == n - 1:
            typ = "key_action" if beat in HOT_BEATS else "reaction"
            frm = "punch"
        else:
            typ = MID_TYPES[(k - 1) % len(MID_TYPES)]
            frm = MID_FRAMES[(k - 1) % len(MID_FRAMES)]
        if MOTION and typ not in MOTION:
            typ = sorted(MOTION)[0]
        res.append((seg, d, typ, frm))
    return res

PKG = os.path.dirname(os.path.abspath(__file__))
story = json.load(open(os.path.join(PKG, "story.json"), encoding="utf-8"))
S = json.load(open(os.path.join(PKG, "sentences.json"), encoding="utf-8"))
units, gap = S["units"], S.get("gap", 0.4)
assert units, "sentences.json has no units"
cfg = config.load(ROOT)
ff = env.ensure_ffmpeg(ROOT)
fp = {k: (v if os.path.isabs(v) else os.path.join(ROOT, v)) for k, v in cfg["fonts"].items()}

print("VO schedule ...")
sents, t = [], 0.0
for u in units:
    f = os.path.join(PKG, u["vo"])
    assert os.path.exists(f), "missing VO: " + f
    d = round(duration(ff, f), 2)
    words = word_times(u["text"], d)
    nbeats = max(2, round(len(u["text"].split()) / 4))
    sents.append(dict(start=round(t, 2), dur=d, words=words, nbeats=nbeats, file=f))
    t = round(t + d + gap, 2)
win = round(t - gap, 2)

print("extract sixths + no-repeat audit ...")
panels, mapping = {}, {}
for i, u in enumerate(units):
    sh = u["sheet"]
    if sh not in panels:
        individual = load_individual_panels(os.path.join(PKG, "panels"), sh)
        panels[sh] = individual or extract_sixths(ff, os.path.join(PKG, "sheets", sh + ".jpg"),
                                                  os.path.join(PKG, "regions"), sh)
    mapping[u["id"]] = (sh, u["region"])
audit_norepeat(mapping)
assert len(mapping) == len(units), "RULE: every sentence must own exactly one scene"
print("no-repeat audit: PASS (%d unique panels)" % len(mapping))

subs = {}
if FILM:
    print("film subs (§4.12: 6 قصّات سينمائية لكل بانل) ...")
    fdir = os.path.join(PKG, "filmshots")
    for sh, paths in panels.items():
        for rg, p in enumerate(paths):
            subs[(sh, rg)] = extract_film_subs(ff, p, fdir, "%s_r%d" % (sh, rg))
    print("film subs: %d panels x6" % len(subs))

shots = []
for i, u in enumerate(units):
    st = BEAT_STYLE.get(u.get("beat", "hero"), ("establishing", "تشويق"))
    mood = st[1] if (not MOOD_GRADE or st[1] in MOOD_GRADE) else sorted(MOOD_GRADE)[0]
    if FILM:
        plan = plan_sentence_film(u["text"], sents[i]["words"], u.get("beat", "hero"))
        t0, acc = sents[i]["start"], 0.0
        for k, (seg, d, typ, frm) in enumerate(plan):
            dd = d if k < len(plan) - 1 else round(sents[i]["dur"] - acc, 2)
            sh, rg = mapping[u["id"]]
            shots.append(dict(sent=u["id"], seg=seg, sub=frm,
                               time=round(t0 + acc, 2), dur=dd,
                               type=typ, mood=mood, still=(sh, rg, frm)))
            acc = round(acc + dd, 2)
    else:
        typ = st[0] if (not MOTION or st[0] in MOTION) else sorted(MOTION)[0]
        bd = round(sents[i]["dur"] / sents[i]["nbeats"], 2)
        for b in range(sents[i]["nbeats"]):
            shots.append(dict(sent=u["id"], time=round(sents[i]["start"] + b * bd, 2),
                               dur=bd if b < sents[i]["nbeats"] - 1 else
                               round(sents[i]["dur"] - bd * b, 2),
                               type=typ, mood=mood, still=mapping[u["id"]]))

board = {"story": story["slug"], "status": "auto-approved (no-repeat audit PASS)",
         "shots": shots}
json.dump(board, open(os.path.join(PKG, "storyboard.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
with open(os.path.join(PKG, "storyboard.md"), "w", encoding="utf-8") as f:
    f.write("# بورد %s — %d جملة / %d نبضة / %d بانل فريد\n\n" % (
        story["title"], len(units), len(shots), len(mapping)))
    f.write("| # | الجملة | البانل | البداية | النوع |\n|---|---|---|---|---|\n")
    for i, u in enumerate(units):
        f.write("| %d | %s | %s#%d | %.2fs | %s |\n" % (
            u["id"], u["text"][:42], u["sheet"], u["region"],
            sents[i]["start"], shots[[s["sent"] for s in shots].index(u["id"])]["type"]))
print("board: %d shots" % len(shots))

if FILM:
    stills = [subs[(sh, rg)][frm] for (sh, rg, frm) in [s["still"] for s in shots]]
    audit_shots(stills)
    print("shot audit: PASS (%d unique film shots)" % len(stills))
else:
    stills = [panels[sh][rg] for (sh, rg) in [s["still"] for s in shots]]
v_sched = [dict(idx=i, scene_dur=s["dur"], start=s["time"],
                shot={"type": s["type"], "mood": s["mood"]}) for i, s in enumerate(shots)]
a_sched = [dict(idx=i, text="", file=s["file"], dur_narr=s["dur"],
                start=s["start"], scene_dur=None) for i, s in enumerate(sents)]

print("SFX ...")
sfxd = os.path.join(ROOT, "build", "sfx")
os.makedirs(sfxd, exist_ok=True)
WAV = {}
specs = {
    "whoosh": (["-f", "lavfi", "-i", "anoisesrc=color=pink:d=0.4"],
               "highpass=f=400,lowpass=f=5000,afade=t=in:st=0:d=0.28,"
               "afade=t=out:st=0.28:d=0.12,volume=0.5"),
    "riser": (["-f", "lavfi", "-i", "anoisesrc=color=pink:d=1.2"],
              "highpass=f=900,afade=t=in:st=0:d=1.2,volume=0.35"),
}
for name, (inp, af) in specs.items():
    o = os.path.join(sfxd, name + ".wav")
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
pows = [s["time"] for s in shots if units[s["sent"] - 1].get("beat") == "power"]
sfx = dict(whoosh=[s["time"] for s in shots],
           impact=[round(x + 0.05, 2) for x in key_starts],
           riser=[round(pows[0] - 1.2, 2)] if pows else [],
           flash=[round(x + 0.03, 2) for x in key_starts],
           whoosh_file=WAV["whoosh"], impact_file=WAV["impact"], riser_file=WAV["riser"])
print("whoosh x%d impact x%d" % (len(sfx["whoosh"]), len(sfx["impact"])))

print("karaoke + cards ...")
pop = [dict(start=s["start"], words=s["words"]) for s in sents]
ass = captions.ass_kinetic(os.path.join(PKG, story["ass"]), pop, 0.0)
captions.card(os.path.join(PKG, "title.png"),
              [(story["title"], "naskh", 150, 290, (255, 255, 255, 255), 6),
               (story.get("subtitle", ""), "naskh", 64, 500, (230, 214, 160, 255), 3),
               (story.get("part", ""), "naskh", 56, 590, (230, 214, 160, 255), 3)], fp)
captions.card(os.path.join(PKG, "end.png"),
              [(story.get("endcard", "يتبع"), "naskh", 120, 430, (255, 255, 255, 255), 6),
               (story.get("endcard2", ""), "naskh", 50, 600, (230, 214, 160, 255), 3)], fp)

print("render ...")
oname = story.get("out_film", story["out"]) if FILM else story["out"]
out = os.path.join(PKG, oname)
render.render_dynamic(ff, stills, v_sched, a_sched, sfx, win, ass,
                      os.path.join(PKG, "title.png"), os.path.join(PKG, "end.png"), out, cards=not FILM)
print("OK", out)
