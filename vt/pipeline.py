#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام "تعليق سريع" — خط إنتاج كامل:
  رابط فيديو → بيانات → قرار (هل أعلّق؟) → ترجمة → سكريبت خليجي → صوت → مونتاج 9:16 → ثامبنيل → باكج نشر

الاستخدام:
  python3 pipeline.py <YOUTUBE_URL> [--start 1194] [--voice ar-KW-FahedNeural]
                      [--script script.json] [--out DIR] [--niche a,b,c]

ملاحظات:
  * بدون مفتاح LLM: السكريبت يبنى من قوالب خليجية + بيانات الفيديو والترجمة.
  * مع مفتاح (OPENROUTER_API_KEY أو OPENAI_API_KEY): السكريبت يكتبه النموذج بأسلوب أفضل.
  * ffmpeg الستاتك في هذه البيئة ينهار على روابط https، لذلك التحميل عبر yt-dlp والقص محلياً.
"""
import argparse, asyncio, json, os, re, subprocess, sys, shutil

HERE   = os.path.dirname(os.path.abspath(__file__))
FF     = None  # مسار ffmpeg
FONT_AR= os.path.join(HERE, "..", "assets", "fonts", "NotoSansArabic-Bold.ttf")
sys.path.insert(0, HERE)
from decision_engine import score_video            # noqa: E402
from transcript import load_json3                  # noqa: E402

def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"فشل الأمر: {' '.join(cmd[:6])}...\n{r.stderr[-1500:]}")
    return r

def find_ffmpeg():
    global FF
    if shutil.which("ffmpeg"): FF = "ffmpeg"; return
    import imageio_ffmpeg; FF = imageio_ffmpeg.get_ffmpeg_exe()

def ffprobe_dur(path):
    r = subprocess.run([FF, "-i", path], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    h, mi, s = m.groups(); return int(h)*3600 + int(mi)*60 + float(s)

# ───────────────────────── 1) الجلب والقرار ─────────────────────────
def fetch_meta(url, work):
    out = os.path.join(work, "meta.json")
    r = subprocess.run([sys.executable, "-m", "yt_dlp", "--dump-json", "--no-warnings", url],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"فشل جلب البيانات:\n{r.stderr[-1500:]}")
    json.dump(json.loads(r.stdout), open(out, "w", encoding="utf-8"), ensure_ascii=False)
    return json.loads(r.stdout)

def fetch_subs(url, work):
    sh([sys.executable, "-m", "yt_dlp", "--skip-download", "--write-auto-subs",
        "--sub-langs", "en.*,en", "--sub-format", "json3", "--no-warnings",
        "-o", os.path.join(work, "subs"), url])
    for f in os.listdir(work):
        if f.endswith(".json3"): return load_json3(os.path.join(work, f))
    return []

# ───────────────────────── 2) السكريبت ─────────────────────────
GULF_TEMPLATES = [
    ("hook",     "لقيت فيديو جاب {views} مشاهدة، وقعدت له {dur} دقيقة كاملة. والصراحة؟ يستاهل."),
    ("summary",  "القناة {channel} سوّت فكرة بسيطة بس عبقرية: {gist}"),
    ("insight",  "وأهم شي: الفيديو ما يعلّمك بالنظرية، يخليك تطبق وأنت تشوف، خطوة خطوة."),
    ("opinion",  "وهنا النقطة اللي وقفتني: الأسلوب يخلي المعلومة تثبت بمخك من غير ما تحس إنك تذاكر."),
    ("detail",   "وفيه لحظة بالنص تعطيك قاعدة عملية تنفعك كل يوم، بس ما أبغى أحرقها عليك."),
    ("cta",      "إذا مجالك قريب من الموضوع، أعطه فرصة وقولي وش صار. والرابط بالتعليق المثبت."),
]

def build_script_template(meta, segs):
    words = " ".join(s["text"] for s in segs[:40]).split()
    gist  = " ".join(words[:14]) + "…"
    fmt = dict(views=f"{meta['view_count']:,}".replace(",", "،"),
               dur=round(meta["duration"]/60), channel=meta["channel"].strip(), gist=gist)
    return [{"id": i+1, "type": t, "text": txt.format(**fmt)}
            for i, (t, txt) in enumerate(GULF_TEMPLATES)]

def build_script_llm(meta, segs):
    """لو فيه مفتاح نموذج لغوي — سكريبت بجودة أعلى بكثير."""
    import urllib.request
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not key: return None
    sample = " ".join(s["text"] for s in segs[:120])[:3000]
    prompt = (f"اكتب تعليق فيديو بأسلوب شاب خليجي عفوي (مو رسمي) عن هذا الفيديو.\n"
              f"العنوان: {meta['title']} | القناة: {meta['channel']} | المدة: {meta['duration']//60} دقيقة\n"
              f"مقتطف من التفريغ: {sample}\n"
              f"أرجع JSON فقط: قائمة 6 مقاطع بأنواع hook,summary,insight,opinion,detail,cta — "
              f"كل مقطع جملة-جملتين بالكلام المنطوق فقط.")
    body = json.dumps({"model": os.environ.get("LLM_MODEL", "openai/gpt-4o-mini"),
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", body,
                                 {"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        res = json.load(urllib.request.urlopen(req, timeout=90))
        segs_llm = json.loads(res["choices"][0]["message"]["content"])
        return [{"id": i+1, **s} for i, s in enumerate(segs_llm)]
    except Exception as e:
        print("⚠️ LLM فشل، رجعت للقوالب:", e); return None

# ───────────────────────── 3) الصوت ─────────────────────────
def synth(script, work, voice):
    import edge_tts
    adir = os.path.join(work, "audio"); os.makedirs(adir, exist_ok=True)
    async def run():
        for s in script:
            await edge_tts.Communicate(s["text"], voice, rate="-4%").save(
                os.path.join(adir, f"s{s['id']:02d}.mp3"))
    asyncio.run(run())
    durs = {f"s{s['id']:02d}.mp3": round(ffprobe_dur(os.path.join(adir, f"s{s['id']:02d}.mp3")), 2)
            for s in script}
    json.dump(durs, open(os.path.join(work, "durations.json"), "w"), indent=1)
    lst = os.path.join(work, "volist.txt")
    open(lst, "w").write("".join(f"file 'audio/s{s['id']:02d}.mp3'\n" for s in script))
    sh([FF, "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
        "-c", "copy", "-y", os.path.join(work, "vo.mp3")])
    return durs, sum(durs.values())

# ───────────────────────── 4) الفيديو الخام ─────────────────────────
def fetch_clip(url, work, start, length):
    v = os.path.join(work, "vfull.mp4"); a = os.path.join(work, "afull.m4a")
    if not os.path.exists(v):
        sh([sys.executable, "-m", "yt_dlp", "-f", "135/134/133", "--no-warnings", "-o", v, url])
    if not os.path.exists(a):
        sh([sys.executable, "-m", "yt_dlp", "-f", "140", "--no-warnings", "-o", a, url])
    clip = os.path.join(work, "clip60.mp4")
    sh([FF, "-hide_banner", "-loglevel", "error", "-ss", str(start), "-t", str(length+1.5), "-i", v,
        "-ss", str(start), "-t", str(length+1.5), "-i", a, "-map", "0:v", "-map", "1:a",
        "-c", "copy", "-y", clip])
    return clip

# ───────────────────────── 5) الكابشنز + البانر ─────────────────────────
def build_captions(script, durs, work):
    import arabic_reshaper as ar
    from bidi.algorithm import get_display
    t = 0.0; times = []
    for s in script:
        d = durs[f"s{s['id']:02d}.mp3"]; times.append((round(t, 2), round(t+d, 2))); t += d
    ts = lambda x: f"{int(x//3600)}:{int(x%3600//60):02d}:{x%60:05.2f}"
    hdr = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n"
           "ScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
           "Style: Cap,Noto Sans Arabic,62,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,4,2,2,60,60,290,1\n"
           "Style: Tag,Noto Sans Arabic,46,&H0000E5FF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,1,0,3,3,1,2,60,60,470,1\n\n"
           "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    lab = {"hook": "— الهوك —", "summary": "— القصة —", "insight": "— الفكرة —",
           "opinion": "— رأيي —", "detail": "— لقطة مهمة —", "cta": "— الخلاصة —"}
    ev = []
    for s, (a, b) in zip(script, times):
        ev.append(f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{get_display(ar.reshape(s['text']))}")
        ev.append(f"Dialogue: 1,{ts(a)},{ts(min(a+2.4, b))},Tag,,0,0,0,,{get_display(ar.reshape(lab.get(s['type'], '—'))) }")
    p = os.path.join(work, "captions.ass"); open(p, "w", encoding="utf-8").write(hdr + "\n".join(ev) + "\n")
    return p, times, t

def build_banner(work, l1_text, l2_ar="المصدر:", l2_lat=""):
    import arabic_reshaper as ar
    from bidi.algorithm import get_display
    from PIL import Image, ImageDraw, ImageFont
    LAT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    W, H = 1080, 300
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle([36, 26, W-36, H-26], radius=40, fill=(8, 8, 16, 210))
    d.rounded_rectangle([36, 26, W-36, H-26], radius=40, outline=(255, 201, 60, 255), width=5)
    def fit(text, path, start, minsize, maxw):
        size = start
        while size > minsize:
            f = ImageFont.truetype(path, size)
            if d.textlength(text, font=f) <= maxw: return f
            size -= 2
        return ImageFont.truetype(path, minsize)
    l1 = get_display(ar.reshape(l1_text)); f1 = fit(l1, FONT_AR, 62, 34, 940)
    d.text(((W-d.textlength(l1, font=f1))/2, 58), l1, font=f1, fill=(255, 255, 255, 255))
    ap = get_display(ar.reshape(l2_ar)); fa = ImageFont.truetype(FONT_AR, 36)
    fl = ImageFont.truetype(LAT, 36); wa = d.textlength(ap, font=fa); wl = d.textlength(l2_lat, font=fl)
    x0 = (W-(wa+wl+14))/2
    d.text((x0+wl+14, 192), ap, font=fa, fill=(255, 201, 60, 255))
    if l2_lat: d.text((x0, 192), l2_lat, font=fl, fill=(255, 201, 60, 255))
    p = os.path.join(work, "banner.png"); img.save(p); return p

# ───────────────────────── 6) التركيب النهائي ─────────────────────────
def render(clip, work, total, banner, captions, out):
    fc = (f"[0:v]fps=30,scale=3840:2160:flags=lanczos,"
          f"zoompan=z='1+0.12*on/{int(total*30)}':x='(iw-iw/zoom)*(0.20+0.60*on/{int(total*30)})':"
          f"y='(ih-ih/zoom)/2':d=1:s=1080x1920:fps=30,setsar=1[base];"
          f"[base][2:v]overlay=0:36[tmp];[tmp]ass={captions}[t2];"
          f"[t2]drawbox=x=0:y=1906:w='min(t/{total},1)*1080':h=14:color=0xFFC93C@0.95:t=fill[vout];"
          f"[0:a]volume=0.12[bg];[1:a]volume=1.0[vc];"
          f"[vc][bg]amix=inputs=2:duration=first:normalize=0,afade=t=out:st={total-1.5}:d=1.4[aout]")
    sh([FF, "-hide_banner", "-loglevel", "error", "-i", clip, "-i", os.path.join(work, "vo.mp3"),
        "-loop", "1", "-i", banner, "-filter_complex", fc, "-map", "[vout]", "-map", "[aout]",
        "-t", f"{total:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
        "-movflags", "+faststart", "-y", out])

# ───────────────────────── الرئيسي ─────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url"); ap.add_argument("--start", type=float, default=0)
    ap.add_argument("--voice", default="ar-KW-FahedNeural")
    ap.add_argument("--script", help="سكريبت جاهز JSON (تجاوز التوليد)")
    ap.add_argument("--niche", default=""); ap.add_argument("--out", default=None)
    a = ap.parse_args()

    find_ffmpeg()
    vid = re.search(r"(?:v=|youtu\.be/)([\w-]{11})", a.url).group(1)
    work = a.out or os.path.join(HERE, "runs", vid); os.makedirs(work, exist_ok=True)
    print(f"📥 [1/6] بيانات الفيديو {vid}")
    meta = fetch_meta(a.url, work)
    rep = score_video(meta, [x for x in a.niche.split(",") if x])
    json.dump(rep, open(os.path.join(work, "decision_report.json"), "w"), ensure_ascii=False, indent=2)
    print(f"   القرار: {rep['verdict']}  ({rep['total']}/100)")

    print("📝 [2/6] الترجمة")
    segs = fetch_subs(a.url, work)
    print(f"   {len(segs)} مقطع مترجم")

    print("✍️  [3/6] السكريبت")
    script = None
    if a.script: script = json.load(open(a.script, encoding="utf-8"))["segments"]
    if not script: script = build_script_llm(meta, segs) or build_script_template(meta, segs)
    json.dump({"video_id": vid, "voice": a.voice, "segments": script},
              open(os.path.join(work, "script.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print("🎙️  [4/6] الصوت")
    durs, total = synth(script, work, a.voice)
    print(f"   مدة الفويس أوفر: {total:.1f} ثانية")

    print("🎬 [5/6] القص والمونتاج")
    start = a.start or max(0, meta["duration"]/2 - total/2)
    clip = fetch_clip(a.url, work, int(start), total)
    cap, times, _ = build_captions(script, durs, work)
    ban = build_banner(work, "شفت المقطع ولخّصته لك بستين ثانية",
                       "المصدر:", meta["channel"].strip())
    out = os.path.join(work, "final_short.mp4")
    render(clip, work, total, ban, cap, out)
    print(f"   ✅ {out}")

    print("📦 [6/6] الباكج")
    print(json.dumps(dict(video=vid, title=meta["title"], decision=rep["verdict"],
                          score=rep["total"], duration_s=round(total, 2), output=out),
                     ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
