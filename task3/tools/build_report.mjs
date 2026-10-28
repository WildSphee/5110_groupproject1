import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const report=path.join(root,'Tour de France.Report');
const base='https://developer.microsoft.com/json-schemas/fabric/item/report/';
const schema=(type,v='1.0.0')=>base+'definition/'+type+'/'+v+'/schema.json';
const write=(f,d)=>{fs.mkdirSync(path.dirname(f),{recursive:true});fs.writeFileSync(f,JSON.stringify(d,null,2));};
const lit=v=>({expr:{Literal:{Value:typeof v==='string'?"'"+v.replaceAll("'","''")+"'":String(v)}}});
const color=v=>({solid:{color:lit(v)}});
const ink='#182B3A', muted='#526372', teal='#087F8C', gold='#D5A51C', coral='#DC715B', violet='#7963AD', bg='#F2F5F7';
const palette=[teal,gold,violet,coral,'#397BBB','#62A887'];
const col=(t,n)=>({Column:{Expression:{SourceRef:{Entity:t}},Property:n}});
const met=n=>({Measure:{Expression:{SourceRef:{Entity:'Metrics'}},Property:n}});
const labels={'Rider Label':'Rider','GC Rank':'GC rank','Points Rank':'Points rank','KOM Rank':'KOM rank','Young Rank':'Young rank','Rider Cumulative Time':'Time (h:mm:ss)','Cumulative Points':'Points','Cumulative KOM Points':'KOM points','Rider Status':'Status','Team Cumulative Hours':'Top-3 hours','Best Team Rank':'Team rank','Stages Scored':'Stages scored','Team Coverage':'Coverage','Roster Riders':'Riders','Finish Seconds':'Finish (s)','Bonus Seconds':'Bonus (s)','Penalty Seconds':'Penalty (s)','Adjusted Seconds':'Adjusted (s)','Stage Position':'Position'};
const p=(t,n,active)=>({field:t==='Metrics'?met(n):col(t,n),queryRef:t+'.'+n,nativeQueryRef:labels[n]||n,...(active===undefined?{}:{active})});
const m=n=>p('Metrics',n);
const pages=[['overview','01  Race overview'],['stages','02  Stage explorer'],['classifications','03  Classifications'],['teams','04  Team performance'],['countries','05  Country participation'],['story','06  GC storyline'],['terrain','07  Terrain & consistency'],['stage_focus','08  Routes & stage focus'],['scenarios','09  GC what-if'],['guide','10  Guide & definitions']];
write(path.join(root,'Tour de France.pbip'),{$schema:'https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json',version:'1.0',artifacts:[{report:{path:'Tour de France.Report'}}],settings:{enableAutoRecovery:true}});
write(path.join(root,'Tour de France.SemanticModel/definition.pbism'),{$schema:'https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json',version:'4.0',settings:{}});
write(path.join(report,'definition.pbir'),{$schema:base+'definitionProperties/2.0.0/schema.json',version:'4.0',datasetReference:{byPath:{path:'../Tour de France.SemanticModel'}}});
write(path.join(report,'definition/version.json'),{$schema:schema('versionMetadata'),version:'2.0.0'});
write(path.join(report,'StaticResources/RegisteredResources/RacePalette.json'),{name:'RacePalette',dataColors:palette,background:bg,foreground:ink,tableAccent:teal,textClasses:{title:{fontFace:'Segoe UI Semibold',color:ink},label:{fontFace:'Segoe UI',color:muted}}});
write(path.join(report,'definition/report.json'),{$schema:schema('report'),themeCollection:{customTheme:{name:'RacePalette',reportVersionAtImport:'5.50',type:'RegisteredResources'}},resourcePackages:[{name:'RegisteredResources',type:'RegisteredResources',items:[{name:'RacePalette',path:'RacePalette.json',type:'CustomTheme'}]}],layoutOptimization:'None',settings:{useStylableVisualContainerHeader:true,defaultDrillFilterOtherVisuals:true,defaultFilterActionIsDataFilter:true}});
write(path.join(report,'definition/pages/pages.json'),{$schema:schema('pagesMetadata'),pageOrder:pages.map(x=>x[0]),activePageName:'overview'});
let z=0;
const manifest=[];
function visual(pg,name,type,x,y,w,h,title,queryState,objects={},sort){
 const v={visualType:type,objects,visualContainerObjects:{
  title:[{properties:{show:lit(!!title),text:lit(title),fontSize:lit(13),fontColor:color(ink),fontFamily:lit('Segoe UI Semibold')}}],
  background:[{properties:{show:lit(true),color:color('#FFFFFF'),transparency:lit(0)}}],
  border:[{properties:{show:lit(false)}}],
  visualTooltip:[{properties:{type:lit('Default')}}]},drillFilterOtherVisuals:true};
 if(queryState)v.query={queryState,...(sort?{sortDefinition:{sort:(Array.isArray(sort[0])?sort:[sort]).map(([field,direction])=>({field,direction})),isDefaultSort:true}}:{})};
 const data={$schema:schema('visualContainer','2.0.0'),name,position:{x,y,width:w,height:h,z:z++,tabOrder:z},visual:v};
 write(path.join(report,`definition/pages/${pg}/visuals/${name}/visual.json`),data);
 manifest.push({page:pg,name,type,title,x,y,width:w,height:h,fields:queryState});
}
function text(pg,name,x,y,w,h,value,size=13,c=muted,bold=false){
 visual(pg,name,'textbox',x,y,w,h,'',undefined,{general:[{properties:{paragraphs:value.split('\n').map(value=>({textRuns:[{value,textStyle:{fontFamily:'Segoe UI',fontSize:size+'pt',color:c,fontWeight:bold?'bold':'normal'}}]}))}}]});
}
function card(pg,name,x,y,w,title,metric,c=teal){visual(pg,name,'card',x,y,w,105,title,{Values:{projections:[m(metric)]}},
 {labels:[{properties:{color:color(c),fontSize:lit(30),labelDisplayUnits:lit(0),displayUnits:lit(0)}}],categoryLabels:[{properties:{show:lit(false)}}]});}
