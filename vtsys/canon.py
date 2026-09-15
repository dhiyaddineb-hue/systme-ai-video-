# -*- coding: utf-8 -*-
"""Continuity engine: canon registry + scene contracts + validation (5.0).
Implements docs/CONTINUITY_SYSTEM_SPEC.md (core runnable subset):
  36 validator, 35 C-classes, 39 impossible-change detector,
  70 state-update contract, 86 scoring, 106 prompt compiler, 87 severity gate.
Canon layout per story package:
  <pkg>/canon/{characters,outfits,locations,props}.json
  <pkg>/canon/world_state.json   (state + events + changelog + knowledge)
CLI:
  python3 vtsys/canon.py validate <pkg> <contract.json>
  python3 vtsys/canon.py update <pkg> <report.json>
  python3 vtsys/canon.py compile <pkg> <contract.json>
"""
import json
import os
import sys

WEIGHTS = {"character": 25, "props": 15, "location": 15, "time": 10,
           "weather": 10, "clothing": 10, "action": 10, "lighting": 5}
PENALTY = {"C4": 1.0, "C3": 0.5, "C2": 0.25, "C1": 0.1, "C0": 0.0}
DAY_SOURCES = {"sun", "window", "sky"}
NIGHT_SOURCES = {"moon", "lamp", "fire", "neon", "screen", "candle"}


def _load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def load_canon(pkg):
    d = os.path.join(pkg, "canon")
    return {
        "characters": _load(os.path.join(d, "characters.json")),
        "outfits": _load(os.path.join(d, "outfits.json")),
        "locations": _load(os.path.join(d, "locations.json")),
        "props": _load(os.path.join(d, "props.json")),
        "state": _load(os.path.join(d, "world_state.json")),
    }


def _tomin(t):
    day, hm = t.split(" ")
    h, m = hm.split(":")
    return int(day.replace("day", "")) * 1440 + int(h) * 60 + int(m)


def validate(pkg, contract):
    cn = load_canon(pkg)
    st = cn["state"]
    issues = []

    def hit(cat, sev, msg):
        issues.append({"category": cat, "severity": sev, "msg": msg})

    # TIME: must move forward (RULE 7)
    if _tomin(contract["time"]) < _tomin(st["time"]):
        hit("time", "C4", "time goes backward: %s < %s" % (contract["time"], st["time"]))
    # LOCATION exists (RULE 6)
    if contract["location"] not in cn["locations"]:
        hit("location", "C4", "unknown location " + contract["location"])
    # WEATHER teleport (RULE 3)
    if (contract.get("weather", {}).get("type") != st["weather"]["type"]
            and not contract.get("cause")):
        hit("weather", "C3", "weather changed without cause/time")
    # LIGHTING vs time of day (RULE 8)
    hr = int(contract["time"].split(" ")[1].split(":")[0])
    night = hr < 5 or hr >= 19
    src = (contract.get("lighting", {}) or {}).get("source", "")
    if night and src in DAY_SOURCES and cn["locations"].get(contract["location"], {}).get("type") == "exterior":
        hit("lighting", "C3", "daylight source at night exterior: " + src)
    if not night and src in NIGHT_SOURCES and src not in ("fire",):
        hit("lighting", "C2", "night source at daytime: " + src)
    # CHARACTERS
    for c in contract.get("characters", []):
        cid = c["id"]
        if cid not in cn["characters"]:
            hit("character", "C4", "unknown character " + cid)
            continue
        if cn["characters"][cid].get("refs", {}).get("status") == "draft":
            hit("character", "C2", cid + " master ref is DRAFT (temp ref in use)")
        # outfit registered + no silent change (RULE 4)
        if c.get("outfit") not in cn["characters"][cid].get("outfits", []):
            hit("clothing", "C3", cid + " unregistered outfit " + str(c.get("outfit")))
        elif (c.get("outfit") != st["characters"].get(cid, {}).get("outfit")
                and not contract.get("cause")):
            hit("clothing", "C3", cid + " outfit changed without cause")
        # teleport (RULE 6)
        if (contract["location"] != st["characters"].get(cid, {}).get("location")
                and not contract.get("cause") and not contract.get("travel")):
            hit("location", "C3", cid + " teleported to " + contract["location"])
        # injury reset (RULE 5)
        old_inj = set(st["characters"].get(cid, {}).get("injuries", []))
        new_inj = set(c.get("injuries", []))
        if old_inj - new_inj and not contract.get("cause"):
            hit("character", "C3", cid + " injuries vanished: %s" % (old_inj - new_inj))
    # PROPS vs state (RULE 2)
    for p in contract.get("props", []):
        pid = p["id"]
        if pid not in cn["props"]:
            hit("props", "C4", "unknown prop " + pid)
            continue
        ps = st["props"].get(pid, {})
        if (p.get("holder") != ps.get("holder") or p.get("location") != ps.get("location")) \
                and not contract.get("cause"):
            hit("props", "C4", pid + " teleported holder=%s loc=%s" % (
                p.get("holder"), p.get("location")))
    # ACTION needs cause for big changes (RULE 10)
    if contract.get("big_change") and not contract.get("cause"):
        hit("action", "C3", "big change without cause: " + contract["big_change"])

    score = 100.0
    for i in issues:
        score -= WEIGHTS[i["category"]] * PENALTY[i["severity"]]
    score = round(max(0.0, score), 1)
    blocked = any(i["severity"] in ("C3", "C4") for i in issues)
    return {"score": score, "blocked": blocked, "issues": issues}


