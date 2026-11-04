"""Report contract checks: bindings, hierarchy depth, bounds and corrected UX definitions."""
import json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'Tour de France.Report/definition'
DATA=json.loads((ROOT/'data/model_data.json').read_text())
MEASURES={m['name'] for m in json.loads((ROOT/'data/measures.json').read_text())}
FILES=list(REPORT.glob('pages/*/visuals/*/visual.json'))
def visual(page,name):return json.loads((REPORT/f'pages/{page}/visuals/{name}/visual.json').read_text())['visual']
def fields(obj):
    if isinstance(obj,dict):
        if 'Column' in obj:yield 'Column',obj['Column']
        if 'Measure' in obj:yield 'Measure',obj['Measure']
        for value in obj.values():yield from fields(value)
    elif isinstance(obj,list):
        for value in obj:yield from fields(value)
class ReportTests(unittest.TestCase):
    def test_pages(self):
        order=json.loads((REPORT/'pages/pages.json').read_text())
        self.assertEqual(order['pageOrder'],['overview','stages','classifications','teams','story','terrain','scenarios'])
        self.assertEqual(set(order['pageOrder']),{p.parent.name for p in (REPORT/'pages').glob('*/page.json')})
        self.assertEqual(visual('overview','riders_country')['visualType'],'azureMap')
        self.assertEqual(visual('scenarios','net_adjustments')['visualType'],'waterfallChart')
    def test_minimal_controls(self):
        dropdowns=set(); lists=set()
        for f in FILES:
            v=json.loads(f.read_text())['visual']; key=(f.parents[2].name,f.parent.name)
            self.assertNotIn(v['visualType'],('card','multiRowCard'))
            if v['visualType']=='textbox':self.assertIn(key[1],{'title','demo'})
            if v['visualType']=='slicer':
                mode=v['objects']['data'][0]['properties']['mode']['expr']['Literal']['Value']
                (dropdowns if mode=="'Dropdown'" else lists).add(key)
        self.assertEqual(dropdowns,{('teams','asof'),('scenarios','asof'),('classifications','asof')})
        self.assertEqual(lists,{('story','rider'),('scenarios','scenario')})
    def test_bindings(self):
        for file in FILES:
            definition=json.loads(file.read_text())
            aliases={}
            def sources(obj):
                if isinstance(obj,dict):
                    for source in obj.get('From',[]):aliases[source['Name']]=source['Entity']
                    for value in obj.values():sources(value)
                elif isinstance(obj,list):
                    for value in obj:sources(value)
            sources(definition)
            for kind,f in fields(definition):
                ref=f['Expression']['SourceRef']
                table=ref.get('Entity') or aliases[ref['Source']];name=f['Property']
                if kind=='Measure':self.assertEqual(table,'Metrics');self.assertIn(name,MEASURES)
                else:self.assertIn(table,DATA);self.assertIn(name,DATA[table][0])
    def test_bounds_and_no_overlap(self):
        for page in (REPORT/'pages').glob('*/page.json'):
            dims=json.loads(page.read_text());rects=[]
            for file in page.parent.glob('visuals/*/visual.json'):
                v=json.loads(file.read_text());p=v['position'];self.assertGreater(p['width'],0);self.assertGreater(p['height'],0)
                self.assertGreaterEqual(p['x'],0);self.assertGreaterEqual(p['y'],0)
                self.assertLessEqual(p['x']+p['width'],dims['width']);self.assertLessEqual(p['y']+p['height'],dims['height'])
                rects.append((v['name'],p))
            for i,(name,a) in enumerate(rects):
                for other,b in rects[i+1:]:
                    overlap=min(a['x']+a['width'],b['x']+b['width'])>max(a['x'],b['x']) and min(a['y']+a['height'],b['y']+b['height'])>max(a['y'],b['y'])
                    self.assertFalse(overlap,f'{page.parent.name}: {name} overlaps {other}')
    def test_drill_depth(self):
        for pg,n,role,depth in [('overview','team_rider','Category',2),('stages','stage_matrix','Rows',4),('teams','detail','Rows',2)]:
            v=visual(pg,n);self.assertEqual(len(v['query']['queryState'][role]['projections']),depth);self.assertTrue(v['drillFilterOtherVisuals'])
    def test_roster_correct_measure(self):
        v=visual('overview','roster');self.assertEqual(v['visualType'],'tableEx')
        cols=v['query']['queryState']['Values']['projections']
        self.assertEqual([next(iter(p['field'].values()))['Property'] for p in cols],['Roster Bib','Rider','Team','Rider Country'])
    def test_stage_selector_and_awards(self):
        v=visual('stages','stage_pick')
        self.assertEqual(v['visualType'],'advancedSlicerVisual')
        self.assertEqual(v['objects']['selection'][0]['properties']['strictSingleSelect']['expr']['Literal']['Value'],'true')
        data=DATA['Stage'];self.assertEqual([s['Stage'] for s in data],list(range(1,22)))
        winner=visual('classifications','winners')['query']['queryState']['Values']['projections']
        self.assertEqual([next(iter(p['field'].values()))['Property'] for p in winner],['Classification','Award leaders','Winning score','Winning rule'])
    def test_readability_and_series(self):
        for file in FILES:
            v=json.loads(file.read_text())['visual']
            if v['visualType'] in ['tableEx','pivotTable']:self.assertEqual(v['objects']['grid'][0]['properties']['textSize']['expr']['Literal']['Value'],'14D')
        self.assertEqual(visual('terrain','mountain_podiums')['visualType'],'clusteredBarChart')
    def test_eligible_first_sort(self):
        sorts=visual('classifications','comparison')['query']['sortDefinition']['sort']
        self.assertEqual([s['field']['Measure']['Property'] for s in sorts],['Rider Status','GC Rank'])
    def test_self_contained_model(self):
        tmdl=list((ROOT/'Tour de France.SemanticModel/definition/tables').glob('*.tmdl'))
        self.assertEqual(len(tmdl),12)
        for file in tmdl:
            text=file.read_text(encoding='utf-8-sig');self.assertNotIn('File.Contents(',text);self.assertIn('#table(',text)
if __name__=='__main__':unittest.main(verbosity=2)
