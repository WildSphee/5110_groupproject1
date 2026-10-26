"""Independent raw CSV/SQLite checks plus expected answers for live Power BI tests."""
import csv, json, sqlite3, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
db=sqlite3.connect(':memory:');db.row_factory=sqlite3.Row
raw={}
for f in (ROOT/'data').glob('*.csv'):
    rows=list(csv.DictReader(f.open(encoding='utf-8')));raw[f.stem]=rows
    numeric={'bib_no','stage_id','finish_time','bonus','time_penalty','position','points','kom_points',
        'eligible','young','cumulative_seconds','stages_completed','gc_rank','points_rank','kom_rank','young_rank',
        'finishers','top3_seconds','stages_scored','cumulative_top3_seconds','team_rank'}
    columns=list(rows[0]);db.execute('CREATE TABLE "'+f.stem+'" ('+','.join('"'+c+'" '+('INTEGER' if c in numeric else 'TEXT') for c in columns)+')')
    db.executemany('INSERT INTO "'+f.stem+'" VALUES('+','.join('?' for _ in columns)+')',[[None if r[c]=='' else int(r[c]) if c in numeric else r[c] for c in columns] for r in rows])
def q(sql,*args):return [dict(r) for r in db.execute(sql,args)]
def scalar(sql,*args):return db.execute(sql,args).fetchone()[0]

def reference(s):
    # Recompute from normalized results and score events; never trust stored snapshots.
    return q('''WITH agg AS (
      SELECT r.bib_no, SUM(f.finish_time-f.bonus+f.time_penalty) secs,
        SUM(p.points) pts, SUM(p.kom_points) kom, r.dob >= '2001-01-01' young
      FROM rider r JOIN result f USING(bib_no) JOIN classification_score p USING(bib_no,stage_id)
      WHERE f.stage_id<=? AND NOT EXISTS(SELECT 1 FROM exit e WHERE e.bib_no=r.bib_no AND e.stage_id<=?)
      GROUP BY r.bib_no HAVING COUNT(*)=?
    ), ranked AS (SELECT *,RANK() OVER(ORDER BY secs) gc,RANK() OVER(ORDER BY pts DESC) pr,
       RANK() OVER(ORDER BY kom DESC) kr FROM agg), youth AS (
       SELECT bib_no,RANK() OVER(ORDER BY secs) yr FROM agg WHERE young=1)
    SELECT ranked.*,youth.yr FROM ranked LEFT JOIN youth USING(bib_no) ORDER BY bib_no''',s,s,scalar('SELECT COUNT(*) FROM stage WHERE stage_id<=?',s))

