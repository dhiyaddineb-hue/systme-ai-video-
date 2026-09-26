import os,sys,subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; PKG=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from vtsys import env, captions, animation2d
from vtsys.scenes import duration
ff=env.ensure_ffmpeg(str(ROOT)); rig=PKG/'rig'; animation2d.make_rig_assets(rig)
frames=animation2d.render_frames(PKG/'background_snow_cabin.jpg',rig,PKG/'frames',fps=25,duration=20)
# Exact speech starts from measured durations; no guessed word timing is used for the edit.
a=[PKG/'vo_a.mp3',PKG/'vo_b.mp3']; da=[duration(ff,str(x)) for x in a]; start_b=8.0
sched=[{'start':0.0,'dur_narr':da[0],'text':'قبل حلول الليل، يقترب الرجل من الكوخ. لا يزال الباب مغلقاً، لكن وجوده يمنحه فرصة.'},{'start':start_b,'dur_narr':da[1],'text':'يمسك الفأس، ثم يتوقف. في هذا الوادي، أحياناً تكون الخطوة الأهم هي أن تعرف متى تنتظر.'}]
ass=captions.ass_doc(str(PKG/'animation.ass'),sched,0.0,size=48,margin_v=34)
out=PKG/'snow_cabin_cutout_animation_v1.mp4'
# Image sequence + two delayed voice clips + quiet wind bed. No lip-sync is claimed: voice is external narration.
fc=(f"[1:a]adelay=0|0[a0];[2:a]adelay={int(start_b*1000)}|{int(start_b*1000)}[a1];"
    f"[a0][a1]amix=inputs=2:duration=longest:normalize=0,asplit=2[vo0][vo1];"
    f"anoisesrc=color=pink:amplitude=0.18:d=20,lowpass=f=650[amb];"
    f"[amb][vo0]sidechaincompress=threshold=0.03:ratio=5:attack=25:release=350[duck];"
    f"[duck][vo1]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[aout];"
    f"[0:v]format=yuv420p,fps=25,ass={ass}[vout]")
cmd=[ff,'-hide_banner','-loglevel','warning','-framerate','25','-i',str(PKG/'frames/frame_%05d.jpg'),'-i',str(a[0]),'-i',str(a[1]),'-filter_complex',fc,'-map','[vout]','-map','[aout]','-t','20','-c:v','libx264','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-ar','48000','-ac','2','-movflags','+faststart','-y',str(out)]
r=subprocess.run(cmd,capture_output=True,text=True)
if r.returncode: raise SystemExit(r.stderr[-2000:])
json.dump({'status':'PASS','animation_type':'2d_cutout_keyframe','frames':frames,'fps':25,'duration':20.0,'voice_timing':{'a_seconds':da,'b_start':start_b},'lip_sync':False,'output':str(out)},open(PKG/'manifest.json','w'),ensure_ascii=False,indent=2)
print(json.dumps(json.load(open(PKG/'manifest.json')),ensure_ascii=False,indent=2))
