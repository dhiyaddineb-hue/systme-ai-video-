# -*- coding: utf-8 -*-
"""Face-lock reference system (4.10).
Bible: package_manga_recap_pilot/identity.json (single source of truth).
- build_prompt: locked prompt (characters + shot + style), no hand writing.
- refs_for: reference paths (full ref + face crop for close-ups).
- extract_face_ref: crop face ref from full ref via ffmpeg (no PIL).
- audit: existence gate + dhash fingerprint per hero (drift advisory).
CLI:
  python3 vtsys/identity.py prompts <PKG> s06 s07 ...
  python3 vtsys/identity.py face <PKG>
  python3 vtsys/identity.py audit <PKG>
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _ff():
    from vtsys import env
    return env.ensure_ffmpeg(ROOT)


def load_bible(pkg):
    with open(os.path.join(pkg, "identity.json"), encoding="utf-8") as f:
        return json.load(f)


def build_prompt(bible, scene_id):
    sc = bible["scenes"][scene_id]
    parts = []
    for c in sc["chars"]:
        parts.append(c.upper() + " (" + bible["characters"][c]["lock"] + ")")
    head = "Same characters as reference - " + " + ".join(parts) + ": "
    return head + sc["shot"] + ", " + bible["style_lock"]


def refs_for(bible, scene_id, pkg):
    out = []
    for c in bible["scenes"][scene_id]["chars"]:
        for r in bible["characters"][c]["refs"]:
            out.append(os.path.join(pkg, r))
    if bible["scenes"][scene_id].get("face"):
        out.append(os.path.join(pkg, bible["face_ref"]))
    ded = []
    for p in out:
        if p not in ded:
            ded.append(p)
    return ded


def extract_face_ref(pkg, box=(0.42, 0.05, 0.26, 0.50)):
    bible = load_bible(pkg)
    src = os.path.join(pkg, bible["characters"]["karim"]["refs"][0])
    out = os.path.join(pkg, bible["face_ref"])
    x, y, w, h = box
    vf = "crop=in_w*%s:in_h*%s:in_w*%s:in_h*%s" % (w, h, x, y)
    subprocess.run([_ff(), "-hide_banner", "-loglevel", "error", "-y",
                    "-i", src, "-vf", vf, "-q:v", "2", out],
                   check=True, capture_output=True)
    return out


def dhash(path, n=8):
    r = subprocess.run([_ff(), "-hide_banner", "-loglevel", "error",
                        "-i", path, "-vf", "scale=%d:%d,format=gray" % (n + 1, n),
                        "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                       check=True, capture_output=True)
    px = list(r.stdout)
    bits = 0
    for yy in range(n):
        for xx in range(n):
            left = px[yy * (n + 1) + xx]
            right = px[yy * (n + 1) + xx + 1]
            bits = (bits << 1) | (1 if left > right else 0)
    return bits


def ham(a, b):
    return bin(a ^ b).count("1")


def dims_of(path):
    r = subprocess.run([_ff(), "-hide_banner", "-i", path],
                       capture_output=True, text=True)
    m = re.search(r"Video:.*?\b(\d{3,5})x(\d{3,5})\b", r.stderr)
    return (m.group(1) + "x" + m.group(2)) if m else "?"


def audit(pkg):
    bible = load_bible(pkg)
    ref = dhash(os.path.join(pkg, bible["characters"]["karim"]["refs"][0]))
    print("%-6s %9s  %-11s  %12s  status" % ("scene", "bytes", "size", "dhash-vs-ref"))
    bad = []
    for sid in sorted(bible["scenes"]):
        p = os.path.join(pkg, "panels_v6", sid + ".jpg")
        if not os.path.exists(p):
            print("%-6s %9s  %-11s  %12s  MISSING" % (sid, "-", "-", "-"))
            bad.append(sid)
            continue
        d = ham(ref, dhash(p))
        flag = "DRIFT?" if d > 45 else "ok"
        if d > 45:
            bad.append(sid + "(drift)")
        print("%-6s %9d  %-11s  %12d  %s" % (sid, os.path.getsize(p), dims_of(p), d, flag))
    return bad


if __name__ == "__main__":
    cmd = sys.argv[1]
    pkgdir = sys.argv[2]
    bb = load_bible(pkgdir)
    if cmd == "prompts":
        for sid in sys.argv[3:]:
            print("===== " + sid + " =====")
            print(build_prompt(bb, sid))
            print("REFS: " + " | ".join(refs_for(bb, sid, pkgdir)))
    elif cmd == "face":
        print(extract_face_ref(pkgdir))
    elif cmd == "audit":
        res = audit(pkgdir)
        print("RESULT:", "CLEAN" if not res else res)
