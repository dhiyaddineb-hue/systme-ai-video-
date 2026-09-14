"""محرّك القرار: يحسب هل يستاهل أعلّق على هذا الفيديو الحين؟"""
import json, datetime, math, sys

def hours_since(upload_date: str) -> float:
    d = datetime.datetime.strptime(upload_date, "%Y%m%d").replace(tzinfo=datetime.timezone.utc)
    return (datetime.datetime.now(datetime.timezone.utc) - d).total_seconds() / 3600

def score_video(m: dict, niche_keywords=()) -> dict:
    age_h   = hours_since(m["upload_date"])
    views   = m.get("view_count") or 0
    likes   = m.get("like_count") or 0
    comments= m.get("comment_count") or 0
    dur     = m.get("duration") or 1

    velocity = views / max(age_h, 1)                    # مشاهدة/ساعة
    conv_r   = comments / max(views, 1)                 # نسبة المحادثة
    eng_r    = likes / max(views, 1)                    # نسبة الإعجاب

    # 1) العمر: الأفضل ≤ 6 ساعات (تعليق مبكر = ظهور أعلى)
    s_age = 30 if age_h <= 6 else 24 if age_h <= 24 else 16 if age_h <= 72 else 8 if age_h <= 168 else 3 if age_h <= 720 else 0
    # 2) سرعة النمو (لوغاريتمي حتى ما يسيطر عليه رقم واحد)
    s_vel = max(0, min(25, round(25 * (math.log10(velocity + 1) / math.log10(20000)))))
    # 3) المحادثة شغّالة؟
    s_conv = max(0, min(20, round(conv_r * 2500)))
    # 4) التفاعل
    s_eng = max(0, min(15, round(eng_r * 400)))
    # 5) ملاءمة النيش
    hay = " ".join([m.get("title",""), " ".join(m.get("tags") or []), " ".join(m.get("categories") or [])]).lower()
    hits = [k for k in niche_keywords if k.lower() in hay]
    s_niche = min(10, len(hits) * 5)

    total = s_age + s_vel + s_conv + s_eng + s_niche
    verdict = "انشر الحين 🔥" if total >= 70 else "مناسب، بس مو أولوية 🟡" if total >= 50 else "تجاوزه ❌"
    return dict(age_hours=round(age_h,1), views=views, likes=likes, comments=comments,
                duration_min=round(dur/60,1), velocity_per_hour=round(velocity),
                conversation_ratio=round(conv_r*100,3), engagement_ratio=round(eng_r*100,2),
                scores=dict(age=s_age, velocity=s_vel, conversation=s_conv, engagement=s_eng, niche=s_niche),
                total=total, threshold=70, verdict=verdict, niche_hits=hits)

if __name__ == "__main__":
    meta = json.load(open(sys.argv[1]))
    niche = sys.argv[2].split(",") if len(sys.argv) > 2 else []
    print(json.dumps(score_video(meta, niche), ensure_ascii=False, indent=2))