function slicer(pg,name,x,w,title,t,n){visual(pg,name,'slicer',x,109,w,88,title,{Values:{projections:[p(t,n)]}},
 {data:[{properties:{mode:lit('Dropdown')}}],selection:[{properties:{singleSelect:lit(false),selectAllCheckboxEnabled:lit(true)}}],items:[{properties:{fontSize:lit(12)}}]});}
function defaultSelection(pg,name,t,n,values,single=false){
 const file=path.join(report,`definition/pages/${pg}/visuals/${name}/visual.json`);
 const data=JSON.parse(fs.readFileSync(file,'utf8'));
 data.visual.objects.general=[{properties:{filter:{Version:2,From:[{Name:'s',Entity:t,Type:0}],Where:[{Condition:{In:{Expressions:[{Column:{Expression:{SourceRef:{Source:'s'}},Property:n}}],Values:values.map(v=>[{Literal:{Value:typeof v==='number'?String(v)+ 'L':"'"+v.replaceAll("'","''")+"'"}}])}}}]}}}];
 data.visual.objects.selection=[{properties:{singleSelect:lit(single),selectAllCheckboxEnabled:lit(!single)}}];
 data.visual.objects.general[0].properties.filter={filter:data.visual.objects.general[0].properties.filter};
 write(file,data);
}
function chart(pg,name,type,x,y,w,h,title,levels,metrics,options={}){
 const qs={Category:{projections:levels.map(([t,n],i)=>p(t,n,i===0))},Y:{projections:metrics.map(m)}};
 if(options.legend && type!=='donutChart')qs.Series={projections:[p(...options.legend)]};
 visual(pg,name,type,x,y,w,h,title,qs,{
  ...(options.legend||metrics.length>1?{}:{dataPoint:[{properties:{defaultColor:color(options.color||teal)}}]}),
  categoryAxis:[{properties:{show:lit(true),fontSize:lit(11),titleFontSize:lit(11)}}],
  valueAxis:[{properties:{show:lit(true),fontSize:lit(11),labelDisplayUnits:lit(1)}}],
  legend:[{properties:{show:lit(!!options.legend||metrics.length>1),fontSize:lit(11)}}],
  labels:[{properties:{show:lit(type!=='lineChart'),fontSize:lit(10),labelDisplayUnits:lit(1)}}]
 },options.sort||(type==='lineChart'?[col(...levels[0]),'Ascending']:[met(metrics[0]),'Descending']));
}
function matrix(pg,name,x,y,w,h,title,rows,values,columns){
 const qs={Rows:{projections:rows.map(([t,n],i)=>p(t,n,i===0))},Values:{projections:values.map(m)}};
 if(columns)qs.Columns={projections:columns.map(([t,n])=>p(t,n,true))};
 visual(pg,name,'pivotTable',x,y,w,h,title,qs,{
  grid:[{properties:{textSize:lit(14),rowPadding:lit(9),gridVertical:lit(false),gridHorizontal:lit(true)}}],
  columnHeaders:[{properties:{fontSize:lit(13),fontColor:color(ink),backColor:color('#EEF2F4')}}],
  rowHeaders:[{properties:{fontSize:lit(13),stepped:lit(true),showExpandCollapseButtons:lit(true)}}],
  values:[{properties:{fontSize:lit(13)}}],
  total:[{properties:{totals:lit(false)}}],
  subTotals:[{properties:{rowSubtotals:lit(false),columnSubtotals:lit(false)}}]
 });
}
function table(pg,name,x,y,w,h,title,fields,sort){visual(pg,name,'tableEx',x,y,w,h,title,{Values:{projections:fields.map(f=>typeof f==='string'?m(f):p(...f))}},
 {grid:[{properties:{textSize:lit(14),rowPadding:lit(9),gridVertical:lit(false)}}],columnHeaders:[{properties:{fontSize:lit(13),fontColor:color(ink),backColor:color('#EEF2F4')}}],values:[{properties:{fontSize:lit(13)}}],total:[{properties:{totals:lit(false)}}]},sort);}
