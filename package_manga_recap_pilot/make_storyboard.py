#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""بناء الستوري بورد الكامل قبل الإنتاج (§4.7).
الاستخدام: python3 package_manga_recap_pilot/make_storyboard.py
المخرجات: storyboard.json (للآلة — يقرأه البناء) + storyboard.md + storyboard.html (للبشر).
المسبح: 24 ربع sheet + 14 لوحة مفردة = 38 still مصنفة بشرياً.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from vtsys import env  # noqa: E402
from vtsys.tts import word_times  # noqa: E402
from vtsys.storyboard import split_beats, beat_times, resolve_regions, check_fixed  # noqa: E402
from vtsys.scenes import duration  # noqa: E402

PKG = os.path.dirname(os.path.abspath(__file__))
BEAT_SHEET = {"hook": 0, "hero": 1, "humiliation": 2, "awakening": 3,
              "power": 4, "cliffhanger": 5}
MOOD = {"hook": "تشويق", "hero": "دفء", "humiliation": "انكسار",
        "awakening": "رهبة", "power": "انفجار", "cliffhanger": "توتر"}

# ── الكتالوج البشري (38 still) ──
def _q(sh, rg, desc, type, max_uses, gap):
    return (f"sh{sh + 1}_{rg}", dict(desc=desc, type=type, max_uses=max_uses, gap=gap,
                                     kind="quad", sheet=sh, region=rg))

def _p(n, desc, type, max_uses, gap):
    return (f"p{n}", dict(desc=desc, type=type, max_uses=max_uses, gap=gap,
                          kind="panel", file=f"panels/p{n}.jpg"))

CATALOG = dict([
    _q(0, "q1", "البوابة الذهبية فجراً", "establishing", 3, 6),
    _q(0, "q2", "عينا كريم المشتعلتان", "reaction", 2, 6),
    _q(0, "q3", "شروق مدينة النحاس", "establishing", 3, 6),
    _q(0, "q4", "قاعة الامتحان", "establishing", 2, 8),
    _q(1, "q1", "زقاق النحاس صباحاً", "establishing", 2, 6),
    _q(1, "q2", "خطاب القبول بالختم", "detail", 1, 9999),
    _q(1, "q3", "يد المعلم على الكتف", "reaction", 2, 6),
    _q(1, "q4", "تدريب السيف وحيداً", "reaction", 2, 6),
    _q(2, "q1", "لحظة الهزيمة", "key_action", 1, 9999),
    _q(2, "q2", "ضحك الدفعة", "reaction", 3, 6),
    _q(2, "q3", "المعلم الصارم", "reaction", 2, 8),
    _q(2, "q4", "السيف المكسور", "detail", 1, 9999),
    _q(3, "q1", "مقبرة السيوف ليلاً", "establishing", 3, 6),
    _q(3, "q2", "السيف الأسود (الكشف)", "detail", 1, 9999),
    _q(3, "q3", "اليد تقترب", "key_action", 1, 9999),
    _q(3, "q4", "الظلال تلتف", "key_action", 1, 9999),
    _q(4, "q1", "القبضة على المقبض", "key_action", 1, 9999),
    _q(4, "q2", "انفجار الظل", "key_action", 1, 9999),
    _q(4, "q3", "تحطم الصخرة", "key_action", 1, 9999),
    _q(4, "q4", "وقفة النصر", "reaction", 3, 6),
    _q(5, "q1", "إعلان التحدي", "key_action", 1, 9999),
    _q(5, "q2", "ابتسامة كريم", "reaction", 2, 6),
    _q(5, "q3", "المواجهة", "key_action", 1, 9999),
    _q(5, "q4", "الجمهور الصاخب", "reaction", 4, 6),
    _p(1, "البوابة (لوحة)", "establishing", 2, 8),
    _p(2, "الزقاق (لوحة)", "establishing", 2, 8),
    _p(3, "الهزيمة (لوحة)", "key_action", 1, 9999),
    _p(4, "المقبرة (لوحة)", "establishing", 2, 8),
    _p(5, "الانفجار (لوحة)", "key_action", 1, 9999),
    _p(6, "النزال (لوحة)", "reaction", 2, 6),
    _p(7, "إزاي؟ (لوحة)", "reaction", 2, 6),
    _p(8, "المدينة (لوحة)", "establishing", 2, 8),
    _p(9, "الخطاب (لوحة)", "detail", 1, 9999),
    _p(10, "المعلم (لوحة)", "reaction", 2, 6),
    _p(11, "إلا واحد (لوحة)", "reaction", 2, 8),
    _p(12, "المقبض (لوحة)", "key_action", 1, 9999),
    _p(13, "التحدي (لوحة)", "key_action", 1, 9999),
    _p(14, "وكريم؟ (لوحة)", "reaction", 2, 6),
])

