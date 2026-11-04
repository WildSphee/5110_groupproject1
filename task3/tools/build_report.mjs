import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const report=path.join(root,'Tour de France.Report');
const base='https://developer.microsoft.com/json-schemas/fabric/item/report/';
const schema=(type,v='1.0.0')=>base+'definition/'+type+'/'+v+'/schema.json';
const write=(f,d)=>{fs.mkdirSync(path.dirname(f),{recursive:true});fs.writeFileSync(f,JSON.stringify(d,null,2));};
const lit=v=>({expr:{Literal:{Value:typeof v==='string'?"'"+v.replaceAll("'","''")+"'":(typeof v==='number'?String(v)+'D':String(v))}}});
const color=v=>({solid:{color:lit(v)}});
const ink='#182B3A', muted='#526372', teal='#087F8C', gold='#D5A51C', coral='#DC715B', violet='#7963AD', bg='#F2F5F7';
const palette=[teal,gold,violet,coral,'#397BBB','#62A887'];
const col=(t,n)=>({Column:{Expression:{SourceRef:{Entity:t}},Property:n}});
const met=n=>({Measure:{Expression:{SourceRef:{Entity:'Metrics'}},Property:n}});
const labels={'Rider Label':'Rider','GC Rank':'GC rank','Points Rank':'Points rank','KOM Rank':'KOM rank','Young Rank':'Young rank','Rider Cumulative Time':'Time (h:mm:ss)','Cumulative Points':'Points','Cumulative KOM Points':'KOM points','Rider Status':'Status','Team Cumulative Hours':'Top-3 hours','Best Team Rank':'Team rank','Stages Scored':'Stages scored','Team Coverage':'Coverage','Roster Riders':'Riders','Finish Seconds':'Finish (s)','Bonus Seconds':'Bonus (s)','Penalty Seconds':'Penalty (s)','Adjusted Seconds':'Adjusted (s)','Stage Position':'Position'};
const p=(t,n,active)=>({field:t==='Metrics'?met(n):col(t,n),queryRef:t+'.'+n,nativeQueryRef:labels[n]||n,...(active===undefined?{}:{active})});
Object.assign(labels,{'Roster Bib':'Bib','Award leaders':'Leading rider(s)','Winning rule':'How to win','GC daily deficit seconds':'Gap to leader (s)','Team deficit minutes':'Gap (min)','Rider Country':'Nationality','GC Rank Change':'Places gained / lost','Stages Scored':'Stages scored','Top Ten Position':'Place','Top Ten Adjusted Seconds':'Adjusted (s)'});
const m=n=>p('Metrics',n);
const pages=[['overview','01  Race & participation'],['stages','02  Stages & routes'],['classifications','03  Classifications'],['teams','04  Team performance'],['story','05  GC progression'],['terrain','06  Terrain & consistency'],['scenarios','07  GC what-if']];
write(path.join(root,'Tour de France.pbip'),{$schema:'https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json',version:'1.0',artifacts:[{report:{path:'Tour de France.Report'}}],settings:{enableAutoRecovery:true}});
write(path.join(root,'Tour de France.SemanticModel/definition.pbism'),{$schema:'https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json',version:'4.0',settings:{}});
write(path.join(report,'definition.pbir'),{$schema:base+'definitionProperties/2.0.0/schema.json',version:'4.0',datasetReference:{byPath:{path:'../Tour de France.SemanticModel'}}});
write(path.join(report,'definition/version.json'),{$schema:schema('versionMetadata'),version:'2.0.0'});
write(path.join(report,'StaticResources/RegisteredResources/RacePalette.json'),{name:'RacePalette',dataColors:palette,background:bg,foreground:ink,tableAccent:teal,visualStyles:{advancedSlicerVisual:{'*':{layout:[{orientation:0,rowCount:1,columnCount:21,maxTiles:21,autoGrid:false,showFixedSize:false,rowPadding:2,columnPadding:2}],value:[{show:true,fontSize:12}]}}},textClasses:{title:{fontFace:'Segoe UI Semibold',color:ink},label:{fontFace:'Segoe UI',color:muted}}});
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
function slicer(pg,name,x,y,w,h,title,t,n,mode='Dropdown'){
 visual(pg,name,'slicer',x,y,w,h,title,{Values:{projections:[p(t,n)]}},
 {data:[{properties:{mode:lit(mode)}}],selection:[{properties:{singleSelect:lit(false),selectAllCheckboxEnabled:lit(false)}}],items:[{properties:{fontSize:lit(12)}}]});
}
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
  grid:[{properties:{textSize:lit(14),rowPadding:lit(5),gridVertical:lit(false),gridHorizontal:lit(true)}}],
  columnHeaders:[{properties:{fontSize:lit(13),fontColor:color(ink),backColor:color('#EEF2F4')}}],
  rowHeaders:[{properties:{fontSize:lit(13),stepped:lit(true),showExpandCollapseButtons:lit(true)}}],
  values:[{properties:{fontSize:lit(13)}}],
  total:[{properties:{totals:lit(false)}}],
  subTotals:[{properties:{rowSubtotals:lit(false),columnSubtotals:lit(false)}}]
 });
}
function table(pg,name,x,y,w,h,title,fields,sort){visual(pg,name,'tableEx',x,y,w,h,title,{Values:{projections:fields.map(f=>typeof f==='string'?m(f):p(...f))}},
 {grid:[{properties:{textSize:lit(14),rowPadding:lit(5),gridVertical:lit(false)}}],columnHeaders:[{properties:{fontSize:lit(13),fontColor:color(ink),backColor:color('#EEF2F4')}}],values:[{properties:{fontSize:lit(13)}}],total:[{properties:{totals:lit(false)}}]},sort);}
