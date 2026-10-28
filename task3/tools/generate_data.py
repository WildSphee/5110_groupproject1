"""Deterministic fictional race; regenerate from this file, never represent as real TdF results."""
from pathlib import Path
from datetime import date, timedelta
import csv, json, random

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'

def rank_map(items, key):
    ordered = sorted(items, key=key)
    ranks, previous, rank = {}, None, 0
    for index, item in enumerate(ordered, 1):
        value = key(item)
        if value != previous: rank = index
        ranks[item['bib_no'] if 'bib_no' in item else item['team_name']] = rank
        previous = value
    return ranks

def rider_snapshot(rider, results, score, exit_at, stages, sid):
    """Historical eligibility uses the stage set, not arithmetic on stage IDs."""
    b=rider['bib_no']
    required={s['stage_id'] for s in stages if s['stage_id']<=sid}
    rows=[r for r in results if r['bib_no']==b and r['stage_id']<=sid]
    exited=exit_at.get(b,float('inf'))<=sid
    eligible={r['stage_id'] for r in rows}==required and not exited
    return dict(bib_no=b,stage_id=sid,eligible=int(eligible),young=int(rider['dob']>='2001-01-01'),
        cumulative_seconds=sum(r['finish_time']-r['bonus']+r['time_penalty'] for r in rows),
        points=sum(score[b,r['stage_id']]['points'] for r in rows),
        kom_points=sum(score[b,r['stage_id']]['kom_points'] for r in rows),stages_completed=len(rows),
        status='Eligible' if eligible else 'Exited' if exited else 'Incomplete results')

