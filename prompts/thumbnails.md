# 🖼️ برومبتات الثامبنيل

## ج.2 ثامبنيل الشورت (توليد ثم نص Pillow فوقه)

```
Vertical 9:16 YouTube Shorts / TikTok thumbnail, bold high-contrast design. A young Arab man in casual hoodie sitting with headphones, looking amazed at an open glowing storybook, magical golden light and sparkles rising from the book pages. Background: dark deep blue-purple gradient with soft bokeh. Large empty space at the top third for text overlay. Cinematic lighting, vibrant saturated colors, dramatic rim light, photorealistic illustration style, clean composition, no text, no letters, no watermark.
```

النص يُرسم فوقه عبر `vtsys/thumb.py` (خط NotoSansArabic-Bold).

## ج.3 قاعدة الثامبنيل الوثائقي

لا تولّد: خذ إطاراً حقيقياً 1080p من اللحظة الأيقونية ← `Contrast+1.08, Color+1.15` ← تعتيم علوي/سفلي ← نص Naskh: سطرا hook (أبيض/أصفر) + شارة chip سفلية.

راجع `vtsys/thumb.py::thumb_text`.
