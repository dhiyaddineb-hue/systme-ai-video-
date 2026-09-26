# -*- coding: utf-8 -*-
"""Acceptance checks for articulated 2D animation prototypes."""
import json, os, subprocess

def audit(manifest, output=None):
    errors=[]; warnings=[]
    data=json.load(open(manifest,encoding='utf-8'))
    if data.get('animation_type') != '2d_cutout_keyframe': errors.append('unknown animation type')
    frames=int(data.get('frames',0)); fps=float(data.get('fps',0)); dur=float(data.get('duration',0))
    if frames <= 0 or fps <= 0: errors.append('invalid frame/fps manifest')
    if frames and fps and abs(frames/fps-dur) > 0.1: errors.append('frame count does not match duration')
    if data.get('lip_sync'): warnings.append('lip sync is declared but this prototype has no lip-sync gate')
    if not data.get('lip_sync',False): warnings.append('voice is external narration; lip-sync not claimed')
    if output:
        if not os.path.exists(output): errors.append('missing animation output')
        else:
            ffmpeg=os.environ.get('FFMPEG_BIN','ffmpeg')
            if not os.path.exists(ffmpeg):
                ffmpeg=os.path.join(os.path.dirname(os.path.dirname(__file__)),'bin','ffmpeg')
            r=subprocess.run([ffmpeg,'-hide_banner','-i',output],capture_output=True,text=True)
            probe=r.stdout+'\n'+r.stderr
            if 'Video:' not in probe or 'Audio:' not in probe: errors.append('missing video/audio stream')
    return {'status':'FAIL' if errors else 'PASS','errors':errors,'warnings':warnings,'manifest':data}
