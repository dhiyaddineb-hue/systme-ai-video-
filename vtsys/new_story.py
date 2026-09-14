#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story scaffolder (4.11): every story lives in its own folder.
Usage: python3 vtsys/new_story.py <package_dir> "<arabic title>"
Creates: story.json, sentences.json, identity.json, SHEETS.md, README.md, build.py
Then fill the JSONs (script + cast + panels) and run <package>/build.py.
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(pkgdir, title):
    os.makedirs(pkgdir, exist_ok=True)
    slug = os.path.basename(os.path.abspath(pkgdir)).replace("package_", "")
    story = {"slug": slug, "title": title, "subtitle": "", "part": "الحلقة الأولى",
             "endcard": "يتبع", "endcard2": "",
             "out": slug + "_ep1_v1.mp4", "ass": "manga_" + slug + "_v1.ass"}
    with open(os.path.join(pkgdir, "story.json"), "w", encoding="utf-8") as f:
        json.dump(story, f, ensure_ascii=False, indent=2)
    skel = {"_note": "وحدات السرد: id/text/vo/beat + sheet/region (بانل فريد لكل جملة).",
            "gap": 0.4, "units": []}
    with open(os.path.join(pkgdir, "sentences.json"), "w", encoding="utf-8") as f:
        json.dump(skel, f, ensure_ascii=False, indent=2)
    ident = {"_note": "ميثاق الهوية (§4.10): characters + style_lock + face_ref + scenes.",
             "style_lock": "", "characters": {}, "face_ref": "", "scenes": {}}
    with open(os.path.join(pkgdir, "identity.json"), "w", encoding="utf-8") as f:
        json.dump(ident, f, ensure_ascii=False, indent=2)
    with open(os.path.join(pkgdir, "SHEETS.md"), "w", encoding="utf-8") as f:
        f.write("# شيتات %s (6 بانل 3×2 لكل شيت)\n\n| الشيت | البانلات | الجُمل |\n|---|---|---|\n" % title)
    with open(os.path.join(pkgdir, "README.md"), "w", encoding="utf-8") as f:
        f.write("# %s\n\nقصة منظمة في مجلد خاص (§4.11).\n" % title)
    shutil.copy(os.path.join(ROOT, "vtsys", "_sheet6_build_template.py"),
                os.path.join(pkgdir, "build.py"))
    print("STORY SCAFFOLD OK:", pkgdir)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
