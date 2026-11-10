"""Import the group's PostgreSQL CSV export and build a portable Power BI import model.

No generated race results or external connections. Run from any directory with Python 3.10+.
"""
from __future__ import annotations
import csv
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path
from extend_analytics import analytics_definitions

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'use_this_data/export/csv'
DATA = ROOT / 'data'
MODEL = ROOT / 'Tour de France.SemanticModel/definition'

def read(name):
    with (SOURCE / (name+'.csv')).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def write_json(file, value):
    file.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

def ranks(values):
    """Competition rank, including ties, on a scalar or compound sort key."""
    order=sorted(values,key=values.get)
    result={}
    for i,k in enumerate(order):
        if i==0 or values[k]!=values[order[i-1]]:rank=i+1
        result[k]=rank
    return result

def duration(sec):
    return f'{sec//3600}:{sec%3600//60:02d}:{sec%60:02d}'

def build():
    countries=read('country'); teams=read('team'); riders=read('rider'); stages=sorted(read('stage'),key=lambda s:int(s['stage_id']))
    registered={r['country_code']:r['country_name'] for r in countries}
    team_country={t['team_name']:registered[t['country_code']] for t in teams}
    exits={int(e['bib_no']):e for e in read('exit')}
    ids=[int(s['stage_id']) for s in stages]
    race_start=date.fromisoformat(stages[0]['stage_date'])
    cutoff=date(race_start.year-25,1,1)
    rider_dim=[]
    for r in riders:
        b=int(r['bib_no']); dob=date.fromisoformat(r['dob']); e=exits.get(b)
        rider_dim.append({'Bib':b,'Rider':r['rider_name'],'Rider Label':f"{r['rider_name']} ({b})",
            'Team':r['team_name'],'Rider Country':registered[r['country_code']] if r['country_code'] else 'Unknown',
            'Team Country':team_country[r['team_name']],'DOB':r['dob'],'Young Rider':int(dob>=cutoff),
            'Leader':int(r['is_leader']=='t'),'Exit Stage':int(e['stage_id']) if e else None,
            'Exit Reason':e['exit_reason'] if e else 'None',
            'Age at Race Start':race_start.year-dob.year-((race_start.month,race_start.day)<(dob.month,dob.day))})
    by_bib={r['Bib']:r for r in rider_dim}
    stage_dim=[{'Stage':int(s['stage_id']),'Stage Label':f"{int(s['stage_id']):02d} | {s['start_location']} - {s['end_location']}",
        'Stage Type':s['stage_type'].title(),'Date':s['stage_date'],'Distance km':float(s['distance_km']),
        'Start':s['start_location'],'Finish':s['end_location']} for s in stages]
    result=[]; by_stage=defaultdict(list);seen=set()
    for r in read('result'):
        b,s=int(r['bib_no']),int(r['stage_id'])
        if (b,s) in seen or b not in by_bib or s not in ids or (b in exits and s>=int(exits[b]['stage_id'])):
            raise ValueError(f'Invalid result bib={b} stage={s}')
        seen.add((b,s));finish,bonus,penalty=map(int,[r['finish_time'],r['bonus'],r['time_penalty']])
        v={'Bib':b,'Stage':s,'Position':int(r['position']),'Finish Seconds':finish,'Bonus Seconds':bonus,
           'Penalty Seconds':penalty,'Adjusted Seconds':finish-bonus+penalty,'Points':None,'KOM Points':None}
        result.append(v);by_stage[s].append(v)
    standings=[];team_stage=[];team_history=[]
    counts=defaultdict(int);times=defaultdict(int);scored=defaultdict(int);team_seconds=defaultdict(int)
    for idx,s in enumerate(ids,1):
        daily=defaultdict(list)
        for v in by_stage[s]:
            b=v['Bib'];counts[b]+=1;times[b]+=v['Adjusted Seconds'];daily[by_bib[b]['Team']].append(v['Adjusted Seconds'])
        elig={b:times[b] for b,r in by_bib.items() if counts[b]==idx and (r['Exit Stage'] is None or r['Exit Stage']>s)}
        gc=ranks(elig);young=ranks({b:t for b,t in elig.items() if by_bib[b]['Young Rider']})
        for b,r in by_bib.items():
            exited=r['Exit Stage'] is not None and r['Exit Stage']<=s
            standings.append({'Bib':b,'Stage':s,'Eligible':int(b in elig),'Young':r['Young Rider'],'Cumulative Seconds':times[b],
                'Points':None,'KOM Points':None,'Stages Completed':counts[b],'Status':'Eligible' if b in elig else 'Exited' if exited else 'Incomplete results',
                'GC Rank':gc.get(b),'Points Rank':None,'KOM Rank':None,'Young Rank':young.get(b)})
        for team in team_country:
            finishes=sorted(daily[team]);total=sum(finishes[:3]) if len(finishes)>=3 else None
            if total is not None:scored[team]+=1;team_seconds[team]+=total
            team_stage.append({'Team':team,'Stage':s,'Finishers':len(finishes),'Top3 Seconds':total})
        team_rank=ranks({t:(-scored[t],team_seconds[t]) for t in team_country if scored[t]})
        for t in team_country:
            team_history.append({'Team':t,'Stage':s,'Stages Scored':scored[t],'Cumulative Top3 Seconds':team_seconds[t] if scored[t] else None,
                'Coverage':'Complete' if scored[t]==idx else 'Incomplete','Team Rank':team_rank.get(t)})
    lookup={(v['Bib'],v['Stage']):v for v in standings}
    # Reference the actual winning adjusted total, not a predicted finishing time.
    winning_seconds=min(v['Cumulative Seconds'] for v in standings if v['Stage']==ids[-1] and v['GC Rank']==1)
    withdrawals=[]
    for b,e in sorted(exits.items()):
        s=int(e['stage_id']);earlier=[k for k in ids if k<s and (b,k) in seen]
        prev=lookup[b,earlier[-1]] if earlier else None
        t=prev['Cumulative Seconds'] if prev else 0;remaining=len(ids)-len(earlier)
        budget=winning_seconds-t
        withdrawals.append({'Bib':b,'Stage':s,'Rider':by_bib[b]['Rider'],'Team':by_bib[b]['Team'],'Exit type':e['exit_reason'],
          'Previous stage':earlier[-1] if earlier else None,'Previous GC rank':prev['GC Rank'] if prev else None,
          'Completed seconds':t,'Stages left':remaining,'Budget seconds':budget,'Time to match winner':duration(budget),
          'Avg required per stage':duration(round(budget/remaining))})
    return {'Country':[{'Country Code':r['country_code'],'Country':r['country_name']} for r in countries]+[{'Country Code':None,'Country':'Unknown'}],
        'Team':[{'Team':t,'Team Country':c} for t,c in team_country.items()],'Rider':rider_dim,'Stage':stage_dim,
        'Stage choice':[{'Choice':choice,'Stage':s,'Order':order} for s in ids for choice,order in [('All',0),(f'{s:02d}',s)]],
        'As Of':[{'Stage':s,'As of Stage':f'Stage {s:02d}'} for s in ids],'Result':result,'Standing':standings,
        'Team Stage':team_stage,'Team Standing':team_history,'Withdrawal':withdrawals,
        'Jersey Leaders':json.loads((DATA/'jersey_leaders.json').read_text(encoding='utf8')),
        'Classification':[{'Classification':c,'Order':i} for i,c in enumerate(['General','Points','Mountains','Young Rider'],1)],
        'Scenario':[{'Scenario':v} for v in ['Official adjusted','No bonuses','No penalties','No bonuses or penalties']]}

