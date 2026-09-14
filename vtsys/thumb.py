# -*- coding: utf-8 -*-
"""بانر الشورت + نصوص الثامبنيل (§2/§6)."""
from .textutil import ar_text

def banner_short(path, l1, src_ar, src_lat, fonts, w=1080, h=300):
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle([36, 26, w-36, h-26], radius=40, fill=(8, 8, 16, 210))
    d.rounded_rectangle([36, 26, w-36, h-26], radius=40, outline=(255, 201, 60, 255), width=5)
    def fit(text, fp, start, minsize, maxw):
        size = start
        while size > minsize:
            f = ImageFont.truetype(fp, size)
            if d.textlength(text, font=f) <= maxw:
                return f
            size -= 2
        return ImageFont.truetype(fp, minsize)
    t1 = ar_text(l1); f1 = fit(t1, fonts["sans"], 62, 34, 940)
    d.text(((w - d.textlength(t1, font=f1)) / 2, 58), t1, font=f1, fill=(255, 255, 255, 255))
    ap = ar_text(src_ar); fa = ImageFont.truetype(fonts["sans"], 36)
    fl = ImageFont.truetype(fonts["latin"], 36)
    wa, wl, gap = d.textlength(ap, font=fa), d.textlength(src_lat, font=fl), 14
    x0 = (w - (wa + wl + gap)) / 2
    d.text((x0 + wl + gap, 192), ap, font=fa, fill=(255, 201, 60, 255))
    d.text((x0, 192), src_lat, font=fl, fill=(255, 201, 60, 255))
    img.save(path)
    return path

def thumb_text(src_img, out, lines, fonts, chip=None, dim_top=0.34, dim_bot=0.0):
    from PIL import Image, ImageDraw, ImageFont, ImageEnhance
    im = Image.open(src_img).convert("RGB")
    im = ImageEnhance.Contrast(im).enhance(1.08)
    W, H = im.size
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    if dim_top:
        od.rectangle([0, 0, W, int(H * dim_top)], fill=(0, 0, 0, 155))
    if dim_bot:
        od.rectangle([0, int(H * (1 - dim_bot)), W, H], fill=(0, 0, 0, 150))
    im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(im)
    for text, key, size, y, fill in lines:
        f = ImageFont.truetype(fonts[key], size)
        t = ar_text(text); w = d.textlength(t, font=f)
        d.text(((W - w) / 2, y), t, font=f, fill=fill, stroke_width=6, stroke_fill=(0, 0, 0))
    if chip:
        f = ImageFont.truetype(fonts["sans"], 52)
        t = ar_text(chip); w = d.textlength(t, font=f)
        d.rounded_rectangle([(W-w)/2-40, H-170, (W+w)/2+40, H-80], radius=45, fill=(255, 201, 60, 255))
        d.text(((W - w) / 2, H - 162), t, font=f, fill=(15, 15, 20))
    im.save(out)
    return out
