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
        self.assertEqual(order['pageOrder'],['overview','stages','classifications','teams','countries','guide'])
        self.assertEqual(len(FILES),74)
    def test_bindings(self):
        for file in FILES:
            for kind,f in fields(json.loads(file.read_text())):
                table=f['Expression']['SourceRef']['Entity'];name=f['Property']
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
        for pg,n,role,depth in [('overview','team_rider','Category',2),('stages','stage_matrix','Rows',4),('teams','detail','Rows',2),('countries','roster','Rows',3)]:
            v=visual(pg,n);self.assertEqual(len(v['query']['queryState'][role]['projections']),depth);self.assertTrue(v['drillFilterOtherVisuals'])
    def test_roster_correct_measure(self):
        self.assertEqual(visual('countries','roster')['query']['queryState']['Values']['projections'][0]['field']['Measure']['Property'],'Roster Riders')
    def test_readability_and_series(self):
        for file in FILES:
            v=json.loads(file.read_text())['visual']
            if v['visualType'] in ['tableEx','pivotTable']:self.assertEqual(v['objects']['grid'][0]['properties']['textSize']['expr']['Literal']['Value'],'14')
        self.assertNotIn('dataPoint',visual('teams','team_trend')['objects'])
    def test_eligible_first_sort(self):
        sorts=visual('classifications','comparison')['query']['sortDefinition']['sort']
        self.assertEqual([s['field']['Measure']['Property'] for s in sorts],['Rider Status','GC Rank'])
    def test_self_contained_model(self):
        tmdl=list((ROOT/'Tour de France.SemanticModel/definition/tables').glob('*.tmdl'))
        self.assertEqual(len(tmdl),11)
        for file in tmdl:
            text=file.read_text(encoding='utf-8-sig');self.assertNotIn('File.Contents(',text);self.assertIn('#table(',text)
if __name__=='__main__':unittest.main(verbosity=2)