def update(pkg, report):
    p = os.path.join(pkg, "canon", "world_state.json")
    st = _load(p)
    d = report.get("deltas", {})
    for k in ("time", "weather", "season"):
        if k in d:
            st[k] = d[k]
    for cid, cs in d.get("characters", {}).items():
        st["characters"].setdefault(cid, {}).update(cs)
    for pid, ps in d.get("props", {}).items():
        st["props"].setdefault(pid, {}).update(ps)
    for e in report.get("events", []):
        st["events"].append(e)
    st["changelog"].append({"scene": report.get("scene"), "at": report.get("time"),
                            "summary": report.get("summary", "")})
    tmp = p + ".tmp"
    json.dump(st, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, p)
    return {"scenes": len(st["changelog"]), "events": len(st["events"])}


NEGATIVE = ("DO NOT change identity, hair, scars. DO NOT invent props. "
            "DO NOT teleport objects. DO NOT reset clothing. "
            "DO NOT contradict time/weather/lighting. "
            "DO NOT add unexplained characters.")


def compile_prompt(pkg, contract):
    cn = load_canon(pkg)
    L = []
    L.append("[STYLE] " + contract.get("style", "dark manga anime"))
    for c in contract.get("characters", []):
        fx = cn["characters"][c["id"]].get("fixed", {})
        L.append("[CANON %s] %s" % (c["id"], fx.get("lock", "")))
        L.append("[STATE %s] outfit=%s emotion=%s held=%s" % (
            c["id"], c.get("outfit"), c.get("emotion"), c.get("held")))
    loc = cn["locations"][contract["location"]]
    L.append("[LOCATION %s] %s (%s)" % (contract["location"], loc.get("name"), loc.get("type")))
    for p in contract.get("props", []):
        L.append("[PROP %s] %s holder=%s" % (p["id"], cn["props"][p["id"]].get("name"), p.get("holder")))
    L.append("[TIME] " + contract["time"])
    L.append("[WEATHER] " + str(contract.get("weather", {}).get("type")))
    L.append("[LIGHTING] " + str((contract.get("lighting", {}) or {}).get("source")))
    L.append("[ACTION] " + contract.get("action", ""))
    L.append("[CAMERA] " + contract.get("camera", "wide"))
    L.append("[NEGATIVE] " + NEGATIVE)
    return " ".join(L)


if __name__ == "__main__":
    cmd, pkg, fp = sys.argv[1], sys.argv[2], sys.argv[3]
    data = _load(fp)
    if cmd == "validate":
        r = validate(pkg, data)
        print("SCORE:", r["score"], "BLOCKED:" if r["blocked"] else "PASS")
        for i in r["issues"]:
            print(" ", i["severity"], i["category"], "-", i["msg"])
        sys.exit(1 if r["blocked"] else 0)
    elif cmd == "update":
        print(update(pkg, data))
    elif cmd == "compile":
        print(compile_prompt(pkg, data))
