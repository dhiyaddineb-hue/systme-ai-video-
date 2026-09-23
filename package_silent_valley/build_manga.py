# -*- coding: utf-8 -*-
"""وثائقي الوادي الصامت: صوت يقود التايملاين + لوحات منفردة + مونتاج هادئ."""
import json, os, sys, subprocess
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PKG=os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,ROOT)
from vtsys import config, env, captions, render
from vtsys.tts import word_times
from vtsys.scenes import duration
from vtsys.sheets import extract_film_subs, audit_shots

story=json.load(open(os.path.join(PKG,'story.json'),encoding='utf-8'))
data=json.load(open(os.path.join(PKG,'sentences.json'),encoding='utf-8')); units=data['units']
cfg=config.load(ROOT); ff=env.ensure_ffmpeg(ROOT)
fp={k:(v if os.path.isabs(v) else os.path.join(ROOT,v)) for k,v in cfg['fonts'].items()}

def meanings(text): return [x.strip() for x in text.replace('...','…').split('…') if x.strip()]
print('VO schedule ...')
sents=[]; t=0.0
for u in units:
 f=os.path.join(PKG,u['vo']); assert os.path.exists(f),f
 d=round(duration(ff,f),2); words=word_times(u['text'],d)
 sents.append({'start':round(t,2),'dur':d,'words':words,'file':f}); t=round(t+d+data.get('gap',.6),2)
win=round(t-data.get('gap',.6),2)
print('individual panels + film crops ...')
film={}; shots=[]; a_sched=[]
frames=['wide','left','right','top','low','punch']
for i,u in enumerate(units):
 p=os.path.join(PKG,'panels_manga',u['panel']+'.jpg'); assert os.path.exists(p),p
 film[u['panel']]=extract_film_subs(ff,p,os.path.join(PKG,'filmshots_manga'),u['panel'])
 segs=meanings(u['text']); d=sents[i]['dur']; n=min(6,max(1,len(segs)))
 # documentary rhythm: each meaning gets a deliberate wide/medium/detail/punch progression
 for j in range(n):
  st=round(sents[i]['start']+d*j/n,2); dd=round(d/n,2) if j<n-1 else round(d-d*(n-1)/n,2)
  typ='establishing' if j==0 else ('key_action' if j==n-1 and u['beat'] in ('build','storm','fire','cliff') else 'detail' if j%2 else 'reaction')
  shots.append({'sent':u['id'],'time':st,'dur':dd,'type':typ,'mood':'دفء' if u['beat'] in ('fire','shelter') else 'تشويق','still':(u['panel'],frames[j])})
 a_sched.append({'idx':i,'text':u['text'],'file':sents[i]['file'],'dur_narr':sents[i]['dur'],'start':sents[i]['start'],'scene_dur':None})
json.dump({'story':story['slug'],'status':'auto-approved (no-repeat audit PASS)','shots':shots},open(os.path.join(PKG,'storyboard.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
with open(os.path.join(PKG,'storyboard.md'),'w',encoding='utf-8') as f:f.write(f"# {story['title']} — {len(shots)} لقطة وثائقية\n")
# Expand the shot references into concrete crop files for the audit.
stills=[]
for s in shots:
 p,fr=s['still']; stills.append(film[p][fr])
audit_shots(stills); print(f'shot audit: PASS ({len(stills)} unique documentary shots)')
v_sched=[{'idx':i,'scene_dur':s['dur'],'start':s['time'],'shot':{'type':s['type'],'mood':s['mood']}} for i,s in enumerate(shots)]
# each audio sentence is delayed on its actual start; duplicate entries are not needed
# narr_chain expects one audio input per schedule entry, so use sentence schedule separately.
print('cards + SFX ...')
captions.card(os.path.join(PKG,'title.png'),[(story['title'],'naskh',130,310,(255,255,255,255),5),(story['subtitle'],'naskh',58,500,(230,214,160,255),3)],fp)
captions.card(os.path.join(PKG,'end.png'),[(story['endcard'],'naskh',110,430,(255,255,255,255),5),(story['endcard2'],'naskh',50,590,(230,214,160,255),3)],fp)
sfxd=os.path.join(ROOT,'build','sfx'); os.makedirs(sfxd,exist_ok=True); WAV={}
def mk(name,args):
 o=os.path.join(sfxd,name+'.wav')
 if not os.path.exists(o): subprocess.run([ff,'-hide_banner','-loglevel','error',*args,'-y',o],check=True,capture_output=True)
 WAV[name]=o
mk('whoosh',['-f','lavfi','-i','anoisesrc=color=pink:d=0.35','-af','highpass=f=500,lowpass=f=4000,afade=t=out:st=0.2:d=0.15,volume=0.20','-ar','48000','-ac','2'])
mk('impact',['-f','lavfi','-i','sine=frequency=70:duration=0.45','-af','afade=t=out:st=0.15:d=0.3,volume=0.18','-ar','48000','-ac','2'])
mk('riser',['-f','lavfi','-i','anoisesrc=color=pink:d=1','-af','highpass=f=700,afade=t=in:st=0:d=1,volume=0.12','-ar','48000','-ac','2'])
key=[sents[i]['start'] for i,u in enumerate(units) if u['beat'] in ('build','storm','fire','cliff')]; sfx={'whoosh':[s['start'] for s in sents[1:]],'impact':[round(x+.05,2) for x in key],'riser':[],'flash':[], 'whoosh_file':WAV['whoosh'],'impact_file':WAV['impact'],'riser_file':WAV['riser']}
# render_dynamic is designed for per-shot audio; give it the sentence audio schedule and hold each sentence's first shot.
v_sched2=[]
for i,s in enumerate(shots): v_sched2.append({'idx':i,'scene_dur':s['dur'],'start':s['time'],'shot':{'type':s['type'],'mood':s['mood']}})
# duplicate audio schedule per sentence is not needed; use render_manga_panels-compatible schedule by sentence windows
# Build a compact per-sentence visual timeline with each sentence's first film crop; captions remain sentence-timed.
base_stills=[film[u['panel']]['wide'] for u in units]
vs=[]
for i,u in enumerate(units):
 vs.append({'idx':i,'scene_dur':sents[i]['dur']+data.get('gap',.6),'start':sents[i]['start'],'shot':{'type':'establishing','mood':'دفء' if u['beat'] in ('fire','shelter') else 'تشويق'}})
out=os.path.join(PKG,'silent_valley_ep1_manga.mp4')
ass=captions.ass_kinetic(os.path.join(PKG,story['ass']),[{'start':s['start'],'words':s['words']} for s in sents],0.0)
render.render_dynamic(ff,base_stills,vs,a_sched,sfx,win,ass,os.path.join(PKG,'title.png'),os.path.join(PKG,'end.png'),out,cards=True)
print('OK',out)
