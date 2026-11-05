"""Check the delivered 2025 model against the supplied PostgreSQL tables and views."""
import csv,json,sqlite3,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'use_this_data/export/csv'
DATA=json.loads((ROOT/'data/model_data.json').read_text(encoding='utf8'))
db=sqlite3.connect(':memory:');db.row_factory=sqlite3.Row
ints={'stage_id','bib_no','position','finish_time','bonus','time_penalty','adjusted_time','gc_rank','young_rank','team_rank','total_adjusted_time','total_top3_time','stages_scored'}
for f in sorted(SOURCE.glob('*.csv')):
    with f.open(encoding='utf-8-sig',newline='') as src:
        rows=csv.DictReader(src);cols=rows.fieldnames
        db.execute(f'CREATE TABLE "{f.stem}" ('+','.join(f'"{c}" '+('INTEGER' if c in ints else 'TEXT') for c in cols)+')')
        db.executemany(f'INSERT INTO "{f.stem}" VALUES('+','.join('?' for _ in cols)+')',
            [[None if not row[c] else int(row[c]) if c in ints else row[c] for c in cols] for row in rows])
def q(sql,*args):return [dict(r) for r in db.execute(sql,args)]
def ref(stage):
    return q("""WITH a AS (SELECT f.bib_no,SUM(f.finish_time-f.bonus+f.time_penalty) secs,ri.dob
      FROM result f JOIN rider ri USING(bib_no) WHERE f.stage_id<=? AND NOT EXISTS(SELECT 1 FROM exit e WHERE e.bib_no=f.bib_no AND e.stage_id<=?)
      GROUP BY f.bib_no HAVING COUNT(*)=(SELECT COUNT(*) FROM stage WHERE stage_id<=?)),
      g AS (SELECT *,RANK() OVER(ORDER BY secs) gc FROM a), y AS (SELECT bib_no,RANK() OVER(ORDER BY secs) yr FROM a WHERE dob>='2000-01-01')
      SELECT bib_no,secs,gc,yr FROM g LEFT JOIN y USING(bib_no) ORDER BY bib_no""",stage,stage,stage)
def team_ref(stage):
    return q("""WITH t AS (SELECT r.team_name team,f.stage_id,finish_time-bonus+time_penalty elapsed,
       ROW_NUMBER() OVER(PARTITION BY r.team_name,f.stage_id ORDER BY finish_time-bonus+time_penalty,bib_no) ordinal
       FROM result f JOIN rider r USING(bib_no) WHERE f.stage_id<=?),
       daily AS (SELECT team,stage_id,SUM(elapsed) top3 FROM t WHERE ordinal<=3 GROUP BY team,stage_id HAVING COUNT(*)=3),
       race AS (SELECT team,COUNT(*) scored,SUM(top3) secs FROM daily GROUP BY team)
       SELECT *,RANK() OVER(ORDER BY scored DESC,secs) ranking FROM race""",stage)
def withdrawal_ref():
    rows=q("""SELECT e.bib_no bib,e.stage_id stage,e.exit_reason type,r.rider_name rider,r.team_name team,
       (SELECT MAX(stage_id) FROM result WHERE bib_no=e.bib_no AND stage_id<e.stage_id) previous,
       COALESCE((SELECT SUM(finish_time-bonus+time_penalty) FROM result WHERE bib_no=e.bib_no AND stage_id<e.stage_id),0) elapsed,
       (SELECT COUNT(*) FROM stage WHERE stage_id>=e.stage_id) remaining
       FROM exit e JOIN rider r USING(bib_no)""")
    target=q('SELECT total_adjusted_time secs FROM v_general_classification WHERE gc_rank=1')[0]['secs']
    for r in rows:
        prior={a['bib_no']:a['gc'] for a in ref(r['previous'])} if r['previous'] else {}
        r.update(prior=prior.get(r['bib']),budget=target-r['elapsed'])
    return rows
