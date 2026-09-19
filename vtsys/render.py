# -*- coding: utf-8 -*-
"""سلاسل الرندر المُختبرة (§2.2/§3.3/§4.3) + الأسرّة الصوتية (§5.3)."""
import subprocess

ENC = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high",
       "-c:a", "aac", "-ar", "48000", "-ac", "2", "-movflags", "+faststart"]

def _run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("رندر فشل:\n" + r.stderr[-1500:])
    return r

def beds(win):
    """رياح شتاء + drone منخفض (§5.3)."""
    return (f"anoisesrc=color=pink:amplitude=0.55:d={win},lowpass=f=420,"
            f"tremolo=f=0.1:d=0.6,volume=0.45[wind];"
            f"sine=frequency=55:d={win},volume=0.05[s1];"
            f"sine=frequency=82.41:d={win},volume=0.025[s2];"
            f"[wind][s1][s2]amix=inputs=3:normalize=0,pan=stereo|c0=c0|c1=c0[amb]")

def narr_chain(sched, w0=0.0, off=1):
    parts = [f"[{off+i}:a]adelay={int(round((s['start']-w0)*1000))}|{int(round((s['start']-w0)*1000))}[d{i}]"
             for i, s in enumerate(sched)]
    n = len(sched)
    parts.append("".join(f"[d{i}]" for i in range(n)) +
                 f"amix=inputs={n}:duration=longest:normalize=0,asplit=2[vo1][vo2]")
    return ";".join(parts), n

def duck_mix(extra_amb=None):
    amb = extra_amb or "[0:a]volume=0.9[amb]"
    return (f"{amb};[amb][vo1]sidechaincompress=threshold=0.03:ratio=6:attack=25:release=400[ambd];"
            f"[ambd][vo2]amix=inputs=2:duration=first:normalize=0,"
            f"loudnorm=I=-16:TP=-1.5:LRA=11[aout]")

def render_short(ff, clip, vo, banner, ass, total, out):
    fc = (f"[0:v]fps=30,scale=3840:2160:flags=lanczos,"
          f"zoompan=z='1+0.12*on/{int(total*30)}':x='(iw-iw/zoom)*(0.20+0.60*on/{int(total*30)})':"
          f"y='(ih-ih/zoom)/2':d=1:s=1080x1920:fps=30,setsar=1[base];"
          f"[base][2:v]overlay=0:36[tmp];[tmp]ass={ass}[t2];"
          f"[t2]drawbox=x=0:y=1906:w='min(t/{total},1)*1080':h=14:color=0xFFC93C@0.95:t=fill[vout];"
          f"[0:a]volume=0.12[bg];[1:a]volume=1.0[vc];"
          f"[vc][bg]amix=inputs=2:duration=first:normalize=0,afade=t=out:st={total-1.5}:d=1.4[aout]")
    _run([ff, "-hide_banner", "-loglevel", "error", "-i", clip, "-i", vo,
          "-loop", "1", "-i", banner, "-filter_complex", fc,
          "-map", "[vout]", "-map", "[aout]", "-t", f"{total:.2f}", "-r", "30",
          *ENC[:6], "-crf", "20", "-level", "4.1",
          "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
          "-movflags", "+faststart", "-y", out])
    return out

