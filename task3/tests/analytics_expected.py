"""Independent raw-data oracle for new DAX, including stage/terrain/filter edges."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'data/model_data.json').read_text())
stages={r['Stage']:r for r in data['Stage']}
riders={r['Bib']:r for r in data['Rider']}
tests=[]
def add(name,measure,expected,filters=''):
    query=f'EVALUATE CALCULATETABLE(ROW("value",[{measure}]){","+filters if filters else ""})'
    tests.append(dict(name=name,query=query,expected=[dict(value=expected)]))
for sid in [1,6,7,21]:
    eligible={r['Bib']:r for r in data['Standing'] if r['Stage']==sid and r['Eligible']}
    for scenario in ['Official adjusted','No bonuses','No penalties','No bonuses or penalties']:
        scores={}
        for bib,row in eligible.items():
            rows=[r for r in data['Result'] if r['Bib']==bib and r['Stage']<=sid]
            scores[bib]=sum(r['Finish Seconds']-(0 if scenario in ['No bonuses','No bonuses or penalties'] else r['Bonus Seconds'])+(0 if scenario in ['No penalties','No bonuses or penalties'] else r['Penalty Seconds']) for r in rows)
        for bib in [1,8,21]:
            filt=f'TREATAS({{{bib}}},\'Rider\'[Bib]),TREATAS({{{sid}}},\'As Of\'[Stage]),TREATAS({{"{scenario}"}},\'Scenario\'[Scenario])'
            add(f'{scenario}: rank rider {bib} stage {sid}','Scenario GC Rank',1+sum(v<scores[bib] for v in scores.values()) if bib in scores else None,filt)
            add(f'{scenario}: time rider {bib} stage {sid}','Scenario Seconds',scores.get(bib),filt)
for team in ['Alpine Velo','Northstar Velo']:
    for terrain in ['Flat','Hilly','Mountain','Individual Time-Trial']:
        rows=[r for r in data['Result'] if riders[r['Bib']]['Team']==team and stages[r['Stage']]['Stage Type']==terrain]
        f=f'TREATAS({{"{team}"}},\'Rider\'[Team]),TREATAS({{"{terrain}"}},\'Stage\'[Stage Type])'
        add(f'Speed {team} {terrain}','Speed Proxy kmh',sum(stages[r['Stage']]['Distance km'] for r in rows)/sum(r['Finish Seconds'] for r in rows)*3600,f)
for bib in [1,8,21,58]:
    rows=[r for r in data['Result'] if r['Bib']==bib and stages[r['Stage']]['Stage Type']=='Mountain']
    gaps=[]
    for r in rows:
        winner=next(w for w in data['Result'] if w['Stage']==r['Stage'] and w['Position']==1)
        gaps.append(r['Adjusted Seconds']-winner['Adjusted Seconds'])
    f=f'TREATAS({{{bib}}},\'Rider\'[Bib])'
    add(f'Mountain podiums {bib}','Mountain Podiums',sum(r['Position']<=3 for r in rows),f)
    add(f'Mountain winner gaps {bib}','Mountain Mean Gap Seconds',sum(gaps)/len(gaps) if gaps else None,f)
    add(f'Top ten finishes {bib}','Top Ten Finishes',sum(r['Position']<=10 for r in data['Result'] if r['Bib']==bib),f)
    for sid in [1,7,9,21]:
        rows=[r for r in data['Standing'] if r['Bib']==bib and r['Stage']==sid]
        now=rows[0]['GC Rank']; prior=next((r['GC Rank'] for r in data['Standing'] if r['Bib']==bib and r['Stage']==sid-1),None)
        add(f'Rank change {bib} {sid}','GC Rank Change',prior-now if prior and now else None,f+f",TREATAS({{{sid}}},'Stage'[Stage])")
for country in ['France','Singapore','Colombia']:
    bibs={b for b,r in riders.items() if r['Rider Country']==country}
    rows=[r for r in data['Result'] if r['Bib'] in bibs]
    ranks=[r['GC Rank'] for r in data['Standing'] if r['Bib'] in bibs and r['Stage']==21 and r['GC Rank']]
    f=f'TREATAS({{"{country}"}},\'Country\'[Country])'
    add(f'National wins {country}','Country Wins',sum(r['Position']==1 for r in rows),f)
    add(f'National podiums {country}','Country Podiums',sum(r['Position']<=3 for r in rows),f)
    add(f'National best GC {country}','Country Best GC Rank',min(ranks) if ranks else None,f)
for sid in [6,9,21]:
    eligible={r['Bib']:r for r in data['Standing'] if r['Stage']==sid and r['Eligible']}
    mountain={b:sum(r['Adjusted Seconds'] for r in data['Result'] if r['Bib']==b and r['Stage']<=sid and stages[r['Stage']]['Stage Type']=='Mountain') for b in eligible}
    young={b:r['Cumulative Seconds'] for b,r in eligible.items() if riders[b]['Age at Race Start']<26}
    for bib in [1,2,8,21]:
        f=f'TREATAS({{{bib}}},\'Rider\'[Bib]),TREATAS({{{sid}}},\'As Of\'[Stage])'
        add(f'Mountain proxy rank {bib} {sid}','Mountain GC Proxy Rank',1+sum(v<mountain[bib] for v in mountain.values()) if bib in mountain and sid>=8 else None,f)
        add(f'Race-start young rank {bib} {sid}','Young GC at Race Start Rank',1+sum(v<young[bib] for v in young.values()) if bib in young else None,f)
for sid in [1,15]:
    for bib in [1,8,21,58]:
        r=next((r for r in data['Result'] if r['Stage']==sid and r['Bib']==bib),None)
        add(f'Top-ten-only result {bib} {sid}','Top Ten Position',r['Position'] if r and r['Position']<=10 else None,f'TREATAS({{{bib}}},\'Rider\'[Bib]),TREATAS({{{sid}}},\'Stage\'[Stage])')
# Verify the two calculations introduced by the merged, click-driven pages.
for nation in ['Hong Kong','Singapore','Japan']:
    scoped=[r for r in data['Result'] if riders[r['Bib']]['Rider Country']==nation]
    add('Overview rider-hours: '+nation,'Country Rider Hours',sum(r['Adjusted Seconds'] for r in scoped)/3600 if scoped else None,f'TREATAS({{"{nation}"}},\'Country\'[Country])')
for sid,stage in [(7,2),(7,8),(21,21)]:
    eligible={r['Bib'] for r in data['Standing'] if r['Stage']==sid and r['Eligible']}
    rows=[r for r in data['Result'] if r['Bib'] in eligible and r['Stage']==stage and stage<=sid]
    for mode in ['Official adjusted','No bonuses','No penalties','No bonuses or penalties']:
        value=sum((r['Penalty Seconds'] if mode in ['Official adjusted','No bonuses'] else 0)-(r['Bonus Seconds'] if mode in ['Official adjusted','No penalties'] else 0) for r in rows) if rows else None
        add(f'Waterfall: {mode}, checkpoint {sid}, day {stage}','Scenario Stage Adjustment Seconds',value,f'TREATAS({{{sid}}},\'As Of\'[Stage]),TREATAS({{{stage}}},\'Stage\'[Stage]),TREATAS({{"{mode}"}},\'Scenario\'[Scenario])')
for sid in [1,9,21]:
    for cat,col,score in [('General','GC Rank','Cumulative Seconds'),('Points','Points Rank','Points'),('Mountains','KOM Rank','KOM Points'),('Young Rider','Young Rank','Cumulative Seconds')]:
        leaders=[r for r in data['Standing'] if r['Stage']==sid and r[col]==1]
        total=leaders[0][score]
        names=', '.join(riders[r['Bib']]['Rider'] for r in sorted(leaders,key=lambda r:r['Bib']))
        pts=cat in ['Points','Mountains']
        if pts and total==0:names='Field tied on zero points'
        formatted=(f'{total} pts' if pts else f'{total//3600}:{total%3600//60:02d}:{total%60:02d}')
        filt=f'TREATAS({{{sid}}},\'As Of\'[Stage]),TREATAS({{"{cat}"}},\'Classification\'[Classification])'
        add(f'Award leaders / {cat} / {sid}','Award leaders',names,filt)
        add(f'Winning score / {cat} / {sid}','Winning score',formatted,filt)
for team in ['MSBA Breeze','Alpine Velo','Northstar Velo']:
    group=[r for r in data['Team Standing'] if r['Stage']==21]
    first=min((r for r in group if r['Team Rank']==1),key=lambda r:r['Team'])
    current=next(r for r in group if r['Team']==team)
    gap=round((current['Cumulative Top3 Seconds']-first['Cumulative Top3 Seconds'])/60,2) if current['Stages Scored']==first['Stages Scored'] else None
    add('Best Team time behind leader / '+team,'Team deficit minutes',gap,f'TREATAS({{"{team}"}},\'Team\'[Team])')
for sid,bib in [(1,61),(9,62),(21,1),(8,8)]:
    rows=[r for r in data['Standing'] if r['Stage']==sid and r['Eligible']]
    r=next((r for r in rows if r['Bib']==bib),None)
    gap=r['Cumulative Seconds']-min(x['Cumulative Seconds'] for x in rows) if r else None
    add(f'Daily GC gap / {bib} / {sid}','GC daily deficit seconds',gap,f'TREATAS({{{sid}}},\'Stage\'[Stage]),TREATAS({{{bib}}},\'Rider\'[Bib])')
for country,bib,val in [('Singapore',61,61),('Hong Kong',62,62),('Singapore',62,None),('Japan',61,None)]:
    add(f'Rider table bib / {country} / {bib}','Roster Bib',val,f'TREATAS({{"{country}"}},\'Country\'[Country]),TREATAS({{{bib}}},\'Rider\'[Bib])')
(ROOT/'tests/analytics_expected.json').write_text(json.dumps(tests,indent=2))
print(f'{len(tests)} independent analytics expectations')
