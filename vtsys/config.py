# -*- coding: utf-8 -*-
"""إعدادات النظام: افتراضات + config.json اختياري في جذر العمل."""
import json, os

DEFAULTS = {
    "threshold": 70,
    "niche": [],
    "voices": {"gulf": "ar-KW-FahedNeural", "doc": "ar-SY-LaithNeural",
              "recap": "ar-EG-ShakirNeural"},
    "tts": {"gulf": {"rate": "-4%"}, "doc": {"rate": "-8%", "pitch": "-4Hz"},
            "recap": {"rate": "+2%"}},
    "quota_per_day": 5,
    "gap_minutes": [40, 90],
    "active_hours": [16, 24],          # بتوقيت الجهاز — جمهور خليجي افتراضاً
    "coverage": {"doc": [0.40, 0.60], "story": [0.60, 0.75]},
    "storage_budget_mb": 110,
    "max_deliverable_mb": 30,
    "fonts": {"sans": "assets/fonts/NotoSansArabic-Bold.ttf",
              "naskh": "assets/fonts/NotoNaskhArabic.ttf",
              "latin": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"},
}

def load(root=None):
    root = root or os.getcwd()
    cfg = json.loads(json.dumps(DEFAULTS))
    p = os.path.join(root, "config.json")
    if os.path.exists(p):
        u = json.load(open(p, encoding="utf-8"))
        for k, v in u.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    cfg["_root"] = root
    return cfg