for(const [pg,label] of pages){
 write(path.join(report,`definition/pages/${pg}/page.json`),{$schema:schema('page'),name:pg,displayName:label,displayOption:'FitToPage',width:1440,height:900,objects:{background:[{properties:{color:color(bg),transparency:lit(0)}}]}});
 text(pg,'title',24,12,760,68,label.slice(4),26,ink,true);
 text(pg,'demo',1148,14,264,48,'BT5110  /  SYNTHETIC RACE',11,teal,true);
}
const asof=pg=>slicer(pg,'asof',830,8,290,74,'Standings after stage','As Of','As of Stage');

// Participation comes from registered nationality, not the country of a rider's team.
visual('overview','riders_country','azureMap',24,94,680,306,'Rider participation by country',{
 Category:{projections:[p('Country','Country',true)]},Size:{projections:[m('Riders by Country')]},
 Tooltips:{projections:[m('Teams by Country'),m('Country Wins'),m('Country Podiums')]}
},{bubbleLayer:[{properties:{show:lit(true),sizeByValue:lit(true),fillColor:color(teal)}}]});
chart('overview','teams_country','clusteredColumnChart',720,94,696,306,'Registered teams and riders by country',[['Country','Country']],['Teams by Country','Riders by Country']);
chart('overview','team_rider','clusteredBarChart',24,416,680,224,'Adjusted rider-hours by team',[['Rider','Team'],['Rider','Rider Label']],['Country Rider Hours']);
visual('overview','squad_depth','treemap',720,416,696,224,'Registered squad size',{
 Group:{projections:[p('Rider','Team',true),p('Rider','Rider Label',false)]},Values:{projections:[m('Roster Riders')]}},{labels:[{properties:{show:lit(true)}}]});
table('overview','roster',24,656,680,220,'Riders in the selection',['Roster Bib',['Rider','Rider'],['Rider','Team'],['Rider','Rider Country']],[col('Rider','Rider'),'Ascending']);
table('overview','outcomes',720,656,696,220,'Results by rider nationality',[['Country','Country'],'Country Best GC Rank','Country Wins','Country Podiums'],[met('Country Wins'),'Descending']);

