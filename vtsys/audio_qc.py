# -*- coding: utf-8 -*-
"""Lightweight voice QA: duration, silence and clipping risk before edit."""
import re, subprocess

def inspect(ff, path):
    cmd=[ff,"-hide_banner","-nostats","-i",path,"-af","volumedetect,silencedetect=noise=-42dB:d=0.35","-f","null","-"]
    r=subprocess.run(cmd,capture_output=True,text=True)
    text=r.stderr
    mean=re.findall(r"mean_volume:\s*([-+\d.]+) dB",text)
    peak=re.findall(r"max_volume:\s*([-+\d.]+) dB",text)
    silences=len(re.findall(r"silence_start",text))
    return {"file":path,"mean_db":float(mean[-1]) if mean else None,"peak_db":float(peak[-1]) if peak else None,"silence_events":silences,"status":"PASS" if r.returncode==0 else "FAIL"}

def audit(ff, files):
    reports=[inspect(ff,p) for p in files]
    errors=[]
    for x in reports:
        if x["status"]!="PASS": errors.append(x["file"]+": ffmpeg failed")
        if x["peak_db"] is not None and x["peak_db"] > -0.5: errors.append(x["file"]+": clipping risk")
        if x["mean_db"] is not None and x["mean_db"] < -32: errors.append(x["file"]+": voice too quiet")
    return {"status":"FAIL" if errors else "PASS","files":reports,"errors":errors}
