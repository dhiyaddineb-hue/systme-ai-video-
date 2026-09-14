# -*- coding: utf-8 -*-
"""نص عربي محمول (§6): Pillow مع raqm ⇒ خام؛ وإلا reshape+bidi."""
from functools import lru_cache

@lru_cache(maxsize=1)
def _raqm():
    try:
        from PIL import features
        return bool(features.check("raqm"))
    except Exception:
        return False

def ar_text(s: str) -> str:
    if _raqm():
        return s
    import arabic_reshaper as ar
    from bidi.algorithm import get_display
    return get_display(ar.reshape(s))

def ar_shaped_for_ass(s: str) -> str:
    """لـ libass: ملفّاتنا المُختبرة تمرّر نصاً مشكّلاً بترتيب بصري."""
    import arabic_reshaper as ar
    from bidi.algorithm import get_display
    return get_display(ar.reshape(s))
