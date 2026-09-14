# -*- coding: utf-8 -*-
"""محرك الديناميكية السينمائية (§4.8): حركة مصممة لكل لقطة حسب نوعها ومزاجها.
- key_action: اقتحام سريع + اهتزاز + فلاش · detail: انسحاب كاشف · البقية: دفع متنوع.
- تدرج مزاجي: كل نبضة لونها (دفء/رهبة/انفجار…).
"""
MOTION = {
    "key_action": {"z0": 1.00, "z1": 1.18, "shake": 10, "sat": 1.25},
    "detail": {"z0": 1.12, "z1": 1.00, "shake": 0, "sat": 1.15},
    "reaction": {"z0": 1.00, "z1": 1.10, "shake": 0, "sat": 1.10},
    "establishing": {"z0": 1.00, "z1": 1.06, "shake": 0, "sat": 1.05},
    "transition": {"z0": 1.06, "z1": 1.00, "shake": 0, "sat": 1.00},
}

MOOD_GRADE = {
    "تشويق": "colorbalance=rs=0.05:gs=0.0:bs=0.10",
    "دفء": "colorbalance=rs=0.12:gs=0.05:bs=-0.08",
    "انكسار": "eq=saturation=0.82,colorbalance=rs=-0.05:bs=0.05",
    "رهبة": "colorbalance=rs=-0.08:gs=-0.03:bs=0.12",
    "انفجار": "eq=saturation=1.3,colorbalance=rs=0.08:bs=-0.05",
    "توتر": "eq=contrast=1.08:brightness=-0.02",
}

def beat_video_chain(idx, dur, shot, fps=25):
    """سلسلة فيديو الـ beat: (اهتزاز) ← scale ← zoompan ← تشبع ← تدرج مزاجي ← vignette."""
    N = max(1, int(dur * fps))
    pan = 0.18 if idx % 2 == 0 else 0.82
    m = MOTION.get(shot.get("type", "reaction"), MOTION["reaction"])
    parts = ["scale=1920:1080"]
    if m["shake"]:
        a = m["shake"]
        parts.append(
            f"crop=iw-24:ih-24:x='12+{a}*sin(2*PI*t*22)*max(0,1-t/0.35)'"
            f":y='12+{a}*cos(2*PI*t*19)*max(0,1-t/0.35)',scale=1920:1080")
    parts.append(
        f"zoompan=z='{m['z0']}+({m['z1']}-{m['z0']})*on/{N}':"
        f"x='(iw-iw/zoom)*{pan}':y='(ih-ih/zoom)/2':d=1:s=1280x720:fps={fps}")
    parts.append(f"eq=saturation={m['sat']}")
    if shot.get("mood") in MOOD_GRADE:
        parts.append(MOOD_GRADE[shot["mood"]])
    parts.append("vignette=PI/5,setsar=1")
    return f"[{idx}:v]" + ",".join(parts) + f"[v{idx}]"
