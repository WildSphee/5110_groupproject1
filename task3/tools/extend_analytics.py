"""PDF E1Ã¢â‚¬â€œE15 extensions; portable embedded tables and reproducible DAX definitions."""
import csv
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'

def analytics_definitions():
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
    m('Country Rider Hours',"CALCULATE([Adjusted Hours],KEEPFILTERS(TREATAS(VALUES('Country'[Country]),'Rider'[Rider Country])))",'#,0.00','Completed effort from riders representing the selected country; includes effort before exit.')
    m('Scenario Stage Adjustment Seconds',"""VAR s=[As of Stage Number] VAR mode=SELECTEDVALUE('Scenario'[Scenario],"Official adjusted") VAR bibs=CALCULATETABLE(VALUES('Standing'[Bib]),REMOVEFILTERS('Stage'),'Standing'[Stage]=s,'Standing'[Eligible]=1) VAR bonus=CALCULATE([Bonus Seconds],KEEPFILTERS(TREATAS(bibs,'Rider'[Bib])),KEEPFILTERS('Stage'[Stage]<=s)) VAR penalty=CALCULATE([Penalty Seconds],KEEPFILTERS(TREATAS(bibs,'Rider'[Bib])),KEEPFILTERS('Stage'[Stage]<=s)) RETURN IF(NOT ISBLANK(bonus)||NOT ISBLANK(penalty),IF(mode IN {"Official adjusted","No bonuses"},penalty,0)-IF(mode IN {"Official adjusted","No penalties"},bonus,0))""",'#,0','Net seconds applied to raw finish time under the selected rules, for riders eligible at the snapshot.')
    m('Roster Bib',"IF(NOT ISBLANK([Roster Riders]),SELECTEDVALUE('Rider'[Bib]))",'0','Bib of a rider in the intersection of the selected team and country.')
    leaders="""VAR c=SELECTEDVALUE('Classification'[Classification]) VAR leaders=CALCULATETABLE(FILTER(ALL('Rider'),[Classification Rank]=1),REMOVEFILTERS('Rider'),REMOVEFILTERS('Stage')) VAR score=MAXX(leaders,SWITCH(c,"Points",[Cumulative Points],"Mountains",[Cumulative KOM Points],[Rider Cumulative Seconds])) """
    m('Award leaders',leaders+"""RETURN IF(NOT ISBLANK(score),IF(c IN {"Points","Mountains"} && score=0,"Field tied on zero points",CONCATENATEX(leaders,'Rider'[Rider],", ",'Rider'[Bib],ASC)))""",'','All joint leaders in the full field through the selected stage.')
    m('Winning score',leaders+"""RETURN IF(NOT ISBLANK(score),IF(c IN {"Points","Mountains"},FORMAT(score,"0") & " pts",FORMAT(INT(score/3600),"0") & ":" & FORMAT(INT(MOD(score,3600)/60),"00") & ":" & FORMAT(MOD(score,60),"00")))""",'')
    m('Winning rule',"""SWITCH(SELECTEDVALUE('Classification'[Classification]),"General","Lowest total adjusted time","Points","Most cumulative finish points","Mountains","Most cumulative mountain points","Young Rider","Lowest total adjusted time; born on or after 1 Jan 2001")""",'')
    m('Team deficit minutes',"""VAR scored=[Stages Scored] VAR most=MAXX(ALL('Team'),[Stages Scored]) VAR referenceTime=MINX(FILTER(ALL('Team'),[Stages Scored]=most),[Team Cumulative Hours]) RETURN IF(HASONEVALUE('Team'[Team]) && scored=most,ROUND(60*([Team Cumulative Hours]-referenceTime),2))""",'0.00','Time behind the leading team; only teams with the same scored-stage coverage are comparable.')
    m('GC daily deficit seconds',"""VAR t=IF(HASONEVALUE('Stage'[Stage]) && HASONEVALUE('Rider'[Bib]),CALCULATE(MIN('Standing'[Cumulative Seconds]),'Standing'[Eligible]=1)) VAR bestTime=CALCULATE(MIN('Standing'[Cumulative Seconds]),REMOVEFILTERS('Rider'),'Standing'[Eligible]=1) RETURN IF(NOT ISBLANK(t),t-bestTime)""",'#,0','Gap to the overall leader on the axis stage; zero is a shared or outright lead.')
    m('Mountain podium finishes',"IF([Mountain Podiums]>0,[Mountain Podiums])",'0','Mountain-stage top-three finishes; only podium finishers are shown.')
    m('Top Ten Finish Gap',"""VAR pos=[Top Ten Position] VAR winner=CALCULATE(MIN('Result'[Finish Seconds]),REMOVEFILTERS('Rider'),'Result'[Position]=1) RETURN IF(NOT ISBLANK(pos),MAX('Result'[Finish Seconds])-winner)""",'#,0','Raw finish seconds behind the stage winner; tied finish times may have different positions.')
    return measures

def extend(refresh_fixture=False):
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
    # Refresh embedded rows too: Power BI reads these partitions, not the generated CSVs.
    for name in (tables if refresh_fixture else ['Team','Country','Result','Standing','Team Stage','Team Standing']):
        path=ROOT/'Tour de France.SemanticModel/definition/tables'/f'{name}.tmdl'
        text=path.read_text(encoding='utf-8')
        rows=tables[name]
        def literal(v):
            return 'null' if v is None else '"' + v.replace('"','""') + '"' if isinstance(v,str) else str(v)
        body=',\n'.join('\t'*4+'{'+','.join(literal(v) for v in row.values())+'}' for row in rows)
        start=text.index('], {\n',text.index('let Source = #table'))+len('], {\n')
        end=text.index('\t'*4+'}) in Source',start)
        updated=text[:start]+body+'\n'+text[end:]
        if text!=updated:path.write_text(updated,encoding='utf-8')
    if refresh_fixture:return  # Retain the checked-in measures, columns and lineage tags.
    measures=analytics_definitions()
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
