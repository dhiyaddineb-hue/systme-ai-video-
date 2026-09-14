# -*- coding: utf-8 -*-
"""الصوت (§5): TTS لكل جملة + قياس حقيقي + جدولة + concat."""
import asyncio, os, subprocess
from .scenes import duration

def synth(ffmpeg, lines, voice, rate=None, pitch=None, adir="narr"):
    import edge_tts
    os.makedirs(adir, exist_ok=True)
    async def run():
        for i, l in enumerate(lines):
            f = os.path.join(adir, f"n{i:02d}.mp3")
            c = edge_tts.Communicate(l["text"], voice,
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