for(const [pg,label]of pages){
 write(path.join(report,`definition/pages/${pg}/page.json`),{$schema:schema('page'),name:pg,displayName:label,displayOption:'FitToPage',width:1440,height:900,objects:{background:[{properties:{color:color(bg),transparency:lit(0)}}]}});
 text(pg,'brand',28,2,1060,40,'TOUR DE FRANCE  /  ANALYTICS LAB',11,teal,true);
 text(pg,'title',28,44,1376,63,label.slice(4),24,ink,true);
 text(pg,'demo',1120,2,292,40,'SYNTHETIC DATA  •  BT5110 / GROUP 5',10,muted,true);
 text(pg,'footer',28,850,1376,46,'FICTIONAL 2026 RACE  |  Select a mark to cross-filter; click it again to clear. Page tabs below navigate. Definitions & demo steps: page 10.',10,muted);
}
slicer('overview','asof',28,260,'Standings as of (latest selected)','As Of','As of Stage');
slicer('overview','team',308,340,'Rider team','Rider','Team');
text('overview','context',672,109,740,88,'THE RACE AT A GLANCE\nNo stage selection = stage 21. Rankings stay global when you filter a team. All people, scores and results are fictional.',12);
card('overview','eligible',28,216,326,'Riders still eligible','Eligible Riders');
card('overview','exited',374,216,326,'Riders exited by selected stage','Exited Riders', '#B34B39');
card('overview','hours',720,216,346,'Eligible rider-hours • cumulative','Eligible Cumulative Hours',gold);
card('overview','registered',1086,216,326,'Registered riders • selected teams','Registered Riders',violet);
chart('overview','team_rider','clusteredBarChart',28,345,704,327,'Whole-race time contribution  |  Team → Rider',[['Rider','Team'],['Rider','Rider Label']],['Adjusted Hours'],{color:teal});
table('overview','gc',752,345,660,327,'General classification • global rank', [['Rider','Rider Label'],'GC Rank','Rider Cumulative Time','GC Gap Seconds'],[met('GC Rank'),'Ascending']);
visual('overview','drill_help','treemap',28,696,704,145,'Squad depth • registered riders • Team → Rider',{Group:{projections:[p('Rider','Team',true),p('Rider','Rider Label',false)]},Values:{projections:[m('Registered Riders')]}},{labels:[{properties:{show:lit(true)}}]});
text('overview','insight',752,696,660,145,'EXPLORE THE FIELD\nThe bar chart adds all completed race effort, including days before exit. Drill Team → Rider, then explore daily profiles on pages 02 and 06. The treemap shows roster depth; page 04 uses the separate fastest-three team score.',13,ink);

