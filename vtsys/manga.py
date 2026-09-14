# -*- coding: utf-8 -*-
"""الخط 🅲: لوحات → قطع Ken Burns → قاعدة concat (§4)."""
import os, subprocess

def build_base(ff, panels, sched, workdir, res=(1280, 720)):
    os.makedirs(workdir, exist_ok=True)
    segs = []
    for i, s in enumerate(sched):
        p = panels[s["idx"]] if isinstance(panels, list) else panels[s["panel"]]
        N = int(s["scene_dur"] * 25)
        pan = 0.18 if i % 2 == 0 else 0.82
        seg = os.path.join(workdir, f"seg{i:02d}.mp4")
        vf = (f"scale=1536:1024,crop=1536:864:0:80,scale=2560:1440:flags=lanczos,"
              f"zoompan=z='1+0.12*on/{N}':x='(iw-iw/zoom)*{pan}':y='(ih-ih/zoom)/2':d=1:"
              f"s={res[0]}x{res[1]}:fps=25,vignette=PI/5,setsar=1")
        subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-loop", "1",
                        "-framerate", "25", "-t", f"{s['scene_dur']}", "-i", p,
                        "-vf", vf, "-c:v", "libx264", "-preset", "ultrafast",
                        "-crf", "18", "-pix_fmt", "yuv420p", "-y", seg],
                       check=True, capture_output=True)
        segs.append(seg)
    lst = os.path.join(workdir, "list.txt")
    open(lst, "w").write("".join(f"file '{os.path.abspath(s)}'\n" for s in segs))
    base = os.path.join(workdir, "base.mp4")
    subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-f", "concat",
                    "-safe", "0", "-i", lst, "-c", "copy", "-y", base],
                   check=True, capture_output=True)
    for s in segs:
        os.remove(s)
    os.remove(lst)
    return base