def reconcile(tables):
    final=max(r['Stage'] for r in tables['Stage'])
    final_rows=[r for r in tables['Standing'] if r['Stage']==final]
    for view,rank_field,source_rank in [('v_general_classification','GC Rank','gc_rank'),('v_young_rider_classification','Young Rank','young_rank')]:
        reference={int(r['bib_no']):(int(r[source_rank]),int(r['total_adjusted_time'])) for r in read(view)}
        actual={r['Bib']:(r[rank_field],r['Cumulative Seconds']) for r in final_rows if r[rank_field] is not None}
        if actual!=reference:raise ValueError(f'{view} mismatch')
    teams={r['Team']:(r['Team Rank'],r['Stages Scored'],r['Cumulative Top3 Seconds']) for r in tables['Team Standing'] if r['Stage']==final and r['Team Rank']}
    if teams!={r['team_name']:(int(r['team_rank']),int(r['stages_scored']),int(r['total_top3_time'])) for r in read('v_best_team')}:raise ValueError('Best Team mismatch')
    if {(r['Bib'],r['Stage']):r['Adjusted Seconds'] for r in tables['Result']}!={(int(r['bib_no']),int(r['stage_id'])):int(r['adjusted_time']) for r in read('v_result_adjusted')}:
        raise ValueError('Adjusted result mismatch')