slicer('stages','type',28,316,'Stage type','Stage','Stage Type');
slicer('stages','stage',364,420,'Stage / route','Stage','Stage Label');
slicer('stages','team',804,292,'Rider team','Rider','Team');
slicer('stages','rider',1116,296,'Rider (search dropdown)','Rider','Rider Label');
card('stages','finishes',28,216,326,'Completed rider-stage results','Stage Finishes');
card('stages','time',374,216,326,'Adjusted time • rider-hours','Adjusted Hours');
card('stages','bonus',720,216,326,'Time bonuses • seconds','Bonus Seconds');
card('stages','penalty',1066,216,346,'Time penalties • seconds','Penalty Seconds','#B34B39');
matrix('stages','stage_matrix',28,345,894,487,'Expand +  |  Stage type → Stage → Team → Rider', [['Stage','Stage Type'],['Stage','Stage Label'],['Rider','Team'],['Rider','Rider Label']],['Finish Seconds','Bonus Seconds','Penalty Seconds','Adjusted Seconds','Stage Position']);
chart('stages','trend','lineChart',942,345,470,290,'Cumulative completed effort • rider-hours',[['Stage','Stage']],['Running Rider Hours']);
text('stages','help',942,656,470,176,'DRILL & CHECK\nUse + on a matrix row or the drill arrows. At rider level: adjusted = finish − bonus + penalty. Position appears only for one rider on one stage.\nThe trend includes all prior stage types and effort before exit.',12,ink);

slicer('classifications','asof',28,300,'Standings as of (latest selected)','As Of','As of Stage');
slicer('classifications','team',348,340,'Rider team','Rider','Team');
slicer('classifications','rider',708,350,'Rider','Rider','Rider Label');
text('classifications','units',1078,109,334,88,'TIME ↓ wins GC / Young\nPOINTS ↑ wins Points / Mountains\nRanks are global, not re-ranked.',11,ink);
table('classifications','comparison',28,216,1384,370,'Compare every classification • scroll for all riders; click a header to sort',
 [['Rider','Rider Label'],'GC Rank','Points Rank','KOM Rank','Young Rank','Rider Cumulative Time','Cumulative Points','Cumulative KOM Points','Rider Status'],[[met('Rider Status'),'Ascending'],[met('GC Rank'),'Ascending']]);
table('classifications','class_hours',28,610,884,222,'Parallel time rankings • race-start age and mountain proxy',[['Rider','Rider Label'],['Rider','Age at Race Start'],'GC Rank','Young GC at Race Start Rank','Mountain GC Proxy Rank'],[met('GC Rank'),'Ascending']);
text('classifications','rules',932,610,480,222,'COMPARE LIKE WITH LIKE\nUpper table: original calendar-year Young rule and KOM points. Lower table: under 26 at race start and Mountain-only adjusted time. The mountain proxy is not the KOM jersey.\nRanks stay global. Exited riders are excluded; ties share competition rank.',12,ink);

