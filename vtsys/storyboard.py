# -*- coding: utf-8 -*-
"""ما قبل الإنتاج (§4.7): سياسة إعادة المشاهد + تقسيم beats + فحص الالتزام.
القاعدة: لا رندر بدون storyboard معتمد يجتاز التدقيق.
الـ stills: أرباع sheets ("sh1_q1") أو لوحات مفردة ("p7") — مسبح موحد.
"""
BEAT_MIN, GAP_SENT, LEAD = 1.8, 0.4, 2.0

SHOT_TYPES = {
    "establishing": {"ar": "تأسيسي", "reusable": True},
    "reaction": {"ar": "انفعالي", "reusable": True},
    "transition": {"ar": "انتقالي", "reusable": True},
    "detail": {"ar": "تفصيلي", "reusable": False},
    "key_action": {"ar": "حدث مفصلي", "reusable": False},
}

def split_beats(sent_words):
    """تقسيم كلمات الجُمل إلى beats بصرية (مصدر وحيد — يستخدمه البناء والبورد).
    sent_words: [[(word,dur),...], ...] → [{sent, words, dur}] (الأخير +GAP_SENT)."""
    beats = []
    for si, words in enumerate(sent_words):
        acc, accw = 0.0, []
        for w, d in words:
            acc += d
            accw.append((w, d))
            if acc >= BEAT_MIN:
                beats.append(dict(sent=si, words=list(accw), dur=round(acc, 2)))
                acc, accw = 0.0, []
        if acc > 0.01:
            beats.append(dict(sent=si, words=list(accw), dur=round(acc, 2)))
        beats[-1]["dur"] = round(beats[-1]["dur"] + GAP_SENT, 2)
    return beats

def beat_times(beats, lead=LEAD):
    t, out = lead, []
    for b in beats:
        out.append(round(t, 2))
        t += b["dur"]
    return out

def resolve_regions(beats, candidates, catalog, starts):
    """توزيع جشع يحترم: التفرد + الفجوات + السقوف + لا تكرار داخل الجملة.
    candidates: [sent_idx] → [still-ids] · catalog: {still-id: {type,max_uses,gap,desc}}."""
    assign, viol, last_use, uses = [], [], {}, {}
    for i, b in enumerate(beats):
        cands = []
        for sid in candidates[b["sent"]]:
            c = catalog[sid]
            u = uses.get(sid, 0)
            ok = u < c["max_uses"] and (sid not in last_use or starts[i] - last_use[sid] >= c["gap"])
            same_sent = any(a["sent"] == b["sent"] and a["key"] == sid for a in assign)
            cands.append(((0 if ok else 2) + (1 if same_sent else 0) + u * 0.1, sid, ok))
        cands.sort(key=lambda x: (x[0], x[1]))
        sid = cands[0][1]
        if not cands[0][2]:
            viol.append(dict(beat=i + 1, sent=b["sent"] + 1, still=sid,
                             reason="تجاوز سقف/فجوة — لا بديل متاح"))
        assign.append(dict(sent=b["sent"], key=sid))
        last_use[sid] = starts[i]
        uses[sid] = uses.get(sid, 0) + 1
    return assign, viol

def check_fixed(beats, still_ids, catalog, starts):
    """تدقيق توزيع قائم (مثل v3) ضد السياسة — يعيد المخالفات."""
    viol, last_use, uses = [], {}, {}
    for i, b in enumerate(beats):
        sid = still_ids[i]
        c = catalog[sid]
        u = uses.get(sid, 0)
        if u >= c["max_uses"]:
            viol.append(dict(beat=i + 1, sent=b["sent"] + 1, still=sid,
                             reason=f"تكرار ممنوع/فوق السقف ({c['type']})"))
        elif sid in last_use and starts[i] - last_use[sid] < c["gap"]:
            viol.append(dict(beat=i + 1, sent=b["sent"] + 1, still=sid,
                             reason=f"فجوة {round(starts[i] - last_use[sid], 1)}s < {c['gap']}s"))
        last_use[sid] = starts[i]
        uses[sid] = u + 1
    return viol
