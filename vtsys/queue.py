# -*- coding: utf-8 -*-
"""طابور النشر البشري (§1.4): حصص + فواصل gauss + ساعات نشاط + منع تكرار."""
import json, os, random, datetime

DB = "queue.json"

def _load(root):
    p = os.path.join(root, DB)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"items": []}

def _save(root, db):
    json.dump(db, open(os.path.join(root, DB), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

def add(root, video_id, url, title, score, verdict):
    db = _load(root)
    if any(i["video_id"] == video_id for i in db["items"]):
        return False
    db["items"].append(dict(video_id=video_id, url=url, title=title, score=score,
                            verdict=verdict, added=_now(), status="pending", planned=None))
    _save(root, db)
    return True

def _now():
    return datetime.datetime.now().isoformat(timespec="seconds")

def _in_hours(dt, hours):
    return hours[0] <= dt.hour < hours[1]

def next_item(root, cfg):
    db = _load(root)
    today = datetime.date.today().isoformat()
    done_today = sum(1 for i in db["items"]
                     if i["status"] == "published" and (i.get("published_at") or "").startswith(today))
    if done_today >= cfg["quota_per_day"]:
        return {"error": f"الحصة اليومية وصلت ({cfg['quota_per_day']})"}
    pend = [i for i in db["items"] if i["status"] == "pending"]
    if not pend:
        return {"error": "الطابور فاضي"}
    it = max(pend, key=lambda i: i["score"])
    dt = datetime.datetime.now() + datetime.timedelta(
        minutes=max(5, random.gauss(sum(cfg["gap_minutes"]) / 2, 12)))
    while not _in_hours(dt, cfg["active_hours"]):
        dt += datetime.timedelta(minutes=15)
    it["status"] = "planned"; it["planned"] = dt.isoformat(timespec="seconds")
    _save(root, db)
    return it

def mark(root, video_id, status):
    db = _load(root)
    for i in db["items"]:
        if i["video_id"] == video_id:
            i["status"] = status
            if status == "published":
                i["published_at"] = _now()
    _save(root, db)

def list_items(root):
    return _load(root)["items"]