# مرشحو كل جملة: أرباع شيتها + لوحاتها المفردة
PANELS_OF = {0: ["p1", "p7", "p8"], 1: ["p7"], 2: ["p8"], 3: ["p2"], 4: ["p9"],
             5: ["p10"], 6: ["p3"], 7: ["p11"], 8: ["p4"], 9: ["p12"], 10: ["p5"],
             11: ["p13"], 12: ["p14"], 13: ["p6"], 14: ["p6"]}

ff = env.ensure_ffmpeg(ROOT)
units = json.load(open(os.path.join(PKG, "sentences.json"), encoding="utf-8"))["units"]
story = json.load(open(os.path.join(PKG, "story.json"), encoding="utf-8"))

print("🎙️ مدد الجُمل…")
sent_words, candidates = [], []
for si, u in enumerate(units):
    d = round(duration(ff, os.path.join(PKG, u["vo"])), 2)
    sent_words.append(word_times(u["text"], d))
    sh = BEAT_SHEET[u["beat"]] + 1
    candidates.append([f"sh{sh}_{r}" for r in ("q1", "q2", "q3", "q4")] + PANELS_OF[si])

beats = split_beats(sent_words)
starts = beat_times(beats)
print(f"   {len(beats)} beat / {sum(len(b['words']) for b in beats)} كلمة / {len(CATALOG)} still")

# تدقيق v3 الرجعي (تدوير أعمى على الأرباع)
v3_ids = [f"sh{BEAT_SHEET[units[b['sent']]['beat']] + 1}_{['q1', 'q2', 'q3', 'q4'][i % 4]}"
          for i, b in enumerate(beats)]
v3_viol = check_fixed(beats, v3_ids, CATALOG, starts)
print(f"🔍 تدقيق v3: {len(v3_viol)} مخالفة")

assign, viol = resolve_regions(beats, candidates, CATALOG, starts)
print(f"📋 توزيع v4: {len(viol)} مخالفة" + (" ✅" if not viol else " ⚠️"))
for v in viol:
    print(f"   beat{v['beat']}: {v['still']} — {v['reason']}")

shots = []
for i, (b, a) in enumerate(zip(beats, assign)):
    c = CATALOG[a["key"]]
    still = dict(kind=c["kind"])
    if c["kind"] == "quad":
        still.update(sheet=c["sheet"], region=c["region"])
        ref = f"sheets/sheet{c['sheet'] + 1}.jpg#{c['region']}"
    else:
        still.update(file=c["file"])
        ref = c["file"]
    shots.append(dict(
        id=f"SH{i + 1:02d}", sent=b["sent"] + 1, time=starts[i], dur=b["dur"],
        words=" ".join(w for w, _ in b["words"]), still=still, ref=ref,
        desc=c["desc"], type=c["type"], reusable=c["max_uses"] > 1,
        max_uses=c["max_uses"],
        camera="push-in + pan-" + ("right" if i % 2 == 0 else "left"),
        mood=MOOD[units[b["sent"]]["beat"]]))

board = dict(episode=f"{story['title']} / {story.get('part', '')}",
             status="مسودة — بانتظار الاعتماد البشري",
             policy="سقف استخدام + فجوة دنيا + لا تكرار داخل الجملة (§4.7)",
             stats=dict(shots=len(shots), stills=len(CATALOG),
                        unique=sum(1 for s in shots if not s["reusable"]),
                        v3_violations=len(v3_viol), v4_violations=len(viol)),
             v3_violations=v3_viol, shots=shots)