def build():
    rng = random.Random(5110)
    countries = [dict(country_code=c, country_name=n) for c,n in [
        ('FRA','France'),('ESP','Spain'),('ITA','Italy'),('BEL','Belgium'),('NLD','Netherlands'),
        ('GBR','United Kingdom'),('DEU','Germany'),('DNK','Denmark'),('AUS','Australia'),
        ('COL','Colombia'),('SGP','Singapore'),('JPN','Japan')]]
    names = {c['country_code']:c['country_name'] for c in countries}
    teams = [dict(team_name=n,country_code=c) for n,c in [
        ('Alpine Velo','FRA'),('Atlantic Racing','FRA'),('Iberia Wheels','ESP'),
        ('Azzurro Cycling','ITA'),('Lowland Sprint','BEL'),('Northstar Velo','NLD')]]
    first=['Alex','Morgan','Robin','Sam','Taylor','Jamie','Casey','Avery']
    last=['Laurent','Moreau','Sierra','Bianchi','Vanden','Berg']
    riders=[]
    for t,team in enumerate(teams):
        for i in range(8):
            bib=t*10+i+1
            born=date(2002 if i in [0,3,6] else 1993+(i%5),1+(i*2)%12,1+i)
            riders.append(dict(bib_no=bib,rider_name=f'{first[i]} {last[t]}',dob=born.isoformat(),
                is_leader=i==0,team_name=team['team_name'],country_code=countries[(t+i*3)%10]['country_code']))
    places=['Lille','Amiens','Rouen','Caen','Rennes','Nantes','Tours','Limoges','Bordeaux','Pau','Tarbes',
            'Foix','Carcassonne','Montpellier','Nimes','Valence','Grenoble','Annecy','Chambery','Dijon','Paris','Versailles']
    locations=[dict(location_name=n,country_code='FRA') for n in places]
    types=['flat','flat','hilly','flat','individual time-trial','hilly','flat','mountain','mountain','flat','hilly',
           'mountain','flat','hilly','mountain','mountain','flat','mountain','individual time-trial','hilly','flat']
    stages=[]
    for i,kind in enumerate(types,1):
        km=round(28.5+i/3 if kind=='individual time-trial' else 145+(i*17)%65,1)
        stages.append(dict(stage_id=i,stage_date=(date(2026,7,4)+timedelta(days=i-1+(i>9)+(i>16))).isoformat(),
            distance_km=km,stage_type=kind,start_location=places[i-1],end_location=places[i]))
    # The last team intentionally falls below 3 finishers after stage 18.
    exits=[dict(bib_no=b,stage_id=s,exit_reason=r) for b,s,r in [
        (8,7,'Illness'),(27,12,'Injury'),(53,10,'Illness'),(54,13,'Injury'),
        (55,15,'Fatigue'),(56,16,'Illness'),(57,17,'Injury'),(58,18,'Fatigue')]]
    exit_at={e['bib_no']:e['stage_id'] for e in exits}
    results=[]; scores=[]
    for st in stages:
        sid=st['stage_id']; kind=st['stage_type']; rows=[]
        for r in riders:
            b=r['bib_no']; role=(b-1)%10
            if exit_at.get(b,999)<=sid: continue
            pace={'flat':43,'hilly':39,'mountain':32,'individual time-trial':47}[kind]
            ability=role*28 if kind in ['mountain','individual time-trial'] else abs(role-2)*7
            elapsed=round(st['distance_km']/pace*3600)+ability+rng.randint(0,100)+(b//10)*13
            if kind=='flat': elapsed=(elapsed//15)*15  # real equal finish times, unique positions
            rows.append(dict(bib_no=b,stage_id=sid,finish_time=elapsed,bonus=0,time_penalty=30 if (b+sid)%43==0 else 0))
        rows.sort(key=lambda r:(r['finish_time'],r['bib_no']))
        for pos,r in enumerate(rows,1):
            r['position']=pos
            r['bonus']=[10,6,4][pos-1] if pos<=3 and kind!='individual time-trial' else 0
            results.append(r)
            p=[50,30,20,18,16,14,12,10,8,6] if kind=='flat' else [25,20,16,12,10,8,6,4,2,1]
            scores.append(dict(bib_no=r['bib_no'],stage_id=sid,points=p[pos-1] if pos<=10 else 0,
                kom_points=([10,8,6,4,2,1][pos-1] if pos<=6 and kind=='mountain' else 0)))
    by_bib={r['bib_no']:r for r in riders}; score={(r['bib_no'],r['stage_id']):r for r in scores}
    standings=[]; team_stage=[]; team_standing=[]
    for st in stages:
        sid=st['stage_id']; current=[]
        for rider in riders:
            current.append(rider_snapshot(rider,results,score,exit_at,stages,sid))
        eligible=[r for r in current if r['eligible']]
        gc=rank_map(eligible,lambda r:r['cumulative_seconds']); pr=rank_map(eligible,lambda r:-r['points'])
        kr=rank_map(eligible,lambda r:-r['kom_points']); yr=rank_map([r for r in eligible if r['young']],lambda r:r['cumulative_seconds'])
        for r in current:
            b=r['bib_no']; r.update(gc_rank=gc.get(b),points_rank=pr.get(b),kom_rank=kr.get(b),young_rank=yr.get(b))
            standings.append(r)
        for team in teams:
            rows=[r for r in results if r['stage_id']==sid and by_bib[r['bib_no']]['team_name']==team['team_name']]
            fastest=sorted(rows,key=lambda r:(r['finish_time']-r['bonus']+r['time_penalty'],r['bib_no']))[:3]
            team_stage.append(dict(team_name=team['team_name'],stage_id=sid,finishers=len(rows),
                top3_seconds=sum(r['finish_time']-r['bonus']+r['time_penalty'] for r in fastest) if len(fastest)==3 else None))
        group=[]
        for team in teams:
            scored=[r for r in team_stage if r['team_name']==team['team_name'] and r['top3_seconds'] is not None]
            group.append(dict(team_name=team['team_name'],stage_id=sid,stages_scored=len(scored),
                cumulative_top3_seconds=sum(r['top3_seconds'] for r in scored),
                coverage='Complete' if len(scored)==sum(s['stage_id']<=sid for s in stages) else 'Incomplete'))
        ranks=rank_map(group,lambda r:(-r['stages_scored'],r['cumulative_top3_seconds']))
        for r in group:r['team_rank']=ranks[r['team_name']];team_standing.append(r)
    normalized={'country':countries,'team':teams,'rider':riders,'location':locations,'stage':stages,'result':results,'exit':exits,
        'classification_score':scores,'standing_snapshot':standings,'team_stage':team_stage,'team_snapshot':team_standing}
    for name,rows in normalized.items():
        with (DATA/(name+'.csv')).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    tc={r['team_name']:names[r['country_code']] for r in teams}
    tables={
        'Country':[{'Country Code':r['country_code'],'Country':r['country_name']} for r in countries],
        'Team':[{'Team':r['team_name'],'Team Country':names[r['country_code']]} for r in teams],
        'Rider':[{'Bib':r['bib_no'],'Rider':r['rider_name'],'Rider Label':f"{r['rider_name']} ({r['bib_no']})",'Team':r['team_name'],
            'Rider Country':names[r['country_code']],'Team Country':tc[r['team_name']],'DOB':r['dob'],
            'Young Rider':int(r['dob']>='2001-01-01'),'Leader':int(r['is_leader']), 'Exit Stage':exit_at.get(r['bib_no']),
            'Exit Reason':next((e['exit_reason'] for e in exits if e['bib_no']==r['bib_no']),'None')} for r in riders],
        'Stage':[{'Stage':r['stage_id'],'Stage Label':f"{r['stage_id']:02d} | {r['start_location']} - {r['end_location']}",
            'Stage Type':r['stage_type'].title(),'Date':r['stage_date'],'Distance km':r['distance_km']} for r in stages],
        'As Of':[{'Stage':r['stage_id'],'As of Stage':f"Stage {r['stage_id']:02d}"} for r in stages],
        'Result':[{'Bib':r['bib_no'],'Stage':r['stage_id'],'Position':r['position'],'Finish Seconds':r['finish_time'],
            'Bonus Seconds':r['bonus'],'Penalty Seconds':r['time_penalty'],
            'Adjusted Seconds':r['finish_time']-r['bonus']+r['time_penalty'],
            'Points':score[r['bib_no'],r['stage_id']]['points'],'KOM Points':score[r['bib_no'],r['stage_id']]['kom_points']} for r in results],
        'Standing':[dict(zip(['Bib','Stage','Eligible','Young','Cumulative Seconds','Points','KOM Points','Stages Completed','Status','GC Rank','Points Rank','KOM Rank','Young Rank'],r.values())) for r in standings],
        'Team Stage':[{'Team':r['team_name'],'Stage':r['stage_id'],'Finishers':r['finishers'],'Top3 Seconds':r['top3_seconds']} for r in team_stage],
        'Team Standing':[{'Team':r['team_name'],'Stage':r['stage_id'],'Stages Scored':r['stages_scored'],
            'Cumulative Top3 Seconds':r['cumulative_top3_seconds'],'Coverage':r['coverage'],'Team Rank':r['team_rank']} for r in team_standing],
        'Classification':[{'Classification':n,'Order':i} for i,n in enumerate(['General','Points','Mountains','Young Rider'],1)]}
    (DATA/'model_data.json').write_text(json.dumps(tables,indent=2),encoding='utf-8')
    print(json.dumps({name:len(rows) for name,rows in tables.items()}))

if __name__=='__main__':
    DATA.mkdir(exist_ok=True,parents=True);build()
    from extend_analytics import extend
    extend()