class DataTests(unittest.TestCase):
    def test_counts(self):self.assertEqual([len(raw[n]) for n in ['rider','team','stage','country','result']],[48,6,21,12,940])
    def test_keys(self):
        self.assertEqual(scalar('SELECT COUNT(*) FROM (SELECT bib_no,stage_id FROM result GROUP BY bib_no,stage_id)'),940)
        self.assertEqual(scalar('SELECT COUNT(*) FROM (SELECT stage_id,position FROM result GROUP BY stage_id,position)'),940)
    def test_foreign_keys(self):
        for table,col,dim,key in [('result','bib_no','rider','bib_no'),('result','stage_id','stage','stage_id'),('rider','team_name','team','team_name'),('rider','country_code','country','country_code'),('team','country_code','country','country_code')]:
            self.assertEqual(scalar(f'SELECT COUNT(*) FROM {table} t LEFT JOIN {dim} d ON t.{col}=d.{key} WHERE d.{key} IS NULL'),0)
    def test_team_members_leader(self):
        for r in q("SELECT team_name,COUNT(*) n,SUM(is_leader='True') leaders FROM rider GROUP BY team_name"):
            self.assertEqual((r['n'],r['leaders']),(8,1))
    def test_time_positive(self):self.assertEqual(scalar('SELECT COUNT(*) FROM result WHERE finish_time<=0 OR bonus<0 OR time_penalty<0 OR finish_time-bonus+time_penalty<=0'),0)
    def test_exits(self):self.assertEqual(scalar('SELECT COUNT(*) FROM result r JOIN exit e USING(bib_no) WHERE r.stage_id>=e.stage_id'),0)
    def test_equal_finish_times(self):self.assertGreater(scalar('SELECT COUNT(*) FROM (SELECT stage_id,finish_time FROM result GROUP BY stage_id,finish_time HAVING COUNT(*)>1)'),0)
    def test_all_snapshot_ranks(self):
        for s in range(1,22):
            exp=reference(s);actual={r['bib_no']:r for r in q('SELECT * FROM standing_snapshot WHERE stage_id=? AND eligible=1',s)}
            self.assertEqual(set(actual),{r['bib_no'] for r in exp})
            for r in exp:
                a=actual[r['bib_no']]
                self.assertEqual([a[k] for k in ['cumulative_seconds','points','kom_points','gc_rank','points_rank','kom_rank','young_rank']],[r[k] for k in ['secs','pts','kom','gc','pr','kr','yr']])
    def test_exited_unranked(self):self.assertEqual(scalar('SELECT COUNT(*) FROM standing_snapshot WHERE eligible=0 AND (gc_rank IS NOT NULL OR points_rank IS NOT NULL OR kom_rank IS NOT NULL OR young_rank IS NOT NULL)'),0)
    def test_youth(self):self.assertEqual(scalar("SELECT COUNT(*) FROM standing_snapshot s JOIN rider r USING(bib_no) WHERE young_rank IS NOT NULL AND dob<'2001-01-01'"),0)
    def test_team_top_three(self):
        expected=q('''WITH a AS(SELECT team_name,stage_id,finish_time-bonus+time_penalty secs,
            ROW_NUMBER() OVER(PARTITION BY team_name,stage_id ORDER BY finish_time-bonus+time_penalty,bib_no) n
            FROM result JOIN rider USING(bib_no)) SELECT team_name,stage_id,SUM(secs) secs FROM a WHERE n<=3 GROUP BY team_name,stage_id HAVING COUNT(*)=3''')
        self.assertEqual({(r['team_name'],r['stage_id']):r['secs'] for r in expected},{(r['team_name'],r['stage_id']):r['top3_seconds'] for r in q('SELECT * FROM team_stage WHERE top3_seconds IS NOT NULL')})
    def test_team_rank(self):
        for s in range(1,22):
            exp=q('''WITH a AS(SELECT team_name,COUNT(top3_seconds) n,SUM(top3_seconds) secs FROM team_stage WHERE stage_id<=? GROUP BY team_name)
             SELECT *,RANK() OVER(ORDER BY n DESC,secs) r FROM a''',s)
            for r in exp:
                a=q('SELECT * FROM team_snapshot WHERE stage_id=? AND team_name=?',s,r['team_name'])[0]
                self.assertEqual((a['stages_scored'],a['cumulative_top3_seconds'],a['team_rank']),(r['n'],r['secs'],r['r']))
    def test_incomplete_team(self):
        self.assertEqual(scalar("SELECT finishers FROM team_stage WHERE team_name='Northstar Velo' AND stage_id=18"),2)
        self.assertIsNone(scalar("SELECT top3_seconds FROM team_stage WHERE team_name='Northstar Velo' AND stage_id=18"))
        self.assertEqual(scalar("SELECT team_rank FROM team_snapshot WHERE team_name='Northstar Velo' AND stage_id=21"),6)
    def test_countries(self):
        self.assertEqual(scalar("SELECT COUNT(*) FROM team WHERE country_code='FRA'"),2)
        for c in ['SGP','JPN']:
            self.assertEqual(scalar('SELECT COUNT(*) FROM rider WHERE country_code=?',c),0)
            self.assertEqual(scalar('SELECT COUNT(*) FROM team WHERE country_code=?',c),0)
    def test_nationality_independence(self):self.assertGreater(scalar('SELECT COUNT(*) FROM rider r JOIN team t USING(team_name) WHERE r.country_code<>t.country_code'),0)
    def test_locations_used(self):self.assertEqual(scalar('SELECT COUNT(*) FROM location l WHERE NOT EXISTS(SELECT 1 FROM stage s WHERE s.start_location=l.location_name OR s.end_location=l.location_name)'),0)
    def test_total_reconciles(self):
        total=scalar('SELECT SUM(finish_time-bonus+time_penalty) FROM result')
        for keys in ['stage_id','r.team_name','r.bib_no','stage_type,stage_id,r.team_name,r.bib_no']:
            rows=q(f'SELECT SUM(finish_time-bonus+time_penalty) secs FROM result f JOIN rider r USING(bib_no) JOIN stage s USING(stage_id) GROUP BY {keys}')
            self.assertEqual(sum(r['secs'] for r in rows),total)
    def test_duration_over_24h(self):self.assertGreater(reference(21)[0]['secs'],86400)
    def test_prologue_and_noncontiguous_ids(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('generator',ROOT/'tools/generate_data.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        rider={'bib_no':1,'dob':'2002-01-01'}
        stages=[{'stage_id':0},{'stage_id':3}]
        rows=[dict(bib_no=1,stage_id=s,finish_time=100,bonus=0,time_penalty=0) for s in [0,3]]
        scores={(1,s):dict(points=0,kom_points=0) for s in [0,3]}
        self.assertEqual(mod.rider_snapshot(rider,rows,scores,{},stages,3)['eligible'],1)
        self.assertEqual(mod.rider_snapshot(rider,rows,scores,{},stages,0)['eligible'],1)
        missing=mod.rider_snapshot(rider,rows[:1],scores,{},stages,3)
        self.assertEqual((missing['eligible'],missing['status']),(0,'Incomplete results'))
        exited=mod.rider_snapshot(rider,rows[:1],scores,{1:3},stages,3)
        self.assertEqual((exited['eligible'],exited['status']),(0,'Exited'))
        for dob,young in [('2000-12-31',0),('2001-01-01',1),('2001-01-02',1)]:
            self.assertEqual(mod.rider_snapshot(dict(bib_no=1,dob=dob),rows,scores,{},stages,3)['young'],young)

def expected():
    tests=[]
    def add(name,query,rows):tests.append(dict(name=name,query=query,expected=rows))
    for s in [1,6,7,17,18,21]:
        add(f'All four ranks, stage {s}',f'''EVALUATE SELECTCOLUMNS(CALCULATETABLE(SUMMARIZECOLUMNS('Rider'[Bib],"gc",[GC Rank],"pr",[Points Rank],"kr",[KOM Rank],"yr",[Young Rank],"secs",[Rider Cumulative Seconds]),TREATAS({{{s}}},'As Of'[Stage])),"bib",'Rider'[Bib],"gc",[gc],"pr",[pr],"kr",[kr],"yr",[yr],"secs",[secs])''',
            [dict(bib=r['bib_no'],gc=r['gc'],pr=r['pr'],kr=r['kr'],yr=r['yr'],secs=r['secs']) for r in reference(s)])
    country=q('''SELECT c.country_name country,(SELECT COUNT(*) FROM team t WHERE t.country_code=c.country_code) teams,
       (SELECT COUNT(*) FROM rider r WHERE r.country_code=c.country_code) riders FROM country c''')
    add('Independent countries including zeros',"EVALUATE SELECTCOLUMNS(SUMMARIZECOLUMNS('Country'[Country],\"teams\",[Teams by Country],\"riders\",[Riders by Country]),\"country\",'Country'[Country],\"teams\",[teams],\"riders\",[riders])",country)
    for fields in [[('Rider Country','country_name')],[('Rider Country','country_name'),('Team','team_name')],[('Rider Country','country_name'),('Team','team_name'),('Bib','bib_no')]]:
        dax=','.join(f"'Rider'[{c}]" for c,k in fields)
        sel=','.join(f'"{k}",\'Rider\'[{c}]' for c,k in fields)
        sql=','.join(k for c,k in fields)
        for country_filter in [None,'France','Singapore']:
            where=' WHERE country_name=?' if country_filter else ''
            rows=q(f'SELECT {sql},COUNT(*) riders FROM rider JOIN country USING(country_code){where} GROUP BY {sql}',*([country_filter] if country_filter else []))
            query=f'SELECTCOLUMNS(SUMMARIZECOLUMNS({dax},"riders",[Roster Riders]),{sel},"riders",[riders])'
            if country_filter:query=f'CALCULATETABLE({query},TREATAS({{"{country_filter}"}},\'Country\'[Country]))'
            add('Roster '+sql+' / '+str(country_filter),'EVALUATE '+query,rows)
    for s in [17,18,21]:
        rows=q('SELECT team_name team,team_rank rank,stages_scored stages,cumulative_top3_seconds/3600.0 hours FROM team_snapshot WHERE stage_id=?',s)
        add(f'Team coverage stage {s}',f'''EVALUATE SELECTCOLUMNS(CALCULATETABLE(SUMMARIZECOLUMNS('Team'[Team],"rank",[Best Team Rank],"stages",[Stages Scored],"hours",[Team Cumulative Hours]),TREATAS({{{s}}},'As Of'[Stage])),"team",'Team'[Team],"rank",[rank],"stages",[stages],"hours",[hours])''',rows)
    for fields in [[('Stage','Stage Type','stage_type')],[('Stage','Stage Type','stage_type'),('Stage','Stage','stage_id')],
                   [('Stage','Stage','stage_id'),('Rider','Team','team_name')],[('Stage','Stage','stage_id'),('Rider','Team','team_name'),('Rider','Bib','bib_no')]]:
        dax=','.join(f"'{t}'[{c}]" for t,c,k in fields);sel=','.join(f'"{k}",\'{t}\'[{c}]' for t,c,k in fields)
        sql=','.join(k for t,c,k in fields)
        rows=q(f'SELECT {sql},SUM(finish_time-bonus+time_penalty) secs FROM result JOIN stage USING(stage_id) JOIN rider USING(bib_no) GROUP BY {sql}')
        for r in rows:
            if 'stage_type' in r:r['stage_type']=r['stage_type'].title()
        add('Drill '+sql,f'EVALUATE SELECTCOLUMNS(SUMMARIZECOLUMNS({dax},"secs",[Adjusted Seconds]),{sel},"secs",[secs])',rows)
    r=next(r for r in reference(21) if r['bib_no']==21)
    add('Single rider preserves global rank',"EVALUATE CALCULATETABLE(ROW(\"gc\",[GC Rank],\"secs\",[Rider Cumulative Seconds]),TREATAS({21},'Rider'[Bib]))",[dict(gc=r['gc'],secs=r['secs'])])
    seconds=r['secs'];duration=f'{seconds//3600}:{seconds%3600//60:02d}:{seconds%60:02d}'
    add('Duration string does not wrap after 24 hours',"EVALUATE CALCULATETABLE(ROW(\"duration\",[Rider Cumulative Time]),TREATAS({21},'Rider'[Bib]))",[dict(duration=duration)])
    for s in [1,6,7,18,21]:
        add(f'Explicit exit count at stage {s}',f'''EVALUATE CALCULATETABLE(ROW("exits",[Exited Riders]),TREATAS({{{s}}},'As Of'[Stage]))''',[dict(exits=scalar('SELECT COUNT(*) FROM exit WHERE stage_id<=?',s))])
    add('Multi stage selector uses latest',"EVALUATE CALCULATETABLE(ROW(\"stage\",[As of Stage Number],\"eligible\",[Eligible Riders]),TREATAS({6,7},'As Of'[Stage]))",[dict(stage=7,eligible=len(reference(7)))])
    add('Historical exit: stage 6 vs 7',"EVALUATE CALCULATETABLE(ROW(\"gc\",[GC Rank],\"time\",[Rider Cumulative Seconds]),TREATAS({8},'Rider'[Bib]),TREATAS({7},'As Of'[Stage]))",[dict(gc=None,time=None)])
    secs=scalar('SELECT SUM(finish_time-bonus+time_penalty) FROM result WHERE bib_no=1 AND stage_id<=9')
    add('Running time ignores stage type filter',"EVALUATE CALCULATETABLE(ROW(\"hours\",[Running Rider Hours]),TREATAS({1},'Rider'[Bib]),TREATAS({9},'Stage'[Stage]),TREATAS({\"Mountain\"},'Stage'[Stage Type]))",[dict(hours=secs/3600)])
    add('No results returns blank, no fake zero rank',"EVALUATE CALCULATETABLE(ROW(\"position\",[Stage Position],\"time\",[Adjusted Seconds]),TREATAS({8},'Rider'[Bib]),TREATAS({7},'Stage'[Stage]))",[dict(position=None,time=None)])
    (ROOT/'tests/dax_expected.json').write_text(json.dumps(tests,indent=2),encoding='utf-8')

if __name__=='__main__':
    expected();unittest.main(verbosity=2)
