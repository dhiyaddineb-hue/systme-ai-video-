# -*- coding: utf-8 -*-
"""Six-panel sheets: 3 cols x 2 rows + no-repeat audit (4.11).
- SIXTHS: relative boxes in reading order (top row r0-r2, bottom row r3-r5).
- extract_sixths: crop 6 clean regions with gutter inset.
- audit_norepeat: every sentence owns a unique (sheet, region); fail = no render.
"""
import os
import subprocess

SIXTHS = [(c / 3.0, r / 2.0, 1 / 3.0, 1 / 2.0) for r in range(2) for c in range(3)]


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
