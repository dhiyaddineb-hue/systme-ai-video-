# -*- coding: utf-8 -*-
"""Narrative contract checks before voice generation and montage."""
import json

def audit(path, max_words=38):
    data=json.load(open(path,encoding='utf-8')); units=data.get('units',data.get('lines',[])); errors=[]; warnings=[]
    if not units: errors.append('no script units')
    seen=[]
    for i,u in enumerate(units,1):
        text=' '.join(str(u.get('text','')).split())
        if not text: errors.append(f'unit {i}: empty text')
        if len(text.split()) > max_words: warnings.append(f'unit {i}: {len(text.split())} words exceeds {max_words}')
        if not u.get('beat') and 'units' in data: warnings.append(f'unit {i}: missing beat')
        owner=u.get('panel',u.get('region',i))
        if owner in seen: errors.append(f'unit {i}: repeated visual owner {owner}')
        seen.append(owner)
    return {'status':'FAIL' if errors else 'PASS','units':len(units),'errors':errors,'warnings':warnings}
