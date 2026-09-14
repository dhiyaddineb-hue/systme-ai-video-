# -*- coding: utf-8 -*-
"""بوابة يوتيوب (§7.3/§7.4): meta/search/subs/download/cut.
قاعدة: التحميل عبر yt-dlp دائماً (ffmpeg static ينهار على https)."""
import json, os, re, subprocess, sys

def _run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"yt-dlp فشل: {' '.join(cmd[2:6])}\n{r.stderr[-800:]}")
    return r

def meta(url):
    r = _run([sys.executable, "-m", "yt_dlp", "--dump-json", "--no-warnings", url])
    return json.loads(r.stdout)

def search(query, limit=8):
    r = _run([sys.executable, "-m", "yt_dlp", "--flat-playlist", "--print",
              "%(id)s\t%(title)s\t%(duration)s\t%(view_count)s",
              f"ytsearch{limit}:{query}"])
    out = []
    for line in r.stdout.strip().splitlines():
        p = line.split("\t")
        if len(p) >= 4:
            out.append(dict(id=p[0], title=p[1], duration=float(p[2] or 0),
                            views=float(p[3] or 0)))
    return out

def subs_json3(url, workdir):
    os.makedirs(workdir, exist_ok=True)
    _run([sys.executable, "-m", "yt_dlp", "--skip-download", "--write-auto-subs",
          "--sub-langs", "en.*,en,ar", "--sub-format", "json3", "--no-warnings",
          "-o", os.path.join(workdir, "subs"), url])
    for f in os.listdir(workdir):
        if f.endswith(".json3"):
            return load_json3(os.path.join(workdir, f))
    return []

def load_json3(path):
    d = json.load(open(path, encoding="utf-8"))
    out = []
    for ev in d.get("events", []):
        txt = "".join(s.get("utf8", "") for s in (ev.get("segs") or [])).strip()
        if not txt or txt == "\n":
            continue
        t = (ev.get("tStartMs") or 0) / 1000.0
        if out and out[-1]["text"] == txt:
            continue
        out.append({"t": round(t, 2), "text": re.sub(r"\s+", " ", txt)})
    return out

def download(url, fmt, out, workdir=None):
    """المصادر في build/src افتراضياً (§7.5) حتى لا تأكل سقف الـWorkspace."""
    workdir = workdir or os.environ.get("VTSYS_SCRATCH") or os.path.join(os.getcwd(), "build", "src")
    os.makedirs(workdir, exist_ok=True)
    dst = os.path.join(workdir, out)
    if not os.path.exists(dst):
        _run([sys.executable, "-m", "yt_dlp", "-f", fmt, "--no-warnings", "-o", dst, url])
    return dst

def cut(ffmpeg, vsrc, asrc, start, dur, out):
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error",
           "-ss", f"{start}", "-t", f"{dur}", "-i", vsrc,
           "-ss", f"{start}", "-t", f"{dur}", "-i", asrc,
           "-map", "0:v", "-map", "1:a", "-c", "copy", "-y", out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("cut فشل:\n" + r.stderr[-600:])
    return out

def video_id(url):
    m = re.search(r"(?:v=|youtu\.be/)([\w-]{11})", url)
    return m.group(1) if m else None
