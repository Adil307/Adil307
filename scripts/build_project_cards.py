#!/usr/bin/env python3
"""Render premium SVG project cards from Adil307's public GitHub repository data.

No third-party images, no dependencies, no modification of README.md.
Public metadata only: primary language, stars, forks, most recent pushed_at.
Project descriptions and stack labels are editorial summaries of project README files.

Local test: python scripts/build_project_cards.py --fixture fixtures/repos.json
Production: GH_TOKEN=<GitHub Actions token> python scripts/build_project_cards.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

USER = 'Adil307'
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'assets'

PROJECTS = [
    {
        'slug': 'axiombraid', 'repo': 'AxiomBraid', 'name': 'AxiomBraid',
        'category': 'DATA QUALITY / OPEN SOURCE', 'index': '01',
        'desc': ('Explainable Python data quality,', 'validation, cleaning & drift detection.'),
        'tags': ('PYTHON', 'DATA QUALITY', 'VALIDATION'),
        'accent': '#ed4dcb', 'accent2': '#7c56ec', 'visual': 'data',
    },
    {
        'slug': 'rate-limiter', 'repo': 'Intelligent-API-Rate-Limiter', 'name': 'Intelligent API',
        'name2': 'Rate Limiter', 'category': 'BACKEND / SYSTEMS ENGINEERING', 'index': '02',
        'desc': ('Sliding-window limits with Redis,', 'FastAPI, concurrency and failure tests.'),
        'tags': ('PYTHON', 'FASTAPI', 'REDIS'),
        'accent': '#54d6ff', 'accent2': '#bf5bea', 'visual': 'rate',
    },
    {
        'slug': 'heatshield', 'repo': 'HeatShield-AI', 'name': 'HeatShield AI',
        'category': 'APPLIED AI / DECISION SYSTEMS', 'index': '03',
        'desc': ('Evidence-grounded urban heat', 'intelligence and controlled AI support.'),
        'tags': ('PYTHON', 'FASTAPI', 'APPLIED AI'),
        'accent': '#ff719e', 'accent2': '#a14df0', 'visual': 'heat',
    },
    {
        'slug': 'bgp', 'repo': 'BGP', 'name': 'BGP Operations',
        'name2': 'System', 'category': '.NET / ENTERPRISE SOFTWARE', 'index': '04',
        'desc': ('Project, contractor and inventory', 'operations built on ASP.NET Core.'),
        'tags': ('C#', 'ASP.NET CORE', 'SQL SERVER'),
        'accent': '#c490ff', 'accent2': '#4ac9f3', 'visual': 'operations',
    },
]

def esc(s):
    return escape(str(s), {'"': '&quot;', "'": '&apos;'})


def text(x, y, value, size=25, color='#f4edff', weight='400', anchor='start', tracking='0'):
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
            f'font-family="Arial, Helvetica, sans-serif" font-weight="{weight}" '
            f'letter-spacing="{tracking}" text-anchor="{anchor}">{esc(value)}</text>')


def shape_visual(kind, accent, alt):
    """Distinct illustrations are SVG paths, not source-claiming statistics."""
    if kind == 'data':
        return f'''<g transform="translate(675 105)">
<rect x="0" y="0" width="338" height="283" rx="28" fill="#1a1032" stroke="{accent}" stroke-opacity=".35"/>
<rect x="20" y="25" width="298" height="39" rx="10" fill="#2b1c44"/>{text(36,52,'DATA / PIPELINE',18,'#e7c4fb','700')}
<path d="M55 138 L156 102 L266 162" stroke="{alt}" stroke-width="6" fill="none" stroke-linecap="round"/>
<path d="M55 138 L151 203 L266 162" stroke="{accent}" stroke-width="4" opacity=".65" fill="none"/>
<circle cx="55" cy="138" r="25" fill="#251b49" stroke="{accent}" stroke-width="4"/>
<circle cx="156" cy="102" r="25" fill="#251b49" stroke="{alt}" stroke-width="4"/>
<circle cx="151" cy="203" r="25" fill="#251b49" stroke="{accent}" stroke-width="4"/>
<circle cx="266" cy="162" r="28" fill="#251b49" stroke="#f8a5eb" stroke-width="4"/>
<path d="M255 162 l8 8 l16 -20" fill="none" stroke="#a4ffcf" stroke-width="5" stroke-linecap="round"/>
{ text(28,263,'INSPECT → VALIDATE → MONITOR',15,'#bd9ed7','700') }
</g>'''
    if kind == 'rate':
        return f'''<g transform="translate(670 100)">
<rect width="345" height="296" rx="28" fill="#14172f" stroke="{accent}" stroke-opacity=".33"/>
{ text(26,42,'REQUEST POLICY',18,'#d5e6ff','700') }
<circle cx="173" cy="147" r="86" stroke="#33466a" stroke-width="18" fill="none"/>
<circle cx="173" cy="147" r="86" stroke="{accent}" stroke-width="18" fill="none" stroke-dasharray="403 541" stroke-linecap="round" transform="rotate(-90 173 147)"/>
<circle cx="173" cy="147" r="64" fill="#111a34"/>
{ text(173,145,'100',64,'#ecfaff','700','middle') }
{ text(173,179,'REQ / 60s',18,'#89c6e7','700','middle') }
<rect x="37" y="249" width="100" height="29" rx="8" fill="#174e55"/>
{ text(87,269,'HTTP 200',15,'#9ce7e3','700','middle') }
<rect x="205" y="249" width="100" height="29" rx="8" fill="#5a2e52"/>
{ text(255,269,'HTTP 429',15,'#ffd1e7','700','middle') }
</g>'''
    if kind == 'heat':
        towers = ''.join(f'<rect x="{23+i*49}" y="{205-h}" width="34" height="{h}" rx="3" fill="{["#4e2b69","#713270","#a93b7d","#dc4f93","#9f3779","#6c336c"][i]}" opacity=".91"/>' for i,h in enumerate([82,130,170,118,205,152]))
        return f'''<g transform="translate(677 99)">
<rect width="336" height="296" rx="28" fill="#20102e" stroke="{accent}" stroke-opacity=".32"/>
{ text(24,42,'URBAN THERMAL MAP',18,'#ffd5e9','700') }
<path d="M12 240 Q86 146 160 220 T330 175" fill="none" stroke="{accent}" stroke-width="2" opacity=".65"/>
{towers}
<path d="M18 206 H316" stroke="#ee82b9" opacity=".45"/>
<path d="M50 120 Q100 52 156 110 T276 95" fill="none" stroke="#ffbb70" stroke-width="4" stroke-dasharray="8 10"/>
<circle cx="157" cy="111" r="12" fill="#ffe1a4" stroke="#ff6a91" stroke-width="7"/>
<rect x="24" y="242" width="285" height="32" rx="10" fill="#3b203e"/>
{ text(166,264,'EVIDENCE → PRIORITY',16,'#ffcee6','700','middle') }
</g>'''
    return f'''<g transform="translate(674 100)">
<rect width="339" height="295" rx="28" fill="#17182d" stroke="{accent}" stroke-opacity=".35"/>
{ text(24,42,'OPERATIONS CONSOLE',18,'#e9d9ff','700') }
<rect x="20" y="62" width="297" height="196" rx="13" fill="#0d1527" stroke="#364064"/>
<rect x="38" y="84" width="96" height="23" rx="6" fill="#49386f"/>
{ text(53,101,'PROJECTS',15,'#ffffff','700') }
<rect x="148" y="84" width="149" height="23" rx="6" fill="#223b59"/>
<path d="M38 124 H290 M38 166 H290 M38 208 H290" stroke="#3b425c" stroke-width="2"/>
<path d="M112 122 V239 M205 122 V239" stroke="#3b425c" stroke-width="2"/>
{ text(53,152,'INV-1024',16,'#c3d6ff') }
{ text(53,194,'INV-1025',16,'#c3d6ff') }
{ text(53,236,'INV-1026',16,'#c3d6ff') }
<rect x="218" y="136" width="62" height="20" rx="5" fill="#1b645d"/>
<rect x="218" y="178" width="62" height="20" rx="5" fill="#64435f"/>
<rect x="218" y="220" width="62" height="20" rx="5" fill="#1b645d"/>
{ text(169,281,'INVENTORY  /  JOBS  /  REPORTS',15,'#abadd9','700','middle') }
</g>'''


def render(p, data, stamp):
    name = p['name']; name2 = p.get('name2')
    accent = p['accent']; alt = p['accent2']
    lang = data.get('language') or 'Not specified'
    stars = int(data['stargazers_count'])
    forks = int(data['forks_count'])
    # pushed_at reflects code pushes, unlike updated_at (which also changes on star activity)
    pushed = str(data['pushed_at'])[:10]
    title_y = 152
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1060" height="550" viewBox="0 0 1060 550" role="img" aria-label="{esc(name)} public GitHub metrics">',
         '<defs>',
         '<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#100b20"/><stop offset=".58" stop-color="#191130"/><stop offset="1" stop-color="#180d29"/></linearGradient>',
         f'<linearGradient id="glow" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{accent}" stop-opacity=".28"/><stop offset="1" stop-color="{alt}" stop-opacity="0"/></linearGradient>',
         '</defs>',
         '<rect x="2" y="2" width="1056" height="546" rx="30" fill="url(#bg)" stroke="#623a72" stroke-width="3"/>',
         '<rect x="3" y="3" width="1054" height="10" rx="5" fill="'+accent+'"/>',
         '<circle cx="892" cy="125" r="227" fill="url(#glow)"/>',
         '<path d="M0 413 Q140 356 285 418 T570 411 T1060 393" fill="none" stroke="'+alt+'" stroke-width="3" opacity=".36"/>',
         '<path d="M0 442 Q180 397 327 436 T633 442 T1060 426" fill="none" stroke="'+accent+'" stroke-width="2" opacity=".18"/>',
         '<g stroke="#633c79" opacity=".22" stroke-width="1">']
    for i in range(40,1060,45): o.append(f'<path d="M{i} 0V545"/>')
    for i in range(35,545,45): o.append(f'<path d="M0 {i}H1060"/>')
    o+=['</g>', f'<rect x="30" y="37" width="482" height="41" rx="15" fill="{accent}" fill-opacity=".13" stroke="{accent}" stroke-opacity=".44"/>',
        text(49,64, f'{p["index"]}  /  {p["category"]}',19, '#f3dfff','700',tracking='1'),
        text(35,title_y,name,47,'#fff7ff','700',tracking='-.8')]
    if name2: o.append(text(35,205,name2,47,'#fff7ff','700',tracking='-.8'))
    desc_y=255 if name2 else 213
    for k,line in enumerate(p['desc']): o.append(text(37,desc_y+k*34,line,27,'#c8b5db','400'))
    tag_y = 348
    xx=37
    for tag in p['tags']:
        width=25+len(tag)*14.8
        o += [f'<rect x="{xx}" y="{tag_y}" width="{width:.0f}" height="40" rx="12" fill="#382342" stroke="{accent}" stroke-opacity=".28"/>',text(xx+13,tag_y+27,tag,18,'#ecd6ef','700')]
        xx += width+12
    o.append(shape_visual(p['visual'],accent,alt))
    # visual separation, live metadata bar
    o+= ['<rect x="25" y="453" width="1010" height="74" rx="15" fill="#120c23" stroke="#4a315e"/>',
         f'<circle cx="54" cy="489" r="7" fill="{accent}"/>',
         text(74,493, f'{lang.upper()}  •  PRIMARY LANGUAGE',20,'#dfd0ec','700'),
         text(480,493,f'{stars} STARS',21,'#fff0fc','700'),
         text(666,493,f'{forks} FORKS',21,'#fff0fc','700'),
         text(865,482,'LAST PUSH',14,'#a891ba','700'),
         text(865,509,pushed,21,'#fff0fc','700'),
         text(34,428,'VIEW REPOSITORY  >',18,accent,'700',tracking='1'),
         text(1014,428,'AUTO-REFRESHED / GITHUB',13,'#88769c','700',anchor='end'),
         '</svg>']
    return ''.join(o)


def fetch_repo(name):
    hdr={'User-Agent':'Adil307-premium-project-cards','Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
    if os.getenv('GH_TOKEN'): hdr['Authorization'] = 'Bearer '+os.environ['GH_TOKEN']
    req=Request('https://api.github.com/repos/'+USER+'/'+name,headers=hdr)
    with urlopen(req,timeout=25) as h:
        return json.load(h)


def validate(data, expected):
    if not isinstance(data,dict) or data.get('name') != expected or data.get('private') is not False:
        raise ValueError(f'Missing/incorrect/nonpublic repository payload: {expected}')
    for key in ('stargazers_count','forks_count','pushed_at','language','html_url'):
        if key not in data:
            raise ValueError(f'Missing {key} in {expected}')
    if (not isinstance(data['stargazers_count'],int) or not isinstance(data['forks_count'],int) or
         not isinstance(data['pushed_at'],str) or
         not re.fullmatch(r'\d{4}-\d{2}-\d{2}T.*',data['pushed_at']) or
         data['html_url'] != f'https://github.com/{USER}/{expected}'):
         raise ValueError(f'Invalid GitHub metadata for {expected}')


def main():
    arg=argparse.ArgumentParser()
    arg.add_argument('--fixture',type=Path,help='Offline JSON for tests; NOT used by Actions')
    arg.add_argument('--out',type=Path,default=OUTPUT)
    ns=arg.parse_args()
    fixture=json.loads(ns.fixture.read_text(encoding='utf-8')) if ns.fixture else None
    payload={}
    for p in PROJECTS:
        item=(fixture.get(p['repo']) if fixture is not None else fetch_repo(p['repo']))
        validate(item,p['repo'])
        payload[p['slug']]=item
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    rendered={f'project-live-{p["slug"]}.svg':render(p,payload[p['slug']],stamp) for p in PROJECTS}
    # Validate all SVGs before writing any, keep last known good assets during outages.
    import xml.etree.ElementTree as ET
    for filename,svg in rendered.items():
        ET.fromstring(svg)
    ns.out.mkdir(parents=True,exist_ok=True)
    for filename,svg in rendered.items():
        target=ns.out/filename
        with tempfile.NamedTemporaryFile('w',encoding='utf-8',delete=False,dir=ns.out,suffix='.tmp') as tf:
            tf.write(svg)
            staging=Path(tf.name)
        os.replace(staging,target)
    print('SUCCESS: 4 public repo cards generated; stars, forks, language and last-push dates are real GitHub data')

if __name__=='__main__':
    main()
