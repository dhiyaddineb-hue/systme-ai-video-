# -*- coding: utf-8 -*-
"""Small deterministic 2D cut-out animation renderer.

It is deliberately honest: this is articulated 2D keyframe animation, not a
text-to-video model and not frame-by-frame hand animation. Assets are saved as
separate parts so a single bad limb or pose can be regenerated.
"""
from pathlib import Path
import math, random
from PIL import Image, ImageDraw, ImageFilter

W,H=1280,720

def _part(size, fill, outline=(20,20,20,255), width=5):
    im=Image.new("RGBA",size,(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((3,3,size[0]-4,size[1]-4),radius=min(size)//5,fill=fill,outline=outline,width=width)
    return im

def make_rig_assets(out):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    # Neutral monochrome cut-out pieces, with a generated character reference kept beside them.
    _part((100,135),(68,68,68,255)).save(out/'head.png')
    _part((190,250),(48,48,48,255)).save(out/'torso.png')
    _part((70,170),(75,75,75,255)).save(out/'upper_arm.png')
    _part((62,155),(105,105,105,255)).save(out/'lower_arm.png')
    _part((85,190),(45,45,45,255)).save(out/'upper_leg.png')
    _part((75,175),(82,82,82,255)).save(out/'lower_leg.png')
    axe=Image.new('RGBA',(220,70),(0,0,0,0)); d=ImageDraw.Draw(axe)
    d.line((15,52,205,18),fill=(35,35,35,255),width=12); d.polygon([(55,48),(95,5),(125,8),(92,58)],fill=(180,180,180,255),outline=(20,20,20,255))
    axe.save(out/'axe.png')
    # Prefer the generated, consistent character sheet for the visible hero.
    # The procedural parts remain available as the articulated fallback.
    ref = out.parent / 'character_reference.jpg'
    if ref.exists():
        src = Image.open(ref).convert('RGB').crop((0, 0, 285, 735))
        pix = src.load(); alpha = Image.new('L', src.size, 0); ap = alpha.load()
        for yy in range(src.height):
            for xx in range(src.width):
                r,g,b = pix[xx,yy]
                # remove the white sheet while preserving ink and shading
                ap[xx,yy] = max(0, min(255, 255 - min(r,g,b)))
        src.putalpha(alpha)
        src.save(out/'character.png')

def _rot(im,deg): return im.rotate(deg,resample=Image.Resampling.BICUBIC,expand=True)

def _place(canvas, im, xy): canvas.alpha_composite(im,(int(xy[0]-im.width/2),int(xy[1]-im.height/2)))

def render_frames(background, rig_dir, out_dir, fps=25, duration=20.0):
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    bg=Image.open(background).convert('RGB').resize((W,H),Image.Resampling.LANCZOS).convert('RGBA')
    parts={n:Image.open(Path(rig_dir)/(n+'.png')).convert('RGBA') for n in ('head','torso','upper_arm','lower_arm','upper_leg','lower_leg','axe')}
    hero_path=Path(rig_dir)/'character.png'
    hero=Image.open(hero_path).convert('RGBA') if hero_path.exists() else None
    if hero is not None:
        hero.thumbnail((245, 460), Image.Resampling.LANCZOS)
    random.seed(7); flakes=[(random.randrange(W),random.randrange(H),random.randrange(1,4)) for _ in range(120)]
    frames=int(duration*fps)
    for k in range(frames):
        t=k/fps; c=bg.copy(); d=ImageDraw.Draw(c)
        # restrained snow layer; motion is environmental, not fake camera shake.
        for x,y,r in flakes:
            yy=(y+int(26*t))%H; d.ellipse((x,yy,x+r,yy+r),fill=(245,245,245,150))
        # keyframes: approach, reach/axe, then deliberate settle.
        # The cabin door is a persistent prop landmark: its opening and glow make
        # the object interaction readable even when the hero is a textured cutout.
        if 6 <= t < 13:
            p=min(1.0,(t-6)/2.0)
            door_x, door_y = 945, 430
            d.line((door_x,door_y,door_x+int(34*p),door_y+8), fill=(42,28,22,220), width=7)
            d.ellipse((door_x-18,door_y-20,door_x+18,door_y+16), outline=(232,201,120,150), width=3)
        if t<6: u=t/6; x=220+480*(u*u*(3-2*u)); lean=-4+4*u
        elif t<13: x=700; lean=4*math.sin((t-6)*.7)
        else: x=700; lean=0
        base_y=500
        if hero is not None:
            # Generated inked hero keeps face, clothing and boots consistent.
            # Keyframes still provide approach, reach/reaction body language and settle.
            bob = 3*math.sin(t*7) if t < 6 else (5*math.sin((t-6)*2.2) if t < 13 else 0)
            tilt = lean + (4*math.sin((t-6)*2.0) if 6 <= t < 13 else 0)
            _place(c, _rot(hero, tilt), (x, base_y-hero.height/2+25+bob))
        else:
            # articulated fallback rig
            stride=18*math.sin(t*7) if t<6 else 0
            _place(c,_rot(parts['lower_leg'],lean+stride/3),(x-34,base_y+100))
            _place(c,_rot(parts['lower_leg'],-lean-stride/3),(x+34,base_y+100))
            _place(c,_rot(parts['upper_leg'],lean),(x-28,base_y+22))
            _place(c,_rot(parts['upper_leg'],-lean),(x+28,base_y+22))
            _place(c,_rot(parts['torso'],lean),(x,base_y-75))
            reach=0
            if 6<=t<13: reach=-28*min(1,(t-6)/2)
            _place(c,_rot(parts['upper_arm'],35+reach),(x-72,base_y-95))
            _place(c,_rot(parts['lower_arm'],55+reach),(x-100,base_y-175))
            _place(c,_rot(parts['upper_arm'],-20),(x+72,base_y-95))
            _place(c,_rot(parts['lower_arm'],-15),(x+92,base_y-170))
            _place(c,parts['head'],(x,base_y-230))
            axe_angle=-18 if t<6 else (-48 if t<13 else -30)
            _place(c,_rot(parts['axe'],axe_angle),(x+125,base_y-150))
        c.convert('RGB').save(out/f'frame_{k:05d}.jpg',quality=94)
    return frames
