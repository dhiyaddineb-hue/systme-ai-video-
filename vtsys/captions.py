# -*- coding: utf-8 -*-
"""سبتايتل ASS + بطاقات PNG (§3.3/§6)."""
from .textutil import ar_text, ar_shaped_for_ass

def _ts(x):
    x = max(0.0, x)
    return f"{int(x//3600)}:{int(x%3600//60):02d}:{x%60:05.2f}"

HDR = ("[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\nWrapStyle: 0\n"
       "ScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
       "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
       "{styles}\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

STYLE_SHORT = ("Style: Cap,Noto Sans Arabic,62,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,4,2,2,60,60,290,1\n"
               "Style: Tag,Noto Sans Arabic,46,&H0000E5FF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,1,0,3,3,1,2,60,60,470,1")
STYLE_DOC = ("Style: Doc,Noto Naskh Arabic,{size},&H00F0F0F0,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,1.5,0,1,2,1,2,140,140,{mv},1")

TAGS = {"hook": "— الهوك —", "summary": "— القصة —", "insight": "— الفكرة —",
        "opinion": "— رأيي —", "detail": "— لقطة مهمة —", "cta": "— الخلاصة —"}

def ass_short(path, segs, times):
    ev = []
    for s, (a, b) in zip(segs, times):
        ev.append(f"Dialogue: 0,{_ts(a)},{_ts(b)},Cap,,0,0,0,,{ar_shaped_for_ass(s['text'])}")
        ev.append(f"Dialogue: 1,{_ts(a)},{_ts(min(a+2.4, b))},Tag,,0,0,0,,{ar_shaped_for_ass(TAGS.get(s.get('type',''), '—'))}")
    open(path, "w", encoding="utf-8").write(
        HDR.format(W=1080, H=1920, styles=STYLE_SHORT) + "\n".join(ev) + "\n")
    return path

def ass_doc(path, sched, w0=0.0, size=50, margin_v=34):
    ev = [f"Dialogue: 0,{_ts(s['start']-w0)},{_ts(s['start']+s['dur_narr']-w0)},Doc,,0,0,0,,{ar_shaped_for_ass(s['text'])}"
          for s in sched]
    open(path, "w", encoding="utf-8").write(
        HDR.format(W=1920, H=1080, styles=STYLE_DOC.format(size=size, mv=margin_v))
        + "\n".join(ev) + "\n")
    return path

def card(path, specs, font_paths, w=1920, h=1080):
    """specs: [(text, font_key, size, y, fill, stroke_width)]"""
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for text, key, size, y, fill, sw in specs:
        f = ImageFont.truetype(font_paths[key], size)
        t = ar_text(text); tw = d.textlength(t, font=f)
        d.text(((w - tw) / 2, y), t, font=f, fill=fill,
               stroke_width=sw, stroke_fill=(0, 0, 0, 220))
    img.save(path)
    return path