def render_doc(ff, clip, sched, w0, win, ass, title, end, out, res=1080, amb_original=True):
    a, n = narr_chain(sched, w0)
    amb = "[0:a]volume=0.9[amb]" if amb_original else beds(win)
    bar = 110 if res == 1080 else 74
    y2 = (1080 - bar) if res == 1080 else (720 - bar)
    sc = ("scale=2304:1296:flags=bicubic" if res == 1080 else "scale=1536:864:flags=bicubic")
    sp = f"s=1920x1080:fps=25" if res == 1080 else "s=1280x720:fps=25"
    W = 1920 if res == 1080 else 1280
    RES = 1080 if res == 1080 else 720
    fc = (f"{a};{duck_mix(amb)};"
          f"[0:v]fps=25,{sc},zoompan=z='1+0.10*on/{int(win*25)}':"
          f"x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=1:{sp},setsar=1[b0];"
          f"[b0]drawbox=y=0:h={bar}:color=black:t=fill,drawbox=y={y2}:h={bar}:color=black:t=fill[b1];"
          f"[b1]ass={ass}[b2];"
          f"[b2]drawbox=x=0:y=0:w={W}:h={RES}:color=black@0.55:t=fill:enable='gte(t,{win-4.2:.1f})'[b3];"
          f"[{n+1}:v]scale={W}:{RES},format=rgba,fade=t=in:st=0.6:d=1.0:alpha=1,fade=t=out:st=4.0:d=1.0:alpha=1[ti];"
          f"[{n+2}:v]scale={W}:{RES},format=rgba,fade=t=in:st={win-4.0:.1f}:d=0.9:alpha=1[en];"
          f"[b3][ti]overlay=0:0:enable='between(t,0.4,5.1)'[b4];"
          f"[b4][en]overlay=0:0:enable='gte(t,{win-4.1:.1f})'[vout]")
    cmd = [ff, "-hide_banner", "-loglevel", "warning", "-i", clip]
    cmd += [x for s in sched for x in ("-i", s["file"])]
    cmd += ["-loop", "1", "-i", title, "-loop", "1", "-i", end,
            "-filter_complex", fc, "-map", "[vout]", "-map", "[aout]",
            "-t", f"{win:.2f}", "-r", "25", *ENC[:6], "-crf", "19", "-level", "4.2",
            "-preset", "fast", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", "-y", out]
    _run(cmd)
    return out

def render_manga_panels(ff, panels, sched, win, ass, title, end, out):
    n = len(sched)
    parts = []
    for i, s in enumerate(sched):
        N = int(s["scene_dur"] * 25); pan = 0.18 if i % 2 == 0 else 0.82
        parts.append(f"[{i}:v]scale=1536:1024,crop=1536:864:0:80,scale=2560:1440:flags=lanczos,"
                     f"zoompan=z='1+0.12*on/{N}':x='(iw-iw/zoom)*{pan}':y='(ih-ih/zoom)/2':d=1:"
                     f"s=1280x720:fps=25,vignette=PI/5,setsar=1[v{i}]")
    parts.append("".join(f"[v{i}]" for i in range(n)) +
                 f"concat=n={n}:v=1:a=0,noise=alls=4:allf=t,fps=25[basev]")
    a, _ = narr_chain(sched, 0.0, off=n)
    fc = (";".join(parts) + ";" + a + ";" + duck_mix(beds(win)) + ";"
          f"[basev]drawbox=y=0:h=74:color=black:t=fill,drawbox=y=646:h=74:color=black:t=fill[b1];"
          f"[b1]ass={ass}[b2];"
          f"[b2]drawbox=x=0:y=0:w=1280:h=720:color=black@0.6:t=fill:enable='gte(t,{win-4.2:.1f})'[b3];"
          f"[{2*n}:v]scale=1280:720,format=rgba,fade=t=in:st=0.6:d=1.0:alpha=1,fade=t=out:st=4.2:d=1.0:alpha=1[ti];"
          f"[{2*n+1}:v]scale=1280:720,format=rgba,fade=t=in:st={win-4.0:.1f}:d=0.9:alpha=1[en];"
          f"[b3][ti]overlay=0:0:enable='between(t,0.4,5.3)'[b4];"
          f"[b4][en]overlay=0:0:enable='gte(t,{win-4.1:.1f})'[vout]")
    cmd = [ff, "-hide_banner", "-loglevel", "warning"]
    for i, s in enumerate(sched):
        cmd += ["-loop", "1", "-framerate", "25", "-t", f"{s['scene_dur']}", "-i", panels[s["idx"]]]
    cmd += [x for s in sched for x in ("-i", s["file"])]
    cmd += ["-loop", "1", "-i", title, "-loop", "1", "-i", end,
            "-filter_complex", fc, "-map", "[vout]", "-map", "[aout]",
            "-t", f"{win:.2f}", "-r", "25", *ENC[:6], "-crf", "23", "-level", "4.0",
            "-preset", "fast", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", "-y", out]
    _run(cmd)
    return out

def render_wordcut(ff, stills, v_sched, a_sched, win, ass, title, end, out):
    """§4.6: فيديو مقطّع على إيقاع الكلمات (stills من sprite sheets) + صوت على الجُمل.
    stills: مسار still لكل beat بالترتيب (v_sched[i] ↔ stills[i]).
    v_sched: [{scene_dur}] للصورة · a_sched: [{file,start,dur_narr}] للصوت (مستقلان)."""
    B, S = len(v_sched), len(a_sched)
    parts = []
    for i, s in enumerate(v_sched):
        N = max(1, int(s["scene_dur"] * 25)); pan = 0.18 if i % 2 == 0 else 0.82
        parts.append(f"[{i}:v]scale=1920:1080,"
                     f"zoompan=z='1+0.10*on/{N}':x='(iw-iw/zoom)*{pan}':y='(ih-ih/zoom)/2':d=1:"
                     f"s=1280x720:fps=25,vignette=PI/5,setsar=1[v{i}]")
    parts.append("".join(f"[v{i}]" for i in range(B)) +
                 f"concat=n={B}:v=1:a=0,noise=alls=4:allf=t,fps=25[basev]")
    a, _ = narr_chain(a_sched, 0.0, off=B)
    fc = (";".join(parts) + ";" + a + ";" + duck_mix(beds(win)) + ";"
          f"[basev]drawbox=y=0:h=74:color=black:t=fill,drawbox=y=646:h=74:color=black:t=fill[b1];"
          f"[b1]ass={ass}[b2];"
          f"[b2]drawbox=x=0:y=0:w=1280:h=720:color=black@0.6:t=fill:enable='gte(t,{win-4.2:.1f})'[b3];"
          f"[{B+S}:v]scale=1280:720,format=rgba,fade=t=in:st=0.6:d=1.0:alpha=1,fade=t=out:st=4.2:d=1.0:alpha=1[ti];"
          f"[{B+S+1}:v]scale=1280:720,format=rgba,fade=t=in:st={win-4.0:.1f}:d=0.9:alpha=1[en];"
          f"[b3][ti]overlay=0:0:enable='between(t,0.4,5.3)'[b4];"
          f"[b4][en]overlay=0:0:enable='gte(t,{win-4.1:.1f})'[vout]")
    cmd = [ff, "-hide_banner", "-loglevel", "warning"]
    for i, s in enumerate(v_sched):
        cmd += ["-loop", "1", "-framerate", "25", "-t", f"{s['scene_dur']}", "-i", stills[i]]
    cmd += [x for s in a_sched for x in ("-i", s["file"])]
    cmd += ["-loop", "1", "-i", title, "-loop", "1", "-i", end,
            "-filter_complex", fc, "-map", "[vout]", "-map", "[aout]",
            "-t", f"{win:.2f}", "-r", "25", *ENC[:6], "-crf", "23", "-level", "4.0",
            "-preset", "fast", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", "-y", out]
    _run(cmd)
    return out

def render_dynamic(ff, stills, v_sched, a_sched, sfx, win, ass, title, end, out, cards=True):
    """§4.8: رندر سينمائي — حركة لكل لقطة + فلاش لحظات القوة + SFX.
    v_sched[i]: {scene_dur, shot:{type,mood}} · sfx: {whoosh:[t], impact:[t], riser:[t],
    flash:[t], whoosh_file, impact_file, riser_file}."""
    from .dynamics import beat_video_chain
    B, S = len(v_sched), len(a_sched)
    W, I, R = len(sfx["whoosh"]), len(sfx["impact"]), len(sfx["riser"])
    parts = [beat_video_chain(i, s["scene_dur"], s["shot"]) for i, s in enumerate(v_sched)]
    parts.append("".join(f"[v{i}]" for i in range(B)) +
                 f"concat=n={B}:v=1:a=0,noise=alls=4:allf=t,fps=25[basev]")
    a, _ = narr_chain(a_sched, 0.0, off=B)
    v = B + S
    wp = [f"[{v + i}:a]adelay={int(t * 1000)}|{int(t * 1000)},volume=0.35[w{i}]"
          for i, t in enumerate(sfx["whoosh"])]
    ip = [f"[{v + W + i}:a]adelay={int(t * 1000)}|{int(t * 1000)},volume=0.5[im{i}]"
          for i, t in enumerate(sfx["impact"])]
    rp = [f"[{v + W + I + i}:a]adelay={int(t * 1000)}|{int(t * 1000)},volume=0.3[rs{i}]"
          for i, t in enumerate(sfx["riser"])]
    wp.append("".join(f"[w{i}]" for i in range(W)) + f"amix=inputs={W}:duration=longest:normalize=0[wh]")
    ip.append("".join(f"[im{i}]" for i in range(I)) + f"amix=inputs={I}:duration=longest:normalize=0[im]")
    if R:
        rp.append("".join(f"[rs{i}]" for i in range(R)) + f"amix=inputs={R}:duration=longest:normalize=0[rs]")
        sfxmix = "[amb][wh][rs]amix=inputs=3:normalize=0[amb0]"
    else:
        sfxmix = "[amb][wh]amix=inputs=2:normalize=0[amb0]"
    flashes = "".join(
        f",drawbox=x=0:y=0:w=1280:h=720:color=white@0.8:t=fill:enable='between(t,{t:.2f},{t + 0.1:.2f})'"
        for t in sfx["flash"])
    video_base = (f"[basev]drawbox=y=0:h=74:color=black:t=fill,drawbox=y=646:h=74:color=black:t=fill{flashes}[b1];"
                  f"[b1]ass={ass}[vout]" if not cards else
                  f"[basev]drawbox=y=0:h=74:color=black:t=fill,drawbox=y=646:h=74:color=black:t=fill{flashes}[b1];"
                  f"[b1]ass={ass}[b2];"
                  f"[b2]drawbox=x=0:y=0:w=1280:h=720:color=black@0.6:t=fill:enable='gte(t,{win - 4.2:.1f})'[b3];"
                  f"[{v + W + I + R}:v]scale=1280:720,format=rgba,fade=t=in:st=0.6:d=1.0:alpha=1,fade=t=out:st=4.2:d=1.0:alpha=1[ti];"
                  f"[{v + W + I + R + 1}:v]scale=1280:720,format=rgba,fade=t=in:st={win - 4.0:.1f}:d=0.9:alpha=1[en];"
                  f"[b3][ti]overlay=0:0:enable='between(t,0.4,5.3)'[b4];"
                  f"[b4][en]overlay=0:0:enable='gte(t,{win - 4.1:.1f})'[vout]")
    fc = (";".join(parts) + ";" + a + ";" + beds(win) + ";" + ";".join(wp + ip + rp) + ";"
          + sfxmix + ";"
          "[amb0][vo1]sidechaincompress=threshold=0.03:ratio=6:attack=25:release=400[ambd];"
          "[ambd][vo2][im]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[aout];" + video_base)
    cmd = [ff, "-hide_banner", "-loglevel", "warning"]
    for i, s in enumerate(v_sched):
        cmd += ["-loop", "1", "-framerate", "25", "-t", f"{s['scene_dur']}", "-i", stills[i]]
    cmd += [x for s in a_sched for x in ("-i", s["file"])]
    cmd += [x for _ in sfx["whoosh"] for x in ("-i", sfx["whoosh_file"])]
    cmd += [x for _ in sfx["impact"] for x in ("-i", sfx["impact_file"])]
    cmd += [x for _ in sfx["riser"] for x in ("-i", sfx["riser_file"])]
    cmd += ["-loop", "1", "-i", title, "-loop", "1", "-i", end,
            "-filter_complex", fc, "-map", "[vout]", "-map", "[aout]",
            "-t", f"{win:.2f}", "-r", "25", *ENC[:6], "-crf", "23", "-level", "4.0",
            "-preset", "fast", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", "-y", out]
    _run(cmd)
    return out

def render_manga(ff, base, sched, win, ass, title, end, out):
    a, n = narr_chain(sched, 0.0)
    fc = (f"{a};{duck_mix(beds(win))};"
          f"[0:v]fps=25,noise=alls=4:allf=t,drawbox=y=0:h=74:color=black:t=fill,drawbox=y=646:h=74:color=black:t=fill[b1];"
          f"[b1]ass={ass}[b2];"
          f"[b2]drawbox=x=0:y=0:w=1280:h=720:color=black@0.6:t=fill:enable='gte(t,{win-4.2:.1f})'[b3];"
          f"[{n+1}:v]scale=1280:720,format=rgba,fade=t=in:st=0.6:d=1.0:alpha=1,fade=t=out:st=4.2:d=1.0:alpha=1[ti];"
          f"[{n+2}:v]scale=1280:720,format=rgba,fade=t=in:st={win-4.0:.1f}:d=0.9:alpha=1[en];"
          f"[b3][ti]overlay=0:0:enable='between(t,0.4,5.3)'[b4];"
          f"[b4][en]overlay=0:0:enable='gte(t,{win-4.1:.1f})'[vout]")
    cmd = [ff, "-hide_banner", "-loglevel", "warning", "-i", base]
    cmd += [x for s in sched for x in ("-i", s["file"])]
    cmd += ["-loop", "1", "-i", title, "-loop", "1", "-i", end,
            "-filter_complex", fc, "-map", "[vout]", "-map", "[aout]",
            "-t", f"{win:.2f}", "-r", "25", *ENC[:6], "-crf", "23", "-level", "4.0",
            "-preset", "fast", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", "-y", out]
    _run(cmd)
    return out
