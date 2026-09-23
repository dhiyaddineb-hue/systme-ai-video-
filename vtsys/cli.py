# -*- coding: utf-8 -*-
"""CLI الموحّد: python3 -m vtsys <cmd>."""
import argparse, json, os, glob

from . import config, env, decision, youtube, scenes, scriptwriter, tts, \
    captions, render, queue as q, storage, thumb, audit, audio_qc, script_audit, visual_qc

def _ff(cfg):
    return env.ensure_ffmpeg(cfg["_root"])

def _fonts(cfg):
    fp = {}
    for k, rel in cfg["fonts"].items():
        fp[k] = rel if os.path.isabs(rel) else os.path.join(cfg["_root"], rel)
    return fp

# ───────── أوامر ─────────
def cmd_selftest(a, cfg):
    rep = env.selftest(cfg["_root"])
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    print("💾", storage.report(cfg["_root"], cfg["storage_budget_mb"]))

def cmd_audit(a, cfg):
    rep = audit.audit_package(a.package, rendered=a.rendered)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    if rep["status"] != "PASS":
        raise SystemExit(2)

def cmd_audio_audit(a, cfg):
    ff = _ff(cfg); rep = audio_qc.audit(ff, a.files)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    if rep['status'] != 'PASS': raise SystemExit(2)

def cmd_script_audit(a, cfg):
    rep = script_audit.audit(a.script, max_words=a.max_words)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    if rep['status'] != 'PASS': raise SystemExit(2)

def cmd_visual_audit(a, cfg):
    rep = visual_qc.audit(a.files, min_width=a.min_width, min_height=a.min_height)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    if rep['status'] != 'PASS': raise SystemExit(2)

