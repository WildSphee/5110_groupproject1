"""PDF E1–E15 extensions; portable embedded tables and reproducible DAX definitions."""
import csv
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'

def extend():
    tables = json.loads((DATA/'model_data.json').read_text(encoding='utf-8'))
    stages = {int(r['stage_id']): r for r in csv.DictReader((DATA/'stage.csv').open())}
    race_start = min(date.fromisoformat(r['stage_date']) for r in stages.values())
    for row in tables['Stage']:
        row['Start'] = stages[row['Stage']]['start_location']
        row['Finish'] = stages[row['Stage']]['end_location']
    for row in tables['Rider']:
        dob = date.fromisoformat(row['DOB'])
        row['Age at Race Start'] = race_start.year-dob.year-((race_start.month,race_start.day)<(dob.month,dob.day))
    tables['Scenario'] = [{'Scenario': s} for s in ['Official adjusted','No bonuses','No penalties','No bonuses or penalties']]
    (DATA/'model_data.json').write_text(json.dumps(tables,indent=2),encoding='utf-8')
    measures=[]
    def m(name,expression,fmt='#,0',description=None):
        measures.append(dict(tableName='Metrics',name=name,expression=expression,formatString=fmt,description=description or name,displayFolder='PDF analytics'))
    m('Top Ten Finishes',"COALESCE(CALCULATE(COUNTROWS('Result'),KEEPFILTERS('Result'[Position]<=10)),0)")
    m('Stage Wins',"COALESCE(CALCULATE(COUNTROWS('Result'),KEEPFILTERS('Result'[Position]=1)),0)")
    m('Stage Podiums',"COALESCE(CALCULATE(COUNTROWS('Result'),KEEPFILTERS('Result'[Position]<=3)),0)")
    m('Mountain Podiums',"CALCULATE([Stage Podiums],KEEPFILTERS('Stage'[Stage Type]=\"Mountain\"))")
    m('Stage Winner Gap Seconds',"AVERAGEX('Result', VAR s='Result'[Stage] VAR winner=CALCULATE(MIN('Result'[Adjusted Seconds]),REMOVEFILTERS('Rider'),REMOVEFILTERS('Result'),'Result'[Stage]=s,'Result'[Position]=1) RETURN 'Result'[Adjusted Seconds]-winner)",'0.0','Mean adjusted-time gap to the rider placed first; can be negative after adjustments.')
    m('Mountain Mean Gap Seconds',"CALCULATE([Stage Winner Gap Seconds],KEEPFILTERS('Stage'[Stage Type]=\"Mountain\"))",'0.0')
    m('Speed Proxy kmh',"DIVIDE(SUMX('Result',RELATED('Stage'[Distance km])),DIVIDE(SUM('Result'[Finish Seconds]),3600))",'0.0','Distance / raw finish hours. Teams use summed rider-distance / summed rider-time, not summed speeds.')
    m('Mountain Cumulative Seconds',"IF(HASONEVALUE('Rider'[Bib]) && NOT ISBLANK([GC Rank]), VAR s=[As of Stage Number] RETURN CALCULATE(SUM('Result'[Adjusted Seconds]),FILTER(ALL('Stage'),'Stage'[Stage]<=s && 'Stage'[Stage Type]=\"Mountain\")))")
    m('Mountain GC Proxy Rank',"VAR t=[Mountain Cumulative Seconds] VAR field=FILTER(ALL('Rider'),NOT ISBLANK(CALCULATE([Mountain Cumulative Seconds]))) RETURN IF(NOT ISBLANK(t),RANKX(field,[Mountain Cumulative Seconds],t,ASC,Skip))",'0','Time-only mountain proxy, distinct from KOM points.')
    m('Young GC at Race Start Rank',"VAR t=[Rider Cumulative Seconds] VAR age=SELECTEDVALUE('Rider'[Age at Race Start]) VAR field=FILTER(ALL('Rider'),'Rider'[Age at Race Start]<26 && NOT ISBLANK(CALCULATE([Rider Cumulative Seconds]))) RETURN IF(NOT ISBLANK(t) && age<26,RANKX(field,[Rider Cumulative Seconds],t,ASC,Skip))",'0','Under 26 on the first stage date; separate from the original calendar-year Young Rider rule.')
    m('GC Trace Hours',"IF(HASONEVALUE('Rider'[Bib]),DIVIDE(CALCULATE(MAX('Standing'[Cumulative Seconds]),'Standing'[Eligible]=1),3600))",'0.00')
    m('GC Trace Rank',"IF(HASONEVALUE('Rider'[Bib]) && HASONEVALUE('Stage'[Stage]),MAX('Standing'[GC Rank]))",'0')
    m('GC Rank Change',"VAR s=SELECTEDVALUE('Stage'[Stage]) VAR nowRank=[GC Trace Rank] VAR prior=CALCULATE(MAX('Standing'[GC Rank]),REMOVEFILTERS('Stage'),'Standing'[Stage]=s-1) RETURN IF(NOT ISBLANK(nowRank) && NOT ISBLANK(prior),prior-nowRank)",'0','Positive = places gained; blank on first stage or after exit.')
    m('Mountain Trace Hours',"CALCULATE([GC Trace Hours],KEEPFILTERS('Stage'[Stage Type]=\"Mountain\"))",'0.00')
    m('Stage Distance km',"SELECTEDVALUE('Stage'[Distance km])",'0.0')
    m('Stage Winner',"VAR winner=CALCULATE(SELECTEDVALUE('Result'[Bib]),REMOVEFILTERS('Rider'),'Result'[Position]=1) RETURN IF(NOT ISBLANK(winner),LOOKUPVALUE('Rider'[Rider Label],'Rider'[Bib],winner))",'')
    m('Top Ten Adjusted Seconds',"IF(HASONEVALUE('Rider'[Bib]) && HASONEVALUE('Stage'[Stage]),CALCULATE(SUM('Result'[Adjusted Seconds]),KEEPFILTERS('Result'[Position]<=10)))")
    m('Top Ten Position',"VAR pos=[Stage Position] RETURN IF(NOT ISBLANK(pos) && pos<=10,pos)",'0')
    m('Cumulative Bonus Seconds',"VAR s=[As of Stage Number] RETURN CALCULATE([Bonus Seconds],FILTER(ALL('Stage'),'Stage'[Stage]<=s))")
    m('Cumulative Penalty Seconds',"VAR s=[As of Stage Number] RETURN CALCULATE([Penalty Seconds],FILTER(ALL('Stage'),'Stage'[Stage]<=s))")
    m('Scenario Seconds',"VAR t=[Rider Cumulative Seconds] VAR mode=SELECTEDVALUE('Scenario'[Scenario],\"Official adjusted\") RETURN IF(NOT ISBLANK(t),t+IF(mode IN {\"No bonuses\",\"No bonuses or penalties\"},[Cumulative Bonus Seconds],0)-IF(mode IN {\"No penalties\",\"No bonuses or penalties\"},[Cumulative Penalty Seconds],0))")
    m('Scenario GC Rank',"VAR t=[Scenario Seconds] VAR field=FILTER(ALL('Rider'),NOT ISBLANK(CALCULATE([Scenario Seconds]))) RETURN IF(NOT ISBLANK(t),RANKX(field,[Scenario Seconds],t,ASC,Skip))",'0')
    m('Scenario Rank Change',"IF(NOT ISBLANK([GC Rank]),[GC Rank]-[Scenario GC Rank])",'0')
    m('Top Ten Movement',"VAR a=[GC Rank] VAR b=[Scenario GC Rank] RETURN IF(NOT ISBLANK(a),SWITCH(TRUE(),a>10 && b<=10,\"Entered top 10\",a<=10 && b>10,\"Left top 10\",a<=10,\"Stayed top 10\",\"Outside top 10\"))",'')
    for name,base in [('Country Wins','Stage Wins'),('Country Podiums','Stage Podiums')]:
        m(name,f"CALCULATE([{base}],KEEPFILTERS(TREATAS(VALUES('Country'[Country]),'Rider'[Rider Country])))")
    m('Country Best GC Rank',"VAR s=[As of Stage Number] RETURN CALCULATE(MIN('Standing'[GC Rank]),REMOVEFILTERS('Stage'),'Standing'[Stage]=s,KEEPFILTERS(TREATAS(VALUES('Country'[Country]),'Rider'[Rider Country])))",'0')
    m('Country Result Count',"CALCULATE(COUNTROWS('Result'),KEEPFILTERS(TREATAS(VALUES('Country'[Country]),'Rider'[Rider Country])))")
    (DATA/'analytics_measures.json').write_text(json.dumps(measures,indent=2),encoding='utf-8')
    existing=json.loads((DATA/'measures.json').read_text(encoding='utf-8'))
    extra={m['name'] for m in measures}
    (DATA/'measures.json').write_text(json.dumps([m for m in existing if m['name'] not in extra]+measures,indent=2),encoding='utf-8')
    definition=ROOT/'Tour de France.SemanticModel/definition'
    for name in ['Stage','Rider','Scenario']:
        rows=tables[name]
        def quote(v):return 'null' if v is None else json.dumps(v,ensure_ascii=False).replace('\\"','""') if isinstance(v,str) else str(v)
        columns=[]; types=[]
        for n in rows[0]:
            sample=next((r[n] for r in rows if r[n] is not None),None)
            typ='string' if isinstance(sample,str) else 'double' if isinstance(sample,float) or n=='Distance km' else 'int64'
            columns.append(f"\tcolumn '{n}'\n\t\tdataType: {typ}\n\t\tsummarizeBy: none\n\t\tsourceColumn: {n}\n")
            types.append(f'#"{n}" = '+('nullable text' if typ=='string' else 'number' if typ=='double' else 'Int64.Type'))
        source='let Source = #table(type table ['+', '.join(types)+'], {\n'+',\n'.join('{'+','.join(quote(v) for v in r.values())+'}' for r in rows)+'\n}) in Source'
        tmdl=f"table '{name}'\n\n"+'\n'.join(columns)+f"\n\tpartition '{name}' = m\n\t\tmode: import\n\t\tsource =\n"+'\n'.join('\t\t\t\t'+line for line in source.splitlines())+'\n'
        (definition/f'tables/{name}.tmdl').write_text(tmdl,encoding='utf-8')
    model=definition/'model.tmdl'
    text=model.read_text(encoding='utf-8')
    if 'ref table Scenario' not in text:text+='\nref table Scenario\n'
    model.write_text(text,encoding='utf-8')
    metric_path=definition/'tables/Metrics.tmdl'
    text=metric_path.read_text(encoding='utf-8').split('\n\t/// PDF ANALYTICS')[0].rstrip()
    for item in measures:
        text=re.sub(r"\n\tmeasure '"+re.escape(item['name'])+r"' =[^\n]*(?:\n\t\t[^\n]*|\n(?=\n))*",'',text)
    text+='\n\n\t/// PDF ANALYTICS\n'
    for item in measures:
        text+=f"\tmeasure '{item['name']}' = {item['expression']}\n"
        if item['formatString']:text+=f"\t\tformatString: {item['formatString']}\n"
        text+='\t\tdisplayFolder: PDF analytics\n\n'
    metric_path.write_text(text,encoding='utf-8')
    country=definition/'tables/Country.tmdl'
    text=country.read_text(encoding='utf-8')
    if 'dataCategory: Country' not in text:text=text.replace('\tcolumn Country\n','\tcolumn Country\n\t\tdataCategory: Country\n')
    country.write_text(text,encoding='utf-8')

if __name__=='__main__':extend()
