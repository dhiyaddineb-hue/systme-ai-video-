# -*- coding: utf-8 -*-
"""حارس التخزين (§7.5): ميزانية Workspace + تنظيف الوسائط."""
import os, subprocess

JUNK = ("seg/", "base_.mp4", "vfull", "afull", "clip.mp4", "clip60.mp4",
        "chk", "_small.jpg", "font_test", "cards_check", "contact")

def du_mb(root):
    r = subprocess.run(["du", "-sm", root], capture_output=True, text=True)
    return int(r.stdout.split()[0])

def report(root, budget_mb):
    used = du_mb(root)
    return dict(used_mb=used, budget_mb=budget_mb, ok=used <= budget_mb)

def clean(root, dry=False):
    removed = []
    for dirpath, dirnames, filenames in os.walk(root):
        if any(x in dirpath for x in (".git", "node_modules", "package_")):
            continue
        for f in filenames:
            p = os.path.join(dirpath, f)
            sz = os.path.getsize(p) / 1e6
            if sz > 15 and any(j in f for j in JUNK):
                removed.append((p, round(sz, 1)))
                if not dry:
                    os.remove(p)
        for d in list(dirnames):
            if d == "seg" and "package" not in dirpath:
                removed.append((os.path.join(dirpath, d), "dir"))
                if not dry:
                    subprocess.run(["rm", "-rf", os.path.join(dirpath, d)])
                dirnames.remove(d)
    return removed
