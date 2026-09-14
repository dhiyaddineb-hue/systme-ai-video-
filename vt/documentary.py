#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
الوضع الوثائقي (documentary mode) — لفيديوهات بلا كلام (بناء/طبيعة/ASMR):
  لا ترجمة ⇒ النظام "يشوف": كشف مشاهد + تحليل صوت + سرد راوٍ.

  python3 documentary.py <URL> --window START END --narration narration.json
                             [--voice ar-SY-LaithNeural] [--out DIR]

مراحل:
 1) كشف المشاهد: ffmpeg select='gt(scene,0.30)' + دمج القطع < 6 ثوانٍ
 2) تحليل صوت كل مشهد: volumedetect ⇒ تصنيف (صخب عمل / عمل متوسط / همس طبيعة)
 3) استخراج إطار وسط كل مشهد ⇒ (وكيل بصري: الإنسان/النموذج) يكتب السرد
 4) جدولة السرد: lead-in + عدم تراكب + تغطية 40-60% (قاعدة تنفّس الوثائقيات)
 5) تركيب: داكنة سينمائية + سبتايتل Naskh داخل الشريط + Ducking جانبي
    (sidechaincompress: صوت الطبيعة ينخفض حين يتكلم الراوي) + loudnorm -16 LUFS
"""
import argparse, asyncio, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from textutil import ar_text  # noqa: E402

FF = os.environ.get("FFMPEG", "ffmpeg")
NASKH = os.path.join(HERE, "..", "assets", "fonts", "NotoNaskhArabic.ttf")

def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError("فشل: " + " ".join(cmd[:5]) + "\n" + r.stderr[-1200:])
    return r

def dur_of(p):
    r = subprocess.run([FF, "-i", p], capture_output=True, text=True)
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr).groups()
    return int(h)*3600 + int(m)*60 + float(s)

# ── 1) المشاهد ────────────────────────────────────────────────
def detect_scenes(video, threshold=0.30, min_dur=6.0):
    r = subprocess.run([FF, "-hide_banner", "-i", video,
                        "-vf", f"select='gt(scene,{threshold})',showinfo",
                        "-an", "-f", "null", "-"], capture_output=True, text=True)
    cuts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r.stderr)]
    total = dur_of(video)
    bounds = [0.0] + cuts + [total]
    merged = []
    for i in range(len(bounds)-1):
        s = [round(bounds[i], 2), round(bounds[i+1], 2)]
        if merged and (s[1]-s[0]) < min_dur:
            merged[-1][1] = s[1]
        elif merged and (merged[-1][1]-merged[-1][0]) < min_dur:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    out = []
    for s in merged:
        if out and (s[1]-s[0]) < min_dur:
            out[-1][1] = s[1]
        else:
            out.append(s)
    return [dict(id=i, start=a, end=b, dur=round(b-a, 1))
            for i, (a, b) in enumerate(out)]

# ── 2) صوت المشهد ─────────────────────────────────────────────
def audio_profile(audio, start, d):
    r = subprocess.run([FF, "-hide_banner", "-ss", f"{start}", "-t", f"{d}",
                        "-i", audio, "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True)
    mean = float(re.search(r"mean_volume: ([-0-9.]+) dB", r.stderr).group(1))
    mx = float(re.search(r"max_volume: ([-0-9.]+) dB", r.stderr).group(1))
    cls = "work_loud" if mx > -6 else "work_mid" if mx > -12 else "nature_quiet"
    return mean, mx, cls

# ── 3) إطار لكل مشهد (للوكيل البصري) ─────────────────────────
def grab_frame(video, t, out_png, width=480):
    sh([FF, "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", video,
        "-frames:v", "1", "-vf", f"scale={width}:-1", "-y", out_png])

# ── 4) السرد + الجدولة ────────────────────────────────────────
DOC_TEMPLATES = {  # سقوط حرّ لو ما فيه وكيل بصري/LLM
    "open":  "هنا، حيث لا تصل الضوضاء… يبدأ الإنسان عمله القديم.",
    "work":  "يداه تعرفان الطريق: لا عجلة، لا تردد… فقط إيقاع الغابة.",
    "quiet": "وفي الصمت، تفصيلٌ صغير يصنع الفرق بين البقاء والضياع.",
    "close": "وهكذا، يوماً بعد يوم… تولد من العدم مأوىً دافئة.",
}

def schedule(lines, scenes_by_id, first_lead=3.0, gap=0.8):
    sched, cursor = [], 0.0
    for i, l in enumerate(lines):
        sc = scenes_by_id[l["scene"]]
        start = max(sc["start"] + (first_lead if i == 0 else gap), cursor + gap)
        sched.append(dict(scene=l["scene"], text=l["text"], file=l["file"],
                          start=round(start, 2), dur=l["dur"]))
        cursor = start + l["dur"]
    return sched

def synth_narration(lines, voice, rate="-8%", pitch="-4Hz", adir="narr"):
    import edge_tts
    os.makedirs(adir, exist_ok=True)
    async def run():
        for i, l in enumerate(lines):
            f = os.path.join(adir, f"n{i:02d}.mp3")
            l["file"] = f
            await edge_tts.Communicate(l["text"], voice, rate=rate, pitch=pitch).save(f)
            l["dur"] = round(dur_of(f), 2)
    asyncio.run(run())
    return lines

# ── 5) السبتايتل (libass) ─────────────────────────────────────
def build_ass(sched, w0, path, size=50):
    ts = lambda x: f"{int(max(0,x)//3600)}:{int(max(0,x)%3600//60):02d}:{max(0,x)%60:05.2f}"
    hdr = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 0\n"
           "ScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
           f"Style: Doc,Noto Naskh Arabic,{size},&H00F0F0F0,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,1.5,0,1,2,1,2,140,140,34,1\n\n"
           "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    # ملاحظة: libass يشكّل بنفسه؛ مرّر نصاً خاماً في الأنظمة الجديدة
    ev = [f"Dialogue: 0,{ts(s['start']-w0)},{ts(s['start']+s['dur']-w0)},Doc,,0,0,0,,{s['text']}"
          for s in sched]
    open(path, "w", encoding="utf-8").write(hdr + "\n".join(ev) + "\n")
    return path

def build_card(path, lines_specs):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for text, fsize, y, fill, sw in lines_specs:
        f = ImageFont.truetype(NASKH, fsize); t = ar_text(text)
        w = d.textlength(t, font=f)
        d.text(((1920-w)/2, y), t, font=f, fill=fill, stroke_width=sw, stroke_fill=(0, 0, 0, 220))
    img.save(path)

# ── 6) الرندر ─────────────────────────────────────────────────
def render(clip, sched, w0, win, ass, title_png, end_png, out, fps=25):
    n = len(sched)
    parts = []
    for i, s in enumerate(sched):
        ms = int(round((s["start"]-w0)*1000))
        parts.append(f"[{i+1}:a]adelay={ms}|{ms}[d{i}]")
    parts.append("".join(f"[d{i}]" for i in range(n)) +
                 f"amix=inputs={n}:duration=longest:normalize=0,asplit=2[vo1][vo2]")
    parts += [
        "[0:a]volume=0.9[amb]",
        "[amb][vo1]sidechaincompress=threshold=0.03:ratio=6:attack=25:release=400[ambd]",
        "[ambd][vo2]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[aout]",
        f"[0:v]fps={fps},scale=2304:1296:flags=bicubic,"
        f"zoompan=z='1+0.10*on/{int(win*fps)}':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:s=1920x1080:fps={fps},setsar=1[b0]",
        "[b0]drawbox=y=0:h=110:color=black:t=fill,drawbox=y=970:h=110:color=black:t=fill[b1]",
        f"[b1]ass={ass}[b2]",
        f"[b2]drawbox=x=0:y=0:w=1920:h=1080:color=black@0.55:t=fill:enable='gte(t,{win-4.2:.1f})'[b3]",
        f"[{n+1}:v]format=rgba,fade=t=in:st=0.6:d=1.0:alpha=1,fade=t=out:st=4.0:d=1.0:alpha=1[ti]",
        f"[{n+2}:v]format=rgba,fade=t=in:st={win-4.0:.1f}:d=0.9:alpha=1[en]",
        "[b3][ti]overlay=0:0:enable='between(t,0.4,5.1)'[b4]",
        f"[b4][en]overlay=0:0:enable='gte(t,{win-4.1:.1f})'[vout]",
    ]
    cmd = [FF, "-hide_banner", "-loglevel", "warning", "-i", clip]
    cmd += [x for s in sched for x in ("-i", s["file"])]
    cmd += ["-loop", "1", "-i", title_png, "-loop", "1", "-i", end_png,
            "-filter_complex", ";".join(parts), "-map", "[vout]", "-map", "[aout]",
            "-t", f"{win:.2f}", "-r", str(fps), "-c:v", "libx264", "-preset", "fast",
            "-crf", "19", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.2",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", "-y", out]
    sh(cmd)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url"); ap.add_argument("--window", nargs=2, type=float, required=True)
    ap.add_argument("--narration", required=True, help="JSON: {voice,title,subtitle,endcard,lines:[{scene,text}]}")
    ap.add_argument("--out", default=os.path.join(HERE, "runs", "doc"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    w0, w1 = a.window; win = w1 - w0

    print("🎬 قص النافذة")
    sh([sys.executable, "-m", "yt_dlp", "-f", "137/136/135", "--no-warnings",
        "-o", os.path.join(a.out, "vfull.mp4"), a.url])
    sh([sys.executable, "-m", "yt_dlp", "-f", "140", "--no-warnings",
        "-o", os.path.join(a.out, "afull.m4a"), a.url])
    sh([FF, "-hide_banner", "-loglevel", "error", "-ss", f"{w0}", "-t", f"{win}",
        "-i", os.path.join(a.out, "vfull.mp4"), "-ss", f"{w0}", "-t", f"{win}",
        "-i", os.path.join(a.out, "afull.m4a"), "-map", "0:v", "-map", "1:a",
        "-c", "copy", "-y", os.path.join(a.out, "clip.mp4")])

    cfg = json.load(open(a.narration, encoding="utf-8"))
    print("🎙️ تركيب السرد")
    lines = synth_narration(cfg["lines"], cfg["voice"],
                            cfg.get("rate", "-8%"), cfg.get("pitch", "-4Hz"),
                            os.path.join(a.out, "narr"))
    scenes = detect_scenes(os.path.join(a.out, "clip.mp4"))
    # إعادة تعيين معرفات مشاهد النافذة محلياً
    sbid = {s["id"]: s for s in scenes}
    sched = schedule(lines, sbid)
    json.dump(sched, open(os.path.join(a.out, "sched.json"), "w"), ensure_ascii=False, indent=1)
    tot = sum(s["dur"] for s in sched)
    print(f"   تغطية السرد: {tot/win*100:.0f}% (هدف 40-60%)")

    print("📝 سبتايتل وبطاقات")
    ass = build_ass(sched, 0.0, os.path.join(a.out, "doc.ass"))
    build_card(os.path.join(a.out, "title.png"),
               [(cfg["title"], 108, 330, (255, 255, 255, 255), 5),
                (cfg["subtitle"], 54, 480, (230, 214, 160, 255), 3)])
    build_card(os.path.join(a.out, "end.png"), [(cfg["endcard"], 108, 470, (255, 255, 255, 255), 5)])

    print("🎞️ الرندر النهائي")
    render(os.path.join(a.out, "clip.mp4"), sched, 0.0, win, ass,
           os.path.join(a.out, "title.png"), os.path.join(a.out, "end.png"),
           os.path.join(a.out, "final_doc.mp4"))
    print("✅", os.path.join(a.out, "final_doc.mp4"))

if __name__ == "__main__":
    main()
