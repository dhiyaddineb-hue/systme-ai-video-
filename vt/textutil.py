# -*- coding: utf-8 -*-
"""
معالجة نص عربي محمولة عبر البيئات:
  - إذا كان Pillow مبنياً مع raqm (HarfBuzz/FriBidi داخلياً): مرّر النص الخام كما هو.
  - وإلا: شكّل يدوياً عبر arabic_reshaper + python-bidi.
استدعِ ar_text() دائماً قبل الرسم بـ Pillow، ولا تستخدمها لنصوص libass/ASS
(llibass يشكّل بنفسه عبر HarfBuzz — لكن ملفنا الحالي يبني الأحداث بنص مشكّل
مسبقاً لأنه اختُبر بنجاح؛ للأنظمة الجديدة فضّل الخام مع libass أيضاً).
"""
from functools import lru_cache

@lru_cache(maxsize=1)
def _have_raqm() -> bool:
    try:
        from PIL import features
        return bool(features.check("raqm"))
    except Exception:
        return False

def ar_text(s: str) -> str:
    if _have_raqm():
        return s
    import arabic_reshaper as ar
    from bidi.algorithm import get_display
    return get_display(ar.reshape(s))