json.dump(board, open(os.path.join(PKG, "storyboard.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

L = [f"# 🎬 ستوري بورد — {board['episode']}",
     "", f"**الحالة:** {board['status']}",
     f"**السياسة:** {board['policy']}",
     f"**الإحصاء:** {board['stats']['shots']} لقطة · {board['stats']['stills']} still · "
     f"فريدة: {board['stats']['unique']} · مخالفات v3: {board['stats']['v3_violations']} · مخالفات v4: {board['stats']['v4_violations']}",
     "", "## ⚠️ تدقيق v3 الرجعي (لماذا نحتاج البورد)", ""]
L += [f"- beat{v['beat']} (ج{v['sent']}) `{v['still']}`: {v['reason']}" for v in v3_viol] or ["- لا مخالفات"]
L += ["", "## 🎞 اللقطات", ""]
cur = 0
for idx, s in enumerate(shots):
    if s["sent"] != cur:
        cur = s["sent"]
        L += [f"### الجملة {cur} [{units[cur - 1]['beat']}] — {units[cur - 1]['text']}", "",
              "| اللقطة | t | المدة | النوع | الصورة | الكاميرا | الكلمات |", "|---|---|---|---|---|---|---|"]
    badge = f"🔁×{s['max_uses']}" if s["reusable"] else "🔒 فريدة"
    L += [f"| {s['id']} | {s['time']}s | {s['dur']}s | {s['type']} {badge} | `{s['ref']}` {s['desc']} | {s['camera']} | {s['words']} |"]
    if idx == len(shots) - 1 or shots[idx + 1]["sent"] != cur:
        L += [""]
open(os.path.join(PKG, "storyboard.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

POS = {"q1": "3.7% 3.7%", "q2": "96.3% 3.7%", "q3": "3.7% 96.3%", "q4": "96.3% 96.3%"}
TC = {"establishing": "#7ec8e2", "reaction": "#a8e27e", "transition": "#d3c87e",
      "detail": "#e29c7e", "key_action": "#e27e7e"}
cards = []
for s in shots:
    badge = f"🔁 ×{s['max_uses']}" if s["reusable"] else "🔒 فريدة"
    st = s["still"]
    if st["kind"] == "quad":
        vis = (f"<div class=\"still\" style=\"background-image:url('sheets/sheet{st['sheet'] + 1}.jpg\");"
               f"background-size:217.4% 217.4%;background-position:{POS[st['region']]};\"></div>")
    else:
        vis = f"<img class=\"still\" src=\"{st['file']}\">"
    cards.append(
        f'<div class="card">{vis}<div class="meta"><div class="r1"><b>{s["id"]}</b>'
        f'<span class="t" style="color:{TC[s["type"]]}">{s["type"]}</span><span>{badge}</span></div>'
        f'<div class="r2">⏱ {s["time"]}s · {s["dur"]}s · 🎥 {s["camera"]} · {s["mood"]}</div>'
        f'<div class="r3">{s["desc"]}</div><div class="r4">{s["words"]}</div></div></div>')
html = f"""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>ستوري بورد — {board['episode']}</title>
<style>*{{box-sizing:border-box;margin:0;padding:0}}body{{background:#0b0b12;color:#f2f2f5;font-family:"Segoe UI",Tahoma,Arial,sans-serif}}
.wrap{{max-width:1100px;margin:0 auto;padding:24px 16px 64px}}h1{{color:#ffc93c;text-align:center}}
.sub{{text-align:center;color:#b9b9c7;margin:8px 0 4px}}.stats{{text-align:center;color:#e6d69c;margin-bottom:20px}}
.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}.card{{background:#14141c;border:1px solid #262633;border-radius:12px;overflow:hidden}}
.still{{width:100%;aspect-ratio:16/9;background-repeat:no-repeat;object-fit:cover;display:block}}.meta{{padding:10px 12px}}
.r1{{display:flex;gap:10px;align-items:center}}.r1 b{{color:#ffc93c}}.t{{font-size:.8rem}}
.r2{{color:#8a8a99;font-size:.8rem;margin:4px 0}}.r3{{color:#e6d69c;font-size:.9rem}}.r4{{color:#d7d7e0;line-height:1.9;font-size:.9rem;margin-top:4px}}
.viol{{background:#2a1414;border:1px solid #5a2626;border-radius:10px;padding:12px 14px;margin-bottom:16px;font-size:.85rem;line-height:2}}
.ok{{background:#142a1c;border:1px solid #265a35;border-radius:10px;padding:12px 14px;margin-bottom:16px;font-size:.9rem;text-align:center}}
@media(max-width:700px){{.grid{{grid-template-columns:1fr}}}}</style></head><body><div class="wrap">
<h1>🎬 ستوري بورد — {board['episode']}</h1><p class="sub">{board['status']} · {board['policy']}</p>
<p class="stats">{board['stats']['shots']} لقطة · {board['stats']['stills']} still · فريدة {board['stats']['unique']} · مخالفات v3: {board['stats']['v3_violations']} · v4: {board['stats']['v4_violations']}</p>
{('<div class="ok">✅ توزيع v4 نظيف — صفر مخالفات. جاهز للاعتماد والرندر.</div>' if not viol else '')}
{('<div class="viol">⚠️ <b>مخالفات v3 المكتشفة:</b><br>' + '<br>'.join(f"beat{v['beat']} (ج{v['sent']}) <code>{v['still']}</code>: {v['reason']}" for v in v3_viol) + '</div>') if v3_viol else ''}
<div class="grid">{''.join(cards)}</div></div></body></html>"""
open(os.path.join(PKG, "storyboard.html"), "w", encoding="utf-8").write(html)
print(f"✅ storyboard.json + storyboard.md + storyboard.html ({len(shots)} لقطة)")
