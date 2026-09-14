"""تحويل ترجمة يوتيوب json3 → نص + مقاطع بتوقيتات"""
import json, re, sys, os

def load_json3(path):
    d = json.load(open(path, encoding="utf-8"))
    out = []
    for ev in d.get("events", []):
        segs = ev.get("segs") or []
        txt = "".join(s.get("utf8","") for s in segs).strip()
        if not txt or txt == "\n": continue
        t0 = (ev.get("tStartMs") or 0)/1000.0
        out.append({"t": round(t0,2), "text": re.sub(r"\s+"," ",txt)})
    # دمج الأسطر المتكررة/المتتالية
    merged=[]
    for it in out:
        if merged and merged[-1]["text"]==it["text"]: continue
        merged.append(it)
    return merged

def fmt_ts(s):
    m, sec = divmod(int(s), 60); h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"

if __name__ == "__main__":
    f = sys.argv[1]
    segs = load_json3(f)
    full = " ".join(s["text"] for s in segs)
    os.makedirs("vt/demo", exist_ok=True)
    json.dump(segs, open("vt/demo/transcript.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
    open("vt/demo/transcript.txt","w",encoding="utf-8").write(full)
    print("segments:", len(segs), "| words:", len(full.split()), "| chars:", len(full))
    print("="*70)
    print("أول 90 ثانية:")
    for s in segs:
        if s["t"] > 90: break
        print(f"  [{fmt_ts(s['t'])}] {s['text']}")
    print("="*70)
    print("عينات من منتصف الفيديو:")
    mid = len(segs)//2
    for s in segs[mid:mid+12]:
        print(f"  [{fmt_ts(s['t'])}] {s['text']}")