// A route or matrix row selects a stage; the stage key keeps each top-ten result separate.
visual('stages','stage_pick','advancedSlicerVisual',24,86,1392,79,'Stage',{Values:{projections:[p('Stage','Stage',true)]}},{layout:[{properties:{orientation:{expr:{Literal:{Value:'0D'}}},rowCount:{expr:{Literal:{Value:'1D'}}},columnCount:{expr:{Literal:{Value:'21D'}}},maxTiles:{expr:{Literal:{Value:'21D'}}},autoGrid:lit(false),columnPadding:{expr:{Literal:{Value:'2D'}}}}}],value:[{properties:{fontSize:lit(12)}}]},[col('Stage','Stage'),'Ascending']);
defaultSelection('stages','stage_pick','Stage','Stage',[1],true);
{const f=path.join(report,'definition/pages/stages/visuals/stage_pick/visual.json'),v=JSON.parse(fs.readFileSync(f));v.visual.objects.selection[0].properties.strictSingleSelect=lit(true);write(f,v);}
matrix('stages','stage_matrix',24,529,780,347,'Stage results and time adjustments',[['Stage','Stage Type'],['Stage','Stage Label'],['Rider','Team'],['Rider','Rider Label']],['Finish Seconds','Bonus Seconds','Penalty Seconds','Adjusted Seconds','Stage Position']);
table('stages','routes',820,181,596,125,'Selected route and stage winner',[['Stage','Stage Label'],['Stage','Stage Type'],['Stage','Date'],'Stage Distance km','Stage Winner'],[met('Stage Distance km'),'Descending']);
table('stages','finishers',24,181,780,332,'Stage finish order • first ten riders',[['Stage','Stage'],['Rider','Rider Label'],['Rider','Team'],['Rider','Rider Country'],'Top Ten Position','Top Ten Adjusted Seconds'],[[col('Stage','Stage'),'Ascending'],[met('Top Ten Position'),'Ascending']]);
chart('stages','finish_gaps','clusteredBarChart',820,529,596,347,'Top ten: seconds behind the first finisher',[['Rider','Rider Label']],['Top Ten Finish Gap'],{sort:[met('Top Ten Finish Gap'),'Ascending']});
chart('stages','squads','donutChart',820,322,596,191,'Top-ten finishes by team',[['Rider','Team']],['Top Ten Finishes'],{legend:['Rider','Team']});

asof('classifications');
table('classifications','winners',24,94,1392,226,'Classification leaders after the selected stage', [['Classification','Classification'],'Award leaders','Winning score','Winning rule'],[col('Classification','Classification'),'Ascending']);
table('classifications','comparison',24,336,1392,252,'All riders • standings and gap to GC leader',[['Rider','Rider Label'],'GC Rank','Points Rank','KOM Rank','Young Rank','Rider Cumulative Time','GC Gap Seconds','Cumulative Points','Cumulative KOM Points','Rider Status'],[[met('Rider Status'),'Ascending'],[met('GC Rank'),'Ascending']]);
table('classifications','class_hours',24,604,812,272,'Age and mountain time rankings',[['Rider','Rider Label'],['Rider','Age at Race Start'],'GC Rank','Young GC at Race Start Rank','Mountain GC Proxy Rank'],[met('GC Rank'),'Ascending']);
chart('classifications','eligible_hours','clusteredBarChart',852,604,564,272,'Cumulative rider-hours by classification',[['Classification','Classification']],['Classification Rider Hours']);

asof('teams');
table('teams','ranking',24,94,690,330,'Best Team • most stages scored, then shortest time',['Best Team Rank',['Team','Team'],'Team Cumulative Hours','Stages Scored','Team Coverage'],[met('Best Team Rank'),'Ascending']);
chart('teams','team_gap','clusteredBarChart',730,94,686,330,'Minutes behind the leader • same stage coverage',[['Team','Team']],['Team deficit minutes'],{sort:[met('Team deficit minutes'),'Ascending']});
matrix('teams','detail',24,440,1392,436,'Stage scores • sum of the three fastest finishers per team',[['Team','Team'],['Stage','Stage Label']],['Stage Top3 Hours','Team Finishers']);

slicer('story','rider',24,94,244,782,'Contenders','Rider','Rider Label','Basic');
defaultSelection('story','rider','Rider','Rider Label',['Alex Laurent (1)'],true);
chart('story','gc_trace','lineChart',284,94,680,374,'Time behind the GC leader (seconds) • zero is the lead',[['Stage','Stage']],['GC daily deficit seconds'],{legend:['Rider','Rider Label']});
chart('story','rank_changes','clusteredColumnChart',980,94,436,374,'Change in GC position • positive means gained',[['Stage','Stage']],['GC Rank Change'],{legend:['Rider','Rider Label'],sort:[col('Stage','Stage'),'Ascending']});
table('story','daily',284,484,680,392,'Daily GC positions',[['Stage','Stage'],['Stage','Stage Type'],['Rider','Rider Label'],'GC Trace Rank','GC daily deficit seconds','GC Rank Change','Adjusted Seconds'],[col('Stage','Stage'),'Ascending']);
chart('story','mountain_markers','lineChart',980,484,436,392,'Cumulative time (hours) • all days and mountain days',[['Stage','Stage']],['GC Trace Hours','Mountain Trace Hours']);