slicer('teams','asof',28,300,'Standings as of (latest selected)','As Of','As of Stage');
slicer('teams','team',348,400,'Team (team nationality context)','Team','Team');
text('teams','explain',768,109,644,88,'BEST TEAM = SUM OF EACH STAGE’S FASTEST THREE\nRank: stages scored descending, then total time ascending. A stage with fewer than 3 finishers does not count.',12,ink);
table('teams','ranking',28,216,740,280,'Best Team standings • incomplete coverage stays visible',[['Team','Team'],'Best Team Rank','Team Cumulative Hours','Stages Scored','Team Coverage'],[met('Best Team Rank'),'Ascending']);
chart('teams','team_trend','lineChart',788,216,624,280,'Top-three time by stage • hours',[['Stage','Stage']],['Stage Top3 Hours'],{legend:['Team','Team']});
matrix('teams','detail',28,520,900,312,'Expand +  |  Team → Stage  •  inspect finishers & top-three hours',[['Team','Team'],['Stage','Stage Label']],['Stage Top3 Hours','Team Finishers']);
text('teams','team_help',948,520,464,312,'INCOMPLETE IS NOT FASTER\nNorthstar Velo drops to two riders at stage 18. Its later top-three values are blank, never zero. Its shorter total must not win the team classification.\nThe chart and matrix show the whole race for stage diagnosis. The as-of selector controls only the standings table.\nTeam nationality is separate from rider nationality on page 05.',13,ink);

slicer('countries','country',28,400,'Country • both participation measures','Country','Country');
text('countries','scope',448,109,964,88,'REGISTRATION, NOT RACE SURVIVAL\nTeams use team nationality; riders use rider nationality. Exited riders remain registered participants. Countries with zero teams and riders remain visible.',13,ink);
card('countries','teams',28,216,326,'Registered teams • selected countries','Teams by Country');
card('countries','riders',374,216,326,'Registered riders • selected countries','Riders by Country');
card('countries','foreign',720,216,346,'Riders on foreign-country teams','Country Foreign Riders',violet);
card('countries','represented',1086,216,326,'Countries represented • whole race','Countries Represented',gold);
visual('countries','riders_country','azureMap',28,345,680,300,'Where the peloton comes from • registered riders',{
 Category:{projections:[p('Country','Country',true)]},Size:{projections:[m('Riders by Country')]},Tooltips:{projections:[m('Teams by Country'),m('Country Wins'),m('Country Podiums')]}
},{bubbleLayer:[{properties:{show:lit(true),sizeByValue:lit(true),fillColor:color(teal)}}]});
chart('countries','teams_country','clusteredColumnChart',728,345,684,300,'Participation by nation • teams and riders',[['Country','Country']],['Teams by Country','Riders by Country']);
matrix('countries','roster',28,665,680,167,'Expand +  |  Rider country → Team → Rider',[['Rider','Rider Country'],['Rider','Team'],['Rider','Rider Label']],['Roster Riders']);
table('countries','outcomes',728,665,684,167,'National outcomes • select a nation to inspect its riders',[['Country','Country'],'Country Best GC Rank','Country Wins','Country Podiums'],[met('Country Best GC Rank'),'Ascending']);

slicer('story','rider',28,360,'GC contender / riders','Rider','Rider Label');
defaultSelection('story','rider','Rider','Rider Label',['Alex Laurent (1)']);
slicer('story','team',408,300,'Rider team','Rider','Team');
text('story','intro',728,109,684,88,'FOLLOW A CONTENDER\nSelect one or a few riders. Positive rank change means places gained; Mountain points identify the terrain.',12,ink);
chart('story','gc_trace','lineChart',28,216,884,340,'GC journey • cumulative adjusted hours',[['Stage','Stage']],['GC Trace Hours'],{legend:['Rider','Rider Label']});
chart('story','rank_changes','clusteredColumnChart',932,216,480,340,'Places gained / lost each day',[['Stage','Stage']],['GC Rank Change'],{legend:['Rider','Rider Label'],sort:[col('Stage','Stage'),'Ascending']});
table('story','daily',28,576,884,256,'Daily evidence • sort places gained to locate a turning point',[['Stage','Stage'],['Stage','Stage Type'],['Rider','Rider Label'],'GC Trace Rank','GC Rank Change','Adjusted Seconds'],[col('Stage','Stage'),'Ascending']);
chart('story','mountain_markers','lineChart',932,576,480,256,'Mountain stages • cumulative hours',[['Stage','Stage']],['Mountain Trace Hours'],{legend:['Rider','Rider Label']});

