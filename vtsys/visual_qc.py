# -*- coding: utf-8 -*-
"""Image-source QA: reject low-resolution or repeated source art."""
import hashlib, os

def audit(files, min_width=1280, min_height=720):
    from PIL import Image
    reports=[]; errors=[]; hashes={}
    for path in files:
        try:
            with Image.open(path) as im:
                w,h=im.size; ratio=w/h
            digest=hashlib.md5(open(path,'rb').read()).hexdigest()
            reports.append({'file':path,'width':w,'height':h,'ratio':round(ratio,3)})
            if w<min_width or h<min_height: errors.append(f'{path}: resolution {w}x{h} below {min_width}x{min_height}')
            if not 1.70 <= ratio <= 1.85: errors.append(f'{path}: aspect ratio {ratio:.3f} is not 16:9')
            if digest in hashes: errors.append(f'{path}: duplicate of {hashes[digest]}')
            hashes[digest]=path
        except Exception as exc: errors.append(f'{path}: {exc}')
    return {'status':'FAIL' if errors else 'PASS','files':reports,'errors':errors}
