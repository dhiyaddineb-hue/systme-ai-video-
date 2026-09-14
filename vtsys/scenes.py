# -*- coding: utf-8 -*-
"""العينان الأولى والثانية (§3.1): كشف مشاهد + بصمة صوت + إطارات."""
import re, subprocess

def detect(ffmpeg, video, threshold=0.30, min_dur=6.0):
    r = subprocess.run([ffmpeg, "-hide_banner", "-i", video,
                        "-vf", f"select='gt(scene,{threshold})',showinfo",
                        "-an", "-f", "null", "-"], capture_output=True, text=True)
    cuts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r.stderr)]
    tot = duration(ffmpeg, video)
    b = [0.0] + cuts + [tot]
    merged = []
    for i in range(len(b) - 1):
        s = [round(b[i], 2), round(b[i + 1], 2)]
        if merged and (s[1] - s[0]) < min_dur:
            merged[-1][1] = s[1]
        elif merged and (merged[-1][1] - merged[-1][0]) < min_dur:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    out = []
    for s in merged:
        if out and (s[1] - s[0]) < min_dur:
            out[-1][1] = s[1]
        else:
            out.append(s)
    return [dict(id=i, start=a, end=b_, dur=round(b_ - a, 1))
            for i, (a, b_) in enumerate(out)]

def duration(ffmpeg, path):
    r = subprocess.run([ffmpeg, "-i", path], capture_output=True, text=True)
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)

def audio_profile(ffmpeg, audio, start, dur):
    r = subprocess.run([ffmpeg, "-hide_banner", "-ss", f"{start}", "-t", f"{dur}",
                        "-i", audio, "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True)
    mean = float(re.search(r"mean_volume: ([-0-9.]+) dB", r.stderr).group(1))
    mx = float(re.search(r"max_volume: ([-0-9.]+) dB", r.stderr).group(1))
    cls = "work_loud" if mx > -6 else "work_mid" if mx > -12 else "nature_quiet"
    return dict(mean_db=mean, max_db=mx, cls=cls)

def frame(ffmpeg, video, t, out, width=480):
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}",
                    "-i", video, "-frames:v", "1", "-vf", f"scale={width}:-1",
                    "-y", out], check=True, capture_output=True)
    return out
