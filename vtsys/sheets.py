# -*- coding: utf-8 -*-
"""Six-panel sheets: 3 cols x 2 rows + no-repeat audit (4.11).
- SIXTHS: relative boxes in reading order (top row r0-r2, bottom row r3-r5).
- extract_sixths: crop 6 clean regions with gutter inset.
- audit_norepeat: every sentence owns a unique (sheet, region); fail = no render.
"""
import os
import subprocess

SIXTHS = [(c / 3.0, r / 2.0, 1 / 3.0, 1 / 2.0) for r in range(2) for c in range(3)]

# §4.12 FILM MODE — كل بانل يُقصّ لـ 6 قصّات سينمائية 16:9 (فريم بفريم كالفيلم):
# كل معنى (مقطع بين …) = لقطة بقصّة مختلفة وحركتها الخاصة. القطع كل ~2 ثانية.
FILM_SUBS = {
    "wide": "crop=iw:iw*9/16:x=(iw-ow)/2:y=(ih-oh)/2",
    "left": "crop=iw*0.66:iw*0.66*9/16:x=0:y=(ih-oh)/2",
    "right": "crop=iw*0.66:iw*0.66*9/16:x=iw-ow:y=(ih-oh)/2",
    "punch": "crop=iw*0.54:iw*0.54*9/16:x=(iw-ow)/2:y=(ih-oh)*0.38",
    "top": "crop=iw*0.72:iw*0.72*9/16:x=(iw-ow)/2:y=0",
    "low": "crop=iw*0.72:iw*0.72*9/16:x=(iw-ow)/2:y=ih-oh",
}
SUB_ORDER = ["wide", "left", "right", "punch", "top", "low"]


def extract_film_subs(ff, region_path, outdir, prefix):
    """قصّ بانل واحد إلى 6 لقطات سينمائية 16:9. يعيد {sub_name: path}."""
    import os
    import subprocess
    os.makedirs(outdir, exist_ok=True)
    out = {}
    for name in SUB_ORDER:
        o = os.path.join(outdir, "%s_%s.jpg" % (prefix, name))
        subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                        "-i", region_path, "-vf", FILM_SUBS[name], "-q:v", "2", o],
                       check=True, capture_output=True)
        out[name] = o
    return out


def audit_shots(stills):
    """كل لقطة ملف فريد عالمياً — أي تكرار بلا غرض يرفض الرندر."""
    seen = {}
    for i, p in enumerate(stills):
        if p in seen:
            raise SystemExit("NO-REPEAT VIOLATION: shots %d and %d share %s"
                             % (seen[p], i, p))
        seen[p] = i
    return True


def extract_sixths(ff, sheet, outdir, prefix, inset=0.012):
    os.makedirs(outdir, exist_ok=True)
    paths = []
    for i, (x, y, w, h) in enumerate(SIXTHS):
        x2, y2, w2, h2 = x + inset, y + inset, w - 2 * inset, h - 2 * inset
        vf = "crop=in_w*%f:in_h*%f:in_w*%f:in_h*%f" % (w2, h2, x2, y2)
        o = os.path.join(outdir, "%s_r%d.jpg" % (prefix, i))
        subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y",
                        "-i", sheet, "-vf", vf, "-q:v", "2", o],
                       check=True, capture_output=True)
        paths.append(o)
    return paths


def audit_norepeat(mapping):
    seen = {}
    for sid, (sh, rg) in mapping.items():
        if (sh, rg) in seen:
            raise SystemExit("NO-REPEAT VIOLATION: sentences %s and %s share %s#region%d"
                             % (seen[(sh, rg)], sid, sh, rg))
    return True