def cmd_decide(a, cfg):
    m = youtube.meta(a.url)
    rep = decision.score(m, a.niche or cfg["niche"], cfg["threshold"])
    out = os.path.join(a.out or os.path.join(cfg["_root"], "runs", m["id"]), "decision.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(rep, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    if a.enqueue:
        ok = q.add(cfg["_root"], m["id"], a.url, m["title"], rep["total"], rep["verdict"])
        print("📥 أُضيف للطابور" if ok else "⚠️ موجود مسبقاً")

def cmd_scan(a, cfg):
    res = youtube.search(a.query, a.limit)
    print(f"🔎 {len(res)} نتيجة لـ: {a.query}\n")
    for r in res:
        url = f"https://youtu.be/{r['id']}"
        try:
            m = youtube.meta(url)
            rep = decision.score(m, a.niche or cfg["niche"], cfg["threshold"])
            tag = "🎬 وثائقي؟" if rep.get("silent_candidate") else ""
            print(f"[{rep['total']:>3}] {rep['verdict']:<22} {r['title'][:60]} {tag}")
            if a.enqueue and rep["total"] >= cfg["threshold"]:
                q.add(cfg["_root"], r["id"], url, m["title"], rep["total"], rep["verdict"])
        except Exception as e:
            print(f"  ⚠️ {r['id']}: {e}")

def cmd_short(a, cfg):
    ff = _ff(cfg); fp = _fonts(cfg)
    m = youtube.meta(a.url)
    rep = decision.score(m, cfg["niche"], cfg["threshold"])
    print(f"🧭 القرار: {rep['verdict']} ({rep['total']}/100)")
    work = a.out or os.path.join(cfg["_root"], "runs", m["id"]); os.makedirs(work, exist_ok=True)
    segs = youtube.subs_json3(a.url, work)
    if a.script:
        script = json.load(open(a.script, encoding="utf-8"))["segments"]
    else:
        raw = scriptwriter.llm(scriptwriter.GULF_SCRIPT_PROMPT.format(
            title=m["title"], channel=m["channel"],
            sample=" ".join(s["text"] for s in segs[:120])[:2500]))
        script = json.loads(raw) if raw else scriptwriter.gulf(m, segs)
    lines = tts.synth(ff, script, cfg["voices"]["gulf"], **cfg["tts"]["gulf"], adir=os.path.join(work, "audio"))
    t = 0.0; times = []
    for l in lines:
        times.append((round(t, 2), round(t + l["dur"], 2))); t += l["dur"]
    v = youtube.download(a.url, "135/134/133", "v.mp4"); au = youtube.download(a.url, "140", "a.m4a")
    clip = youtube.cut(ff, v, au, a.start if a.start else max(0, m["duration"]/2 - t/2), t + 1.5,
                       os.path.join(work, "clip.mp4"))
    ass = captions.ass_short(os.path.join(work, "captions.ass"), lines, times)
    ban = thumb.banner_short(os.path.join(work, "banner.png"),
                             "شفت المقطع ولخّصته لك بستين ثانية", "المصدر:", m["channel"].strip(), fp)
    out = os.path.join(work, "final_short.mp4")
    render.render_short(ff, clip, tts.concat_vo(ff, lines, os.path.join(work, "vo.mp3")),
                        ban, ass, t, out)
    print("✅", out)

def cmd_doc(a, cfg):
    ff = _ff(cfg); fp = _fonts(cfg)
    w0, w1 = a.window; win = w1 - w0
    work = a.out or os.path.join(cfg["_root"], "runs", "doc"); os.makedirs(work, exist_ok=True)
    v = youtube.download(a.url, "137/136/135", "v.mp4"); au = youtube.download(a.url, "140", "a.m4a")
    clip = youtube.cut(ff, v, au, w0, win, os.path.join(work, "clip.mp4"))
    cfgj = json.load(open(a.narration, encoding="utf-8"))
    sc = scenes.detect(ff, clip)
    sbid = {s["id"]: s for s in sc}
    lines = tts.synth(ff, cfgj["lines"], cfgj.get("voice", cfg["voices"]["doc"]),
                      rate=cfgj.get("rate", "-8%"), pitch=cfgj.get("pitch", "-4Hz"),
                      adir=os.path.join(work, "narr"))
    sched, tcur = [], 0.0
    for i, l in enumerate(lines):
        st = max(sbid[l["scene"]]["start"] + (3.0 if i == 0 else 0.8), tcur + 0.8)
        sched.append(dict(idx=i, text=l["text"], file=l["file"], dur_narr=l["dur"],
                          start=round(st, 2), scene_dur=None))
        tcur = st + l["dur"]
    cov = tts.coverage(sched, win)
    lo, hi = cfg["coverage"]["doc"]
    print(f"🎙️ تغطية السرد: {cov}% (هدف {lo*100:.0f}-{hi*100:.0f}%)")
    ass = captions.ass_doc(os.path.join(work, "doc.ass"), sched, w0)
    captions.card(os.path.join(work, "title.png"),
                  [(cfgj["title"], "naskh", 108, 330, (255, 255, 255, 255), 5),
                   (cfgj.get("subtitle", ""), "naskh", 54, 480, (230, 214, 160, 255), 3)], fp)
    captions.card(os.path.join(work, "end.png"),
                  [(cfgj.get("endcard", "يتبع"), "naskh", 108, 470, (255, 255, 255, 255), 5)], fp)
    out = os.path.join(work, "final_doc.mp4")
    render.render_doc(ff, clip, sched, w0, win, ass, os.path.join(work, "title.png"),
                      os.path.join(work, "end.png"), out, res=a.res)
    print("✅", out)

def cmd_manga(a, cfg):
    ff = _ff(cfg); fp = _fonts(cfg)
    story = json.load(open(a.story, encoding="utf-8"))
    panels = sorted(glob.glob(os.path.join(a.panels, "*.jpg")) +
                    glob.glob(os.path.join(a.panels, "*.png")))
    assert len(panels) >= len(story["lines"]), "لوحات أقل من النبضات!"
    work = a.out or os.path.join(cfg["_root"], "runs", "manga"); os.makedirs(work, exist_ok=True)
    lines = tts.synth(ff, story["lines"], story.get("voice", cfg["voices"]["doc"]),
                      rate=story.get("rate", "-8%"), pitch=story.get("pitch", "-4Hz"),
                      adir=os.path.join(work, "narr"))
    sched, t = [], 0.0
    for i, (l, bd) in enumerate(zip(lines, story.get("base_durs", [12] * len(lines)))):
        sd = round(max(bd, l["dur"] + 3.0), 1)
        st = round(t + (2.5 if i == 0 else 0.6), 2)
        sched.append(dict(idx=i, panel=l.get("panel", i + 1), text=l["text"], file=l["file"],
                          dur_narr=l["dur"], start=st, scene_dur=sd))
        t = st + sd
    win = round(t, 2)
    cov = tts.coverage(sched, win)
    lo, hi = cfg["coverage"]["story"]
    print(f"🎙️ تغطية السرد: {cov}% (هدف {lo*100:.0f}-{hi*100:.0f}%) | المدة: {win}s")
    ass = captions.ass_doc(os.path.join(work, "manga.ass"), sched, 0.0)
    captions.card(os.path.join(work, "title.png"),
                  [(story["title"], "naskh", 150, 300, (255, 255, 255, 255), 6),
                   (story.get("subtitle", ""), "naskh", 56, 500, (230, 214, 160, 255), 3)], fp)
    captions.card(os.path.join(work, "end.png"),
                  [(story.get("endcard", "يتبع"), "naskh", 120, 430, (255, 255, 255, 255), 6),
                   (story.get("endcard2", ""), "naskh", 50, 600, (230, 214, 160, 255), 3)], fp)
    out = os.path.join(work, "manga_ep.mp4")
    render.render_manga_panels(ff, panels, sched, win, ass,
                               os.path.join(work, "title.png"), os.path.join(work, "end.png"), out)
    print("✅", out)

def cmd_queue(a, cfg):
    if a.act == "list":
        for i in q.list_items(cfg["_root"]):
            print(f"[{i['status']:>9}] {i['score']:>3} {i['title'][:50]}  {i['url']}")
    elif a.act == "next":
        print(json.dumps(q.next_item(cfg["_root"], cfg), ensure_ascii=False, indent=1))
    elif a.act == "mark":
        q.mark(cfg["_root"], a.video_id, a.status)
        print("✔️", a.video_id, "→", a.status)

def cmd_status(a, cfg):
    print("💾", storage.report(cfg["_root"], cfg["storage_budget_mb"]))
    db = q.list_items(cfg["_root"])
    print("📥 طابور:", {s: sum(1 for i in db if i["status"] == s)
                       for s in ("pending", "planned", "published", "skipped")})
    if a.clean:
        for p, sz in storage.clean(cfg["_root"]):
            print("🧹", p, sz)

def main(argv=None):
    ap = argparse.ArgumentParser(prog="vtsys")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("selftest"); p.set_defaults(fn=cmd_selftest)
    p = sub.add_parser("audit", help="preflight/postflight audit for a story package")
    p.add_argument("package"); p.add_argument("--rendered", action="store_true")
    p.set_defaults(fn=cmd_audit)
    p = sub.add_parser("audio-audit"); p.add_argument("files", nargs='+'); p.set_defaults(fn=cmd_audio_audit)
    p = sub.add_parser("script-audit"); p.add_argument("script"); p.add_argument("--max-words", type=int, default=38); p.set_defaults(fn=cmd_script_audit)
    p = sub.add_parser("visual-audit"); p.add_argument("files", nargs='+'); p.add_argument("--min-width", type=int, default=1280); p.add_argument("--min-height", type=int, default=720); p.set_defaults(fn=cmd_visual_audit)
    p = sub.add_parser("decide"); p.add_argument("url"); p.add_argument("--niche", nargs="*")
    p.add_argument("--out"); p.add_argument("--enqueue", action="store_true"); p.set_defaults(fn=cmd_decide)
    p = sub.add_parser("scan"); p.add_argument("--query", required=True); p.add_argument("--limit", type=int, default=6)
    p.add_argument("--niche", nargs="*"); p.add_argument("--enqueue", action="store_true"); p.set_defaults(fn=cmd_scan)
    p = sub.add_parser("short"); p.add_argument("url"); p.add_argument("--script"); p.add_argument("--start", type=float)
    p.add_argument("--out"); p.set_defaults(fn=cmd_short)
    p = sub.add_parser("doc"); p.add_argument("url"); p.add_argument("--window", nargs=2, type=float, required=True)
    p.add_argument("--narration", required=True); p.add_argument("--res", type=int, default=1080)
    p.add_argument("--out"); p.set_defaults(fn=cmd_doc)
    p = sub.add_parser("manga"); p.add_argument("--story", required=True); p.add_argument("--panels", required=True)
    p.add_argument("--out"); p.set_defaults(fn=cmd_manga)
    p = sub.add_parser("queue"); p.add_argument("act", choices=["list", "next", "mark"])
    p.add_argument("--video-id"); p.add_argument("--status"); p.set_defaults(fn=cmd_queue)
    p = sub.add_parser("status"); p.add_argument("--clean", action="store_true"); p.set_defaults(fn=cmd_status)
    a = ap.parse_args(argv)
    env.ensure_deps()
    a.fn(a, config.load())
