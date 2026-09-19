# -*- coding: utf-8 -*-
"""Production-package audit gates.

The renderer checks its own invariants while running; this module provides a
repeatable preflight/postflight check that can be run after a recycled
workspace or before publishing a package.
"""
import json
import os
from pathlib import Path


def audit_package(package, rendered=False):
    pkg = Path(package).resolve()
    errors, warnings = [], []

    def need(path, label):
        if not path.exists():
            errors.append(f"missing {label}: {path.relative_to(pkg)}")

    for name in ("story.json", "sentences.json", "identity.json"):
        need(pkg / name, name)
    if errors:
        return {"package": str(pkg), "status": "FAIL", "errors": errors, "warnings": warnings}

    try:
        story = json.loads((pkg / "story.json").read_text(encoding="utf-8"))
        data = json.loads((pkg / "sentences.json").read_text(encoding="utf-8"))
        units = data.get("units", [])
    except Exception as exc:
        return {"package": str(pkg), "status": "FAIL", "errors": [f"invalid JSON: {exc}"], "warnings": warnings}

    if not units:
        errors.append("sentences.json has no units")
    ids = [u.get("id") for u in units]
    if len(ids) != len(set(ids)):
        errors.append("duplicate sentence ids")
    panels = [(u.get("sheet"), u.get("region")) for u in units]
    if len(panels) != len(set(panels)):
        errors.append("repeated sheet/region: no-repeat gate failed")

    sheets = sorted({u.get("sheet") for u in units})
    for sheet in sheets:
        need(pkg / "sheets" / f"{sheet}.jpg", f"sheet {sheet}")
    for u in units:
        vo = pkg / u.get("vo", "")
        need(vo, f"VO sentence {u.get('id')}")

    board = pkg / "storyboard.json"
    if rendered:
        need(board, "storyboard.json")
        out = story.get("out_film", story.get("out"))
        need(pkg / out, "rendered video")
        if board.exists():
            try:
                b = json.loads(board.read_text(encoding="utf-8"))
                shots = b.get("shots", [])
                if not shots:
                    errors.append("storyboard has no shots")
                if "PASS" not in b.get("status", ""):
                    warnings.append("storyboard status does not mention PASS")
            except Exception as exc:
                errors.append(f"invalid storyboard.json: {exc}")

    # A story must have one visual owner for every narrated sentence.
    if units and len(panels) == len(set(panels)):
        warnings.append(f"{len(units)} sentences mapped to {len(panels)} unique panels")
    status = "FAIL" if errors else "PASS"
    return {"package": str(pkg), "status": status, "sentences": len(units),
            "sheets": len(sheets), "errors": errors, "warnings": warnings}
