# -*- coding: utf-8 -*-
"""محرّك القرار (§1): هل أعلّق الحين؟ نقاط 0-100، حد افتراضي 70."""
import datetime, math

def hours_since(upload_date: str) -> float:
    d = datetime.datetime.strptime(upload_date, "%Y%m%d").replace(tzinfo=datetime.timezone.utc)
    return (datetime.datetime.now(datetime.timezone.utc) - d).total_seconds() / 3600

def score(meta: dict, niche=(), threshold=70) -> dict:
    age_h = hours_since(meta["upload_date"])
    views = meta.get("view_count") or 0
    likes = meta.get("like_count") or 0
    comments = meta.get("comment_count") or 0
    velocity = views / max(age_h, 1)
    conv_r = comments / max(views, 1)
    eng_r = likes / max(views, 1)

    s_age = 30 if age_h <= 6 else 24 if age_h <= 24 else 16 if age_h <= 72 \
        else 8 if age_h <= 168 else 3 if age_h <= 720 else 0
    s_vel = max(0, min(25, round(25 * (math.log10(velocity + 1) / math.log10(20000)))))
    s_conv = max(0, min(20, round(conv_r * 2500)))
    s_eng = max(0, min(15, round(eng_r * 400)))
    hay = " ".join([meta.get("title", ""), " ".join(meta.get("tags") or []),
                    " ".join(meta.get("categories") or [])]).lower()
    hits = [k for k in niche if k.lower() in hay]
    s_niche = min(10, len(hits) * 5)

    total = s_age + s_vel + s_conv + s_eng + s_niche
    verdict = ("انشر الحين 🔥" if total >= threshold
               else "مناسب، بس مو أولوية 🟡" if total >= threshold - 20 else "تجاوزه ❌")
    # فيديو صامت؟ (لا ترجمة ولا تلقائية) ⇒ مرشّح للخط الوثائقي
    silent = not (meta.get("subtitles") or meta.get("automatic_captions"))
    return dict(age_hours=round(age_h, 1), views=views, velocity_per_hour=round(velocity),
                conversation_ratio=round(conv_r * 100, 3), engagement_ratio=round(eng_r * 100, 2),
                scores=dict(age=s_age, velocity=s_vel, conversation=s_conv,
                            engagement=s_eng, niche=s_niche),
                total=total, threshold=threshold, verdict=verdict,
                niche_hits=hits, silent_candidate=silent)