slicer('terrain','team',28,300,'Rider team','Rider','Team');
slicer('terrain','rider',348,340,'Rider','Rider','Rider Label');
slicer('terrain','type',708,300,'Terrain','Stage','Stage Type');
text('terrain','intro',1028,109,384,88,'DISTANCE / FINISH TIME\nSpeed is a proxy in km/h. Team speed weights each rider’s distance and time.',11,ink);
chart('terrain','speed','clusteredColumnChart',28,216,680,284,'Speed profile • terrain × team',[['Stage','Stage Type']],['Speed Proxy kmh'],{legend:['Rider','Team']});
visual('terrain','mountain_scatter','scatterChart',728,216,684,284,'Mountain specialists • more podiums, smaller gaps',{
 Category:{projections:[p('Rider','Rider Label',true)]},X:{projections:[m('Mountain Mean Gap Seconds')]},Y:{projections:[m('Mountain Podiums')]},Series:{projections:[p('Rider','Team')]}
},{categoryAxis:[{properties:{show:lit(true)}}],valueAxis:[{properties:{show:lit(true)}}],legend:[{properties:{show:lit(true),fontSize:lit(10)}}]});
chart('terrain','top_ten','barChart',28,520,680,312,'Top-ten intensity • Team → Rider',[['Rider','Team'],['Rider','Rider Label']],['Top Ten Finishes'],{legend:['Stage','Stage Type']});
matrix('terrain','evidence',728,520,684,312,'Expand +  |  Rider → Stage → Terrain',[['Rider','Rider Label'],['Stage','Stage Label'],['Stage','Stage Type']],['Top Ten Finishes','Mountain Podiums','Stage Winner Gap Seconds','Speed Proxy kmh']);

slicer('stage_focus','stage',28,450,'Stage / route','Stage','Stage Label');
const routeData=JSON.parse(fs.readFileSync(path.join(root,'data/model_data.json'),'utf8')).Stage;
defaultSelection('stage_focus','stage','Stage','Stage Label',[routeData.toSorted((a,b)=>b['Distance km']-a['Distance km'])[0]['Stage Label']]);
slicer('stage_focus','type',498,300,'Stage type • select ITT for catalogue','Stage','Stage Type');
slicer('stage_focus','team',818,280,'Rider team','Rider','Team');
text('stage_focus','intro',1118,109,294,88,'THE LONG DAY\nOpens on the longest route. Clear Stage to browse all routes or ITT.',11,ink);
table('stage_focus','routes',28,216,1384,238,'Route catalogue • distance descending • filter Individual Time-Trial for ITT',[['Stage','Stage Label'],['Stage','Date'],['Stage','Stage Type'],['Stage','Start'],['Stage','Finish'],'Stage Distance km','Stage Winner'],[met('Stage Distance km'),'Descending']);
table('stage_focus','finishers',28,474,884,358,'Leading finishers • select one stage above',[['Rider','Rider Label'],['Rider','Team'],['Rider','Rider Country'],'Top Ten Position','Top Ten Adjusted Seconds'],[met('Top Ten Position'),'Ascending']);
chart('stage_focus','squads','donutChart',932,474,480,358,'Share of top-ten finishes • team',[['Rider','Team']],['Top Ten Finishes'],{legend:['Rider','Team']});