class RaceTests(unittest.TestCase):
    def test_export_grain(self):
        self.assertEqual([len(DATA[x]) for x in ['Rider','Team','Stage','Result','Withdrawal']],[184,23,21,3602,24])
        self.assertEqual(len({(r['Stage'],r['Bib']) for r in DATA['Result']}),3602)
    def test_exact_adjusted_view(self):
        self.assertEqual({(r['Bib'],r['Stage']):(r['Position'],r['Adjusted Seconds']) for r in DATA['Result']},
          {(r['bib_no'],r['stage_id']):(r['position'],r['adjusted_time']) for r in q('SELECT * FROM v_result_adjusted')})
    def test_gc_and_age_ranks_all_stages(self):
        for s in range(1,22):
            self.assertEqual({r['Bib']:(r['Cumulative Seconds'],r['GC Rank'],r['Young Rank']) for r in DATA['Standing'] if r['Stage']==s and r['Eligible']},
                {r['bib_no']:(r['secs'],r['gc'],r['yr']) for r in ref(s)})
    def test_team_rank_all_stages(self):
        for s in range(1,22):
            self.assertEqual({r['Team']:(r['Team Rank'],r['Stages Scored'],r['Cumulative Top3 Seconds']) for r in DATA['Team Standing'] if r['Stage']==s},
              {r['team']:(r['ranking'],r['scored'],r['secs']) for r in team_ref(s)})
    def test_final_views(self):
        gc=q('SELECT * FROM v_general_classification');y=q('SELECT * FROM v_young_rider_classification');t=q('SELECT * FROM v_best_team')
        self.assertEqual((len(gc),len(y),len(t)),(160,42,23))
        self.assertEqual({(r['bib_no'],r['gc_rank'],r['total_adjusted_time']) for r in gc},
            {(r['Bib'],r['GC Rank'],r['Cumulative Seconds']) for r in DATA['Standing'] if r['Stage']==21 and r['GC Rank']})
        self.assertEqual({(r['bib_no'],r['young_rank'],r['total_adjusted_time']) for r in y},
            {(r['Bib'],r['Young Rank'],r['Cumulative Seconds']) for r in DATA['Standing'] if r['Stage']==21 and r['Young Rank']})
        self.assertEqual({(r['team_name'],r['team_rank'],r['total_top3_time'],r['stages_scored']) for r in t},
            {(r['Team'],r['Team Rank'],r['Cumulative Top3 Seconds'],r['Stages Scored']) for r in DATA['Team Standing'] if r['Stage']==21})
    def test_missing_points_are_null(self):
        self.assertTrue(all(r['Points'] is None and r['KOM Points'] is None for r in DATA['Result']))
        self.assertTrue(all(r['Points Rank'] is None and r['KOM Rank'] is None for r in DATA['Standing']))
    def test_unknown_and_tied_position(self):
        self.assertEqual([r['Bib'] for r in DATA['Rider'] if r['Rider Country']=='Unknown'],[78])
        self.assertEqual(sorted(r['Bib'] for r in DATA['Result'] if r['Stage']==13 and r['Position']==108),[23,197])
        self.assertFalse(any(r['Stage']==13 and r['Position']==109 for r in DATA['Result']))
    def test_exit_baseline_and_budget(self):
        by_bib={r['Bib']:r for r in DATA['Withdrawal']}
        for raw in withdrawal_ref():
            r=by_bib[raw['bib']]
            self.assertEqual((r['Previous stage'],r['Previous GC rank'],r['Budget seconds'],r['Stages left']),(raw['previous'],raw['prior'],raw['budget'],raw['remaining']))
            self.assertFalse(any(f['Bib']==r['Bib'] and f['Stage']>=r['Stage'] for f in DATA['Result']))
        self.assertEqual((by_bib[21]['Stage'],by_bib[21]['Previous GC rank']),(14,3))
        self.assertEqual(sum(r['Exit type']=='DNS' for r in by_bib.values()),12)
        self.assertEqual(sum(r['Exit type']=='withdrawal' for r in by_bib.values()),12)
    def test_anomalies_not_corrected(self):
        self.assertEqual(q('SELECT COUNT(*) n,SUM(time_penalty) seconds FROM result WHERE time_penalty>0'),[{'n':4,'seconds':50}])
        inversion=q("""SELECT DISTINCT stage_id FROM (SELECT stage_id,finish_time,LAG(finish_time) OVER(PARTITION BY stage_id ORDER BY position,bib_no) prior FROM result) WHERE finish_time<prior ORDER BY stage_id""")
        self.assertEqual([r['stage_id'] for r in inversion],[1,17,21])