chart('terrain','speed','clusteredColumnChart',24,94,680,374,'Average speed by terrain and team (km/h)',[['Stage','Stage Type']],['Speed Proxy kmh'],{legend:['Rider','Team']});
chart('terrain','mountain_podiums','clusteredBarChart',720,94,696,374,'Who finished in the top three on mountain stages?',[['Rider','Rider Label']],['Mountain podium finishes'],{color:violet});
chart('terrain','top_ten','barChart',24,484,680,392,'Top-ten finishes by team and terrain',[['Rider','Team'],['Rider','Rider Label']],['Top Ten Finishes'],{legend:['Stage','Stage Type']});
matrix('terrain','evidence',720,484,696,392,'Performance by rider and stage',[['Rider','Rider Label'],['Stage','Stage Label'],['Stage','Stage Type']],['Top Ten Finishes','Mountain Podiums','Stage Winner Gap Seconds','Speed Proxy kmh']);

asof('scenarios');
slicer('scenarios','scenario',24,94,284,268,'Timing rules','Scenario','Scenario','Basic');
defaultSelection('scenarios','scenario','Scenario','Scenario',['Official adjusted'],true);
table('scenarios','comparison',324,94,1092,394,'Official and scenario standings',[['Rider','Rider Label'],'Rider Status','GC Rank','Scenario GC Rank','Scenario Rank Change','Top Ten Movement','Cumulative Bonus Seconds','Cumulative Penalty Seconds'],[[met('Rider Status'),'Ascending'],[met('Scenario GC Rank'),'Ascending']]);
chart('scenarios','adjustments','clusteredBarChart',24,504,622,372,'Bonuses and penalties by rider (seconds)',[['Rider','Rider Label']],['Cumulative Bonus Seconds','Cumulative Penalty Seconds']);
visual('scenarios','net_adjustments','waterfallChart',662,504,754,372,'Scenario time adjustments by stage (seconds)',{
 Category:{projections:[p('Stage','Stage',true)]},Y:{projections:[m('Scenario Stage Adjustment Seconds')]}
},{},[col('Stage','Stage'),'Ascending']);

// Prune obsolete generated definitions, never remove other files or follow symlinks.
const pageRoot=path.resolve(report,'definition/pages');
const active=new Set(pages.map(([id])=>id));
const wanted=new Set(manifest.map(v=>v.page+'/'+v.name));
for(const entry of fs.readdirSync(pageRoot,{withFileTypes:true})){
 if(!entry.isDirectory())continue;
 const pg=entry.name, dir=path.resolve(pageRoot,pg);
 if(!dir.startsWith(pageRoot+path.sep) || fs.realpathSync(dir)!==dir)throw Error('Unexpected page directory: '+dir);
 const visuals=path.join(dir,'visuals');
 if(fs.existsSync(visuals)){
  if(fs.realpathSync(visuals)!==visuals)throw Error('Unexpected visuals directory');
  for(const v of fs.readdirSync(visuals,{withFileTypes:true})){
   if(!v.isDirectory()||wanted.has(pg+'/'+v.name))continue;
   const folder=path.join(visuals,v.name), file=path.join(folder,'visual.json');
   if(fs.realpathSync(folder)!==folder)throw Error('Unexpected visual directory');
   if(fs.existsSync(file))fs.unlinkSync(file);
   if(!fs.readdirSync(folder).length)fs.rmdirSync(folder);
  }
  if(!fs.readdirSync(visuals).length)fs.rmdirSync(visuals);
 }
 if(!active.has(pg)){
  const f=path.join(dir,'page.json');if(fs.existsSync(f))fs.unlinkSync(f);
  if(!fs.readdirSync(dir).length)fs.rmdirSync(dir);
 }
}
write(path.join(root,'review/visual-manifest.json'),manifest);
console.log(`Built ${pages.length} pages; ${manifest.length} native visuals.`);
