"""Build an honest, self-hosted public GitHub milestones panel.

Facts come from GitHub's public REST API. No invented ranks, awards, or
private activity. This script deliberately never edits README.md.
"""
from __future__ import annotations
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

USER = "Adil307"
DEST = Path(__file__).resolve().parent.parent / "assets" / "milestones-live.svg"

def fetch(path):
    h = {
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'Adil307-github-milestones'
    }
    token = os.getenv('GH_TOKEN')
    if token: h['Authorization'] = 'Bearer ' + token
    with urlopen(Request('https://api.github.com/' + path, headers=h), timeout=30) as response:
        return json.load(response)

def label(x, y, s, size=20, color='#dbe3ff', weight='500'):
    return (f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial,Helvetica,sans-serif" '
            f'font-size="{size}" font-weight="{weight}">{escape(str(s))}</text>')

def render(profile, repos, stamp):
    original = [r for r in repos if not r.get('fork',False) and not r.get('private',False)]
    public = [r for r in repos if not r.get('private',False)]
    stars = sum(int(r.get('stargazers_count') or 0) for r in original)
    languages = len(set(r['language'] for r in original if r.get('language')))
    rows = [
      ('PUBLIC REPOS',len(public),'Public repositories owned'),
      ('FOLLOWERS',int(profile['followers']),'Public follower count'),
      ('REPO STARS',stars,'Non-fork repositories'),
      ('LANGUAGES',languages,'Primary repo languages')
    ]
    out = [
      '<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="290" viewBox="0 0 1120 290" role="img" aria-label="GitHub public repository milestones">',
      '<defs><linearGradient id="panel" x1="0" x2="1" y1="0" y2="1"><stop stop-color="#140b20"/><stop offset="1" stop-color="#25102f"/></linearGradient></defs>',
      '<rect width="1120" height="290" rx="18" fill="url(#panel)"/>',
      '<rect x="1" y="1" width="1118" height="288" rx="18" fill="none" stroke="#ae388f" opacity=".75"/>',
      '<path d="M28 58H1092" stroke="#ad398f" opacity=".32"/>',
      label(30,40,'GITHUB / PUBLIC MILESTONES',23,'#ff75cf','700')]
    for i,(name,value,desc) in enumerate(rows):
      x=30+i*273
      out += [f'<rect x="{x}" y="81" width="254" height="150" rx="12" fill="#21152f" stroke="#6d2b6a"/>',
              f'<rect x="{x}" y="81" width="254" height="4" rx="2" fill="{["#fc66c9","#ad8cff","#45d3e3","#ff9ad8"][i]}"/>',
              label(x+17,115,name,16,'#cbb1da','700'),label(x+17,177,value,48,'#ffffff','700'),
              label(x+17,208,desc,13,'#9c90b5')]
    out += [label(30,267,'Auto-refreshed from public GitHub API  |  Not GitHub-awarded trophies  |  '+stamp,14,'#a99ab9'),'</svg>']
    return ''.join(out)

def main():
    profile=fetch(f'users/{USER}')
    if not isinstance(profile,dict) or 'followers' not in profile:
      raise RuntimeError('Invalid profile response; preserving previous image')
    repos=[]
    for page in range(1,51):
      part=fetch(f'users/{USER}/repos?type=owner&per_page=100&page={page}')
      if not isinstance(part,list): raise RuntimeError('Invalid repositories response')
      repos.extend(part)
      if len(part)<100: break
    else: raise RuntimeError('Pagination limit reached; preserving previous image')
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    svg=render(profile,repos,stamp)
    DEST.parent.mkdir(parents=True,exist_ok=True)
    temp=DEST.with_suffix('.svg.tmp')
    temp.write_text(svg,encoding='utf-8')
    temp.replace(DEST)
    print('Updated GitHub milestones panel from public API')

if __name__=='__main__': main()