def expected():
    tests=[]
    def add(name,query,rows):tests.append(dict(name=name,query=query,expected=rows))
    for s in [1,7,13,14,21]:
        add(f'GC and Young ranks after stage {s}',f"""EVALUATE SELECTCOLUMNS(CALCULATETABLE(SUMMARIZECOLUMNS('Rider'[Bib],"gc",[GC Rank],"yr",[Young Rank],"secs",[Rider Cumulative Seconds]),TREATAS({{{s}}},'As Of'[Stage])),"bib_no",'Rider'[Bib],"gc",[gc],"yr",[yr],"secs",[secs])""",ref(s))
        add(f'Best Team after stage {s}',f"""EVALUATE SELECTCOLUMNS(CALCULATETABLE(SUMMARIZECOLUMNS('Team'[Team],"ranking",[Best Team Rank],"scored",[Stages Scored],"hours",[Team Cumulative Hours]),TREATAS({{{s}}},'As Of'[Stage])),"team",'Team'[Team],"ranking",[ranking],"scored",[scored],"hours",[hours])""",
            [dict(team=r['team'],ranking=r['ranking'],scored=r['scored'],hours=r['secs']/3600) for r in team_ref(s)])
    for group in [['stage_id'],['stage_id','team_name'],['stage_id','team_name','bib_no']]:
        fields={'stage_id':"'Stage'[Stage]",'team_name':"'Rider'[Team]",'bib_no':"'Rider'[Bib]"}
        g=','.join(fields[k] for k in group);sel=','.join(f'"{k}",{fields[k]}' for k in group);sql=','.join(group)
        add('Drill '+sql,f'EVALUATE SELECTCOLUMNS(SUMMARIZECOLUMNS({g},"secs",[Adjusted Seconds]),{sel},"secs",[secs])',
              q(f'SELECT {sql},SUM(finish_time-bonus+time_penalty) secs FROM result JOIN rider USING(bib_no) GROUP BY {sql}'))
    add('Registration by independent country roles',"""EVALUATE SELECTCOLUMNS(SUMMARIZECOLUMNS('Country'[Country],"teams",[Teams by Country],"riders",[Riders by Country]),"country",'Country'[Country],"teams",[teams],"riders",[riders])""",
        q("""SELECT country_name country,(SELECT COUNT(*) FROM team t WHERE t.country_code=c.country_code) teams,
           (SELECT COUNT(*) FROM rider r WHERE r.country_code=c.country_code) riders FROM country c UNION ALL SELECT 'Unknown',0,COUNT(*) FROM rider WHERE country_code IS NULL"""))
    add('Exit stage and type',"""EVALUATE SELECTCOLUMNS(SUMMARIZECOLUMNS('Stage'[Stage],'Withdrawal'[Exit type],"n",[Exit count]),"stage",'Stage'[Stage],"type",'Withdrawal'[Exit type],"n",[n])""",q('SELECT stage_id stage,exit_reason type,COUNT(*) n FROM exit GROUP BY stage_id,exit_reason'))
    add('Exits by terrain',"""EVALUATE SELECTCOLUMNS(SUMMARIZECOLUMNS('Stage'[Stage Type],"n",[Exit count]),"terrain",'Stage'[Stage Type],"n",[n])""",[dict(terrain=r['terrain'].title(),n=r['n']) for r in q('SELECT stage_type terrain,COUNT(*) n FROM stage JOIN exit USING(stage_id) GROUP BY stage_type')])
    add('Remaining field',"""EVALUATE SELECTCOLUMNS(SUMMARIZECOLUMNS('Stage'[Stage],"n",[Field remaining]),"stage",'Stage'[Stage],"n",[n])""",q('SELECT stage_id stage,(SELECT COUNT(*) FROM rider)-(SELECT COUNT(*) FROM exit e WHERE e.stage_id<=s.stage_id) n FROM stage s'))
    add('Last real GC and finish-time budget',"""EVALUATE SELECTCOLUMNS('Withdrawal',"bib",'Withdrawal'[Bib],"prior",'Withdrawal'[Previous GC rank],"budget",'Withdrawal'[Budget seconds],"remaining",'Withdrawal'[Stages left])""",[{k:r[k] for k in ('bib','prior','budget','remaining')} for r in withdrawal_ref()])
    (ROOT/'tests/dax_expected.json').write_text(json.dumps(tests,indent=2),encoding='utf8')
if __name__=='__main__':
    expected();unittest.main(verbosity=2)