def embed_model(tables):
    for name,rows in tables.items():
        file=MODEL/'tables'/f'{name}.tmdl'
        cols=list(rows[0])
        types={}
        for col in cols:
            v=next((r[col] for r in rows if r[col] is not None),None)
            types[col]='string' if isinstance(v,str) else 'double' if isinstance(v,float) else 'int64'
        existing=file.read_text(encoding='utf8') if file.exists() else ''
        if existing:
            prefix=existing[:existing.index('\t\tsource =')]
            prefix=re.sub(r'\A///[^\n]*\n','',prefix)
        else:
            prefix="table '"+name+"'\n\n"+''.join(f"\tcolumn '{col}'\n\t\tdataType: {types[col]}\n\t\tsummarizeBy: none\n\t\tsourceColumn: {col}\n\n" for col in cols)+f"\tpartition '{name}' = m\n\t\tmode: import\n"
        if name=='Stage choice' and 'sortByColumn:' not in prefix:
            prefix=prefix.replace("sourceColumn: Choice","sourceColumn: Choice\n\t\tsortByColumn: Order")
        def literal(v):return 'null' if v is None else '"'+v.replace('"','""')+'"' if isinstance(v,str) else str(v)
        ms={'string':'nullable text','double':'number','int64':'Int64.Type'}
        m='let Source = #table(type table ['+', '.join(f'#"{c}" = '+ms[types[c]] for c in cols)+'], {\n'+',\n'.join('{'+','.join(literal(r[c]) for c in cols)+'}' for r in rows)+'\n}) in Source'
        file.write_text(prefix+'\t\tsource =\n'+''.join('\t'*4+l+'\n' for l in m.splitlines()),encoding='utf8',newline='\n')
    p=MODEL/'model.tmdl';s=p.read_text(encoding='utf8')
    if 'ref table Withdrawal' not in s:p.write_text(s.replace('ref table Scenario','ref table Scenario\nref table Withdrawal'),encoding='utf8')
    p=MODEL/'model.tmdl';s=p.read_text(encoding='utf8')
    if "ref table 'Stage choice'" not in s:
        p.write_text(s.replace('ref table Stage\n',"ref table Stage\nref table 'Stage choice'\n"),encoding='utf8')
    p=MODEL/'model.tmdl';s=p.read_text(encoding='utf8')
    if "ref table 'Jersey Leaders'" not in s:
        p.write_text(s.rstrip()+"\nref table 'Jersey Leaders'\n",encoding='utf8')
    p=MODEL/'relationships.tmdl';s=p.read_text(encoding='utf8')
    if 'relationship StageChoice_Stage' not in s:
        s+="\nrelationship StageChoice_Stage\n\tcrossFilteringBehavior: bothDirections\n\tfromColumn: 'Stage choice'.Stage\n\ttoColumn: Stage.Stage\n"
    for dim,key in [('Stage','Stage'),('Rider','Bib')]:
        if f'Withdrawal_{dim}' not in s:s+=f'\nrelationship Withdrawal_{dim}\n\tfromColumn: Withdrawal.{key}\n\ttoColumn: {dim}.{key}\n'
    p.write_text(s.rstrip()+'\n',encoding='utf8',newline='\n')

def sync_measures():
    old=json.loads((DATA/'measures.json').read_text(encoding='utf8'));extra=analytics_definitions()
    names={m['name'] for m in extra}
    measures=[m for m in old if m['name'] not in names]+extra
    # Unknown nationality participates in registered totals, but is not a represented country.
    for m in measures:
        if m['name']=='Classification Rider Hours':m['expression']='SWITCH(SELECTEDVALUE(\'Classification\'[Classification]),"General",[Eligible Cumulative Hours],"Young Rider",CALCULATE([Eligible Cumulative Hours],\'Rider\'[Young Rider]=1))'
        if m['name']=='Countries Represented':m['expression']='COUNTROWS(FILTER(ALL(\'Country\'),\'Country\'[Country]<>"Unknown" && [Teams by Country]+[Riders by Country]>0))'
        if m['name']=='Foreign Team Riders':m['expression']='COUNTROWS(FILTER(\'Rider\',\'Rider\'[Rider Country]<>"Unknown" && \'Rider\'[Rider Country]<>\'Rider\'[Team Country]))'
    write_json(DATA/'analytics_measures.json',extra);write_json(DATA/'measures.json',measures)
    file=MODEL/'tables/Metrics.tmdl';s=file.read_text(encoding='utf8');header=s[s.index('table Metrics'):s.index('\n\t///')]
    col=s[s.index('\n\tcolumn '):]
    lineage={}
    for match in re.finditer(r"^\tmeasure (?:'([^']+)'|(\w+)) = [^\n]*(?:\n\t\t[^\n]*)*",s,re.M):
        tag=re.search(r'\n\t\tlineageTag: ([^\n]+)',match[0])
        if tag:lineage[match[1] or match[2]]=tag[1]
    blocks=[]
    for m in measures:
        n=m['name'];b=f"\t/// {m['description']}\n\tmeasure '{n}' = {m['expression']}\n"
        if m.get('formatString'):b+='\t\tformatString: '+m['formatString']+'\n'
        b+='\t\tdisplayFolder: '+m['displayFolder']+'\n'
        if n in lineage:b+='\t\tlineageTag: '+lineage[n]+'\n'
        blocks.append(b)
    file.write_text(header.rstrip()+'\n\n'+'\n'.join(blocks)+col.rstrip()+'\n',encoding='utf8',newline='\n')

if __name__=='__main__':
    tables=build();reconcile(tables)
    write_json(DATA/'model_data.json',tables);embed_model(tables);sync_measures()
    print('All four exported views reconciled.',{t:len(r) for t,r in tables.items()})