slicer('scenarios','asof',28,280,'Standings as of','As Of','As of Stage');
slicer('scenarios','scenario',328,400,'Counterfactual • choose one','Scenario','Scenario');
defaultSelection('scenarios','scenario','Scenario','Scenario',['Official adjusted'],true);
slicer('scenarios','team',748,300,'Rider team','Rider','Team');
text('scenarios','intro',1068,109,344,88,'REPLAY THE GC\nNo selection = official. Choose one scenario. Positive movement = places gained.',11,ink);
table('scenarios','comparison',28,216,1384,340,'Official versus counterfactual • global ranks; eligibility held fixed',[['Rider','Rider Label'],'Rider Status','GC Rank','Scenario GC Rank','Scenario Rank Change','Top Ten Movement','Cumulative Bonus Seconds','Cumulative Penalty Seconds'],[[met('Rider Status'),'Ascending'],[met('Scenario GC Rank'),'Ascending']]);
chart('scenarios','adjustments','clusteredBarChart',28,576,884,256,'Cumulative adjustments • bonus and penalty seconds',[['Rider','Rider Label']],['Cumulative Bonus Seconds','Cumulative Penalty Seconds']);
text('scenarios','rules',932,576,480,256,'WHAT CHANGES?\nNo bonuses adds awarded bonus seconds back to adjusted time. No penalties subtracts penalty seconds. Both applies both changes.\nRider eligibility and stage results stay fixed. A scenario may change times without changing ranks or top-ten membership.',13,ink);

text('guide','guide_intro',28,109,1384,80,'DEMO GUIDE  /  A FICTIONAL RACE FOR TESTING\nSeed 5110 • 48 riders • 6 teams • 21 stages • 12 countries. No actual Tour de France results or predictions.',15,ink,true);
text('guide','use',28,216,660,292,'01  INTERACT\nUse page tabs to move between analysis questions. Slicers are local to each page. Open a dropdown to select values; use its eraser to clear. No as-of selection means the final stage; multiple selections use the latest.\nFor charts: select → enable ↓ → click a bar. Use ↑ to roll up. For matrices: expand + or use drill arrows. Select a row or mark to filter other visuals; click it again to clear. In Desktop, Ctrl+click is needed for action buttons only.',14,ink);
text('guide','semantics',708,216,704,292,'02  TIME & ELIGIBILITY\nAdjusted seconds = finish − bonus + penalty. Duration strings use h:mm:ss and never wrap at 24 hours. A rider ranks only if every stage up to the selected stage is complete and they have not exited by then. Historical rankings retain riders who exit later.\nBest Team follows the group report: sum each stage’s fastest 3 adjusted times; rank stages scored first, then time. Cumulative snapshot rows are not added across stages.',14,ink);
text('guide','scoring',28,532,660,300,'03  SYNTHETIC SCORING RULES\nPoints: flat stage top 10 earn 50,30,20,18,16,14,12,10,8,6. Other stages: 25,20,16,12,10,8,6,4,2,1.\nMountains: mountain-stage top 6 earn 10,8,6,4,2,1. Other stages score zero. There are no intermediate sprint or summit events in this demo.\nYoung Rider: born on/after 1 Jan 2001. These are declared demo assumptions, not a claim of official 2026 regulations.',13,ink);
text('guide','walkthrough',708,532,704,300,'04  FIVE-MINUTE DEMO\n1. Overview: drill Alpine Velo into individual riders.\n2. Stage explorer: expand Mountain → a stage → a team → rider; verify the adjusted-time arithmetic.\n3. Classifications: compare stage 06 vs 07 for Avery Laurent (bib 8); the exited rider loses all ranks.\n4. Teams: compare stages 17 and 18 for Northstar Velo.\n5. Countries: France has 2 teams; Singapore and Japan have zero participation. Expand a rider-country row to inspect teams with different nationalities.',13,ink);
write(path.join(root,'review/visual-manifest.json'),manifest);
console.log(`Built ${pages.length} report pages and ${manifest.length} native visuals.`);
