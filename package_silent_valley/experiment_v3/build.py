import os,sys,subprocess,json
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); PKG=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,ROOT)
from vtsys import config,env,captions,render,audio_qc,visual_qc
from vtsys.scenes import duration
from vtsys.tts import word_times
cfg=config.load(ROOT); ff=env.ensure_ffmpeg(ROOT)
texts=["رغم العاصفة، دخل الرجل الوادي حاملاً فأسه وحلماً قديماً.","بين الثلج، وجد كوخاً نصف مدفون. لمس بابه المتجمد، فشعر بنبض تحت الخشب.","في الليل اشتعلت نار صغيرة. داخل الكوخ، بدأ الصمت يتحول إلى وطن."]
files=[os.path.join(PKG,'vo',f'v0{i}.mp3') for i in range(1,4)]
panels=[os.path.join(PKG,'panels',f'p0{i}.jpg') for i in range(1,4)]
for p in files+panels: assert os.path.exists(p),p
# actual durations drive both audio and picture
sched=[]; t=0.0
for i,(text,fp) in enumerate(zip(texts,files)):
 d=duration(ff,fp)
 sched.append({'idx':i,'text':text,'file':fp,'dur_narr':d,'start':round(t,2),'scene_dur':round(d+(.25 if i<2 else 0),2),'words':word_times(text,d)})
 t+=d+(.25 if i<2 else 0)
ass=captions.ass_kinetic(os.path.join(PKG,'experiment.ass'),[{'start':x['start'],'words':x['words']} for x in sched],0)
# generate small documentary whoosh once and place it only at actual cuts
sfxd=os.path.join(PKG,'sfx'); os.makedirs(sfxd,exist_ok=True); whoosh=os.path.join(sfxd,'whoosh.wav')
subprocess.run([ff,'-hide_banner','-loglevel','error','-f','lavfi','-i','anoisesrc=color=pink:d=0.35','-af','highpass=f=500,lowpass=f=3500,afade=t=out:st=0.2:d=0.15,volume=0.16','-ar','48000','-ac','2','-y',whoosh],check=True)
starts=[sched[1]['start'],sched[2]['start']]
sfx={'whoosh':starts,'impact':[],'riser':[],'flash':[],'whoosh_file':whoosh,'impact_file':whoosh,'riser_file':whoosh}
vs=[{'idx':i,'scene_dur':x['scene_dur'],'start':x['start'],'shot':{'type':['establishing','detail','reaction'][i],'mood':'تشويق' if i<2 else 'دفء'}} for i,x in enumerate(sched)]
out=os.path.join(PKG,'silent_valley_experiment_v3.mp4')
render.render_dynamic(ff,panels,vs,sched,sfx,t,ass,os.path.join(ROOT,'package_silent_valley/title.png'),os.path.join(ROOT,'package_silent_valley/end.png'),out,cards=False)
print(json.dumps({'output':out,'duration':round(t,2),'audio_qc':audio_qc.audit(ff,files),'visual_qc':visual_qc.audit(panels)},ensure_ascii=False,indent=2))
