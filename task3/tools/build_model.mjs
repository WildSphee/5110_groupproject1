import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {connect,call} from './mcp.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const tables=JSON.parse(fs.readFileSync(path.join(root,'data/model_data.json'),'utf8'));
tables.Metrics=[{Label:'Measures'}];
const {client}=await connect();
const log=[];
async function op(name,request){const r=await call(client,name,request);log.push({name,operation:request.operation,result:r});fs.writeFileSync(path.join(root,'review/model-build.json'),JSON.stringify(log,null,2));console.log(name,request.operation);return r;}
const connection=process.argv[2];
if(!connection)throw Error('Supply local Power BI connection string');
await op('connection_operations',{operation:'Connect',connectionString:connection});
const definitions=Object.entries(tables).map(([name,rows])=>{
 const cols=Object.keys(rows[0]).map(n=>{
  const sample=rows.map(r=>r[n]).find(v=>v!==null);
  const dataType=typeof sample==='number'?(Number.isInteger(sample)&&n!=='Distance km'?'Int64':'Double'):'String';
  return {name:n,sourceColumn:n,dataType,summarizeBy:'None',isHidden:['Bib','Stage'].includes(n)&&!['Rider','Stage','As Of'].includes(name)};
 });
 const val=v=>v===null?'null':typeof v==='string'?'"'+v.replaceAll('"','""')+'"':String(v);
 const mExpression='let Source = #table(type table ['+cols.map(c=>'#"'+c.name+'" = '+(c.dataType==='String'?'nullable text':c.dataType==='Int64'?'Int64.Type':'number')).join(', ')+'], {\n'+rows.map(r=>'{'+cols.map(c=>val(r[c.name])).join(',')+'}').join(',\n')+'\n}) in Source';
 return {name,description:'Fictional BT5110 demo. See task3/docs/semantics.md for grain and rules.',mExpression,columns:cols};
});
if(!process.argv.includes('--update-measures'))await op('table_operations',{operation:'Create',definitions:process.argv.includes('--resume')?definitions.filter(d=>d.name==='Metrics'):definitions});
const rels=[];
for(const fact of ['Result','Standing'])for(const [dim,col] of [['Rider','Bib'],['Stage','Stage']])rels.push([fact,col,dim,col]);
for(const fact of ['Team Stage','Team Standing'])for(const [dim,col] of [['Team','Team'],['Stage','Stage']])rels.push([fact,col,dim,col]);
if(!process.argv.includes('--resume')&&!process.argv.includes('--update-measures'))await op('relationship_operations',{operation:'Create',definitions:rels.map(([fromTable,fromColumn,toTable,toColumn])=>({
 name:fromTable+'_'+toTable,fromTable,fromColumn,toTable,toColumn,fromCardinality:'Many',toCardinality:'One',crossFilteringBehavior:'OneDirection',isActive:true}))});
const measures=[];
function m(name,expression,formatString='#,0',description='',displayFolder='Performance'){
 measures.push({tableName:'Metrics',name,expression,formatString,description:description||name,displayFolder});
}
const snap=expr=>`VAR s = [As of Stage Number] RETURN CALCULATE(${expr}, REMOVEFILTERS('Stage'), 'Standing'[Stage] = s)`;
const tsnap=expr=>`VAR s = [As of Stage Number] RETURN CALCULATE(${expr}, REMOVEFILTERS('Stage'), 'Team Standing'[Stage] = s)`;
m('As of Stage Number',"MAX('As Of'[Stage])",'0','Latest selected stage; no selection means stage 21.','Context');
m('Snapshot Label','"STANDINGS AFTER STAGE " & FORMAT([As of Stage Number], "00")','',undefined,'Context');
m('Registered Riders',"COUNTROWS('Rider')",'0',undefined,'Participation');
m('Registered Teams',"COUNTROWS('Team')",'0',undefined,'Participation');
m('Stage Finishes',"COUNTROWS('Result')");
m('Adjusted Hours',"DIVIDE(SUM('Result'[Adjusted Seconds]),3600)",'#,0.00');
m('Adjusted Seconds',"SUM('Result'[Adjusted Seconds])");
m('Finish Seconds',"SUM('Result'[Finish Seconds])");
m('Bonus Seconds',"SUM('Result'[Bonus Seconds])");
m('Penalty Seconds',"SUM('Result'[Penalty Seconds])");
m('Stage Position',"IF(HASONEVALUE('Rider'[Bib]) && HASONEVALUE('Stage'[Stage]), MAX('Result'[Position]))",'0');
m('Stage Points',"SUM('Result'[Points])");
m('Stage KOM Points',"SUM('Result'[KOM Points])");
m('Average Stage Minutes',"DIVIDE(AVERAGE('Result'[Adjusted Seconds]),60)",'0.0');
m('Eligible Riders',snap("SUM('Standing'[Eligible])"),'0');
m('Exited Riders',"VAR s=[As of Stage Number] RETURN COALESCE(COUNTROWS(FILTER('Rider',NOT ISBLANK('Rider'[Exit Stage]) && 'Rider'[Exit Stage]<=s)),0)",'0','Explicit withdrawals by the selected stage; incomplete results alone are not an exit.');
m('Eligible Cumulative Hours',snap("DIVIDE(CALCULATE(SUM('Standing'[Cumulative Seconds]), 'Standing'[Eligible] = 1),3600)"),'#,0.00','Sum of eligible riders cumulative adjusted time in the selected rider/team slice.');
m('Rider Cumulative Seconds',"IF(HASONEVALUE('Rider'[Bib]), "+snap("CALCULATE(MAX('Standing'[Cumulative Seconds]), 'Standing'[Eligible]=1)")+")");
m('Rider Cumulative Time',`VAR t=[Rider Cumulative Seconds] RETURN IF(NOT ISBLANK(t), FORMAT(INT(t/3600),"0") & ":" & FORMAT(INT(MOD(t,3600)/60),"00") & ":" & FORMAT(MOD(t,60),"00"))`,'');
for(const n of ['GC Rank','Points Rank','KOM Rank','Young Rank'])m(n,"IF(HASONEVALUE('Rider'[Bib]), "+snap(`MAX('Standing'[${n}])`)+")",'0','Global competition rank. Preserved under rider/team filtering; blank when ineligible.','Classifications');
for(const [n,col] of [['Cumulative Points','Points'],['Cumulative KOM Points','KOM Points']])m(n,snap(`CALCULATE(SUM('Standing'[${col}]), 'Standing'[Eligible]=1)`),'#,0',undefined,'Classifications');
m('Rider Status',"IF(HASONEVALUE('Rider'[Bib]), "+snap("SELECTEDVALUE('Standing'[Status])")+")",'',undefined,'Context');
m('GC Gap Seconds',`VAR t=[Rider Cumulative Seconds] VAR s=[As of Stage Number] VAR leader=CALCULATE(MIN('Standing'[Cumulative Seconds]),REMOVEFILTERS('Rider'),REMOVEFILTERS('Stage'),'Standing'[Stage]=s,'Standing'[Eligible]=1) RETURN IF(NOT ISBLANK(t),t-leader)`,'#,0','Gap to global GC leader, seconds.','Classifications');
m('Classification Rank',`SWITCH(SELECTEDVALUE('Classification'[Classification]),"General",[GC Rank],"Points",[Points Rank],"Mountains",[KOM Rank],"Young Rider",[Young Rank])`,'0',undefined,'Classifications');
m('Classification Rider Hours',`VAR c=SELECTEDVALUE('Classification'[Classification]) RETURN IF(c="Young Rider",CALCULATE([Eligible Cumulative Hours],'Rider'[Young Rider]=1),[Eligible Cumulative Hours])`,'#,0.00','The same eligible field participates in General, Points and Mountains; time is not their points score.','Classifications');
m('Running Rider Hours',`VAR s=MAX('Stage'[Stage]) RETURN CALCULATE(DIVIDE(SUM('Result'[Adjusted Seconds]),3600),FILTER(ALL('Stage'),'Stage'[Stage]<=s))`,'#,0.00','All stage types through the x-axis stage; includes historical completed effort before exits.');
m('Best Team Rank',"IF(HASONEVALUE('Team'[Team]), "+tsnap("MAX('Team Standing'[Team Rank])")+")",'0','Rank by stages scored DESC, then cumulative stage top-3 time ASC.','Team');
m('Team Cumulative Hours',tsnap("DIVIDE(SUM('Team Standing'[Cumulative Top3 Seconds]),3600)"),'#,0.00',undefined,'Team');
m('Stages Scored',"IF(HASONEVALUE('Team'[Team]), "+tsnap("MAX('Team Standing'[Stages Scored])")+")",'0',undefined,'Team');
m('Team Coverage',"IF(HASONEVALUE('Team'[Team]), "+tsnap("SELECTEDVALUE('Team Standing'[Coverage])")+")",'',undefined,'Team');
m('Stage Top3 Hours',"DIVIDE(SUM('Team Stage'[Top3 Seconds]),3600)",'#,0.00',undefined,'Team');
m('Team Finishers',"IF(HASONEVALUE('Stage'[Stage]) && HASONEVALUE('Team'[Team]),MAX('Team Stage'[Finishers]))",'0',undefined,'Team');
m('Teams by Country',"COALESCE(CALCULATE(COUNTROWS('Team'),KEEPFILTERS(TREATAS(VALUES('Country'[Country]),'Team'[Team Country]))),0)",'0','Country dimension intentionally applies team nationality independently.','Participation');
m('Riders by Country',"COALESCE(CALCULATE(COUNTROWS('Rider'),KEEPFILTERS(TREATAS(VALUES('Country'[Country]),'Rider'[Rider Country]))),0)",'0','Registered rider nationality, independent of team nationality; includes exited riders.','Participation');
m('Roster Riders',"CALCULATE(COUNTROWS('Rider'),KEEPFILTERS(TREATAS(VALUES('Country'[Country]),'Rider'[Rider Country])))",'0','Intersection of selected country and roster hierarchy; blank hides unrelated roster branches.','Participation');
m('Foreign Team Riders',"COUNTROWS(FILTER('Rider','Rider'[Rider Country]<>'Rider'[Team Country]))",'0',undefined,'Participation');
m('Foreign Team Share',"DIVIDE([Foreign Team Riders],[Registered Riders])",'0.0%',undefined,'Participation');
m('Country Foreign Riders',"COALESCE(CALCULATE([Foreign Team Riders],KEEPFILTERS(TREATAS(VALUES('Country'[Country]),'Rider'[Rider Country]))),0)",'0',undefined,'Participation');
m('Countries Represented',"COUNTROWS(FILTER(ALL('Country'),[Teams by Country]+[Riders by Country]>0))",'0',undefined,'Participation');
measures.push(...JSON.parse(fs.readFileSync(path.join(root,'data/analytics_measures.json'),'utf8')));
if(process.argv.includes('--update-measures')){
 const existing=await op('measure_operations',{operation:'List'});
 const text=JSON.stringify(existing);
 const added=measures.filter(m=>!text.includes(m.name));
 if(added.length)await op('measure_operations',{operation:'Create',definitions:added});
 await op('measure_operations',{operation:'Update',definitions:measures});
}else await op('measure_operations',{operation:'Create',definitions:measures});
fs.writeFileSync(path.join(root,'data/measures.json'),JSON.stringify(measures,null,2));
await op('model_operations',{operation:'RefreshWithXMLA',refreshType:'Full'});
await op('database_operations',{operation:'ExportToTmdlFolder',tmdlFolderPath:path.join(root,'Tour de France.SemanticModel/definition')});
function normalizeTmdl(dir){for(const entry of fs.readdirSync(dir,{withFileTypes:true})){const f=path.join(dir,entry.name);if(entry.isDirectory())normalizeTmdl(f);else if(f.endsWith('.tmdl'))fs.writeFileSync(f,fs.readFileSync(f,'utf8').replaceAll('\r\n','\n').trimEnd()+'\n');}}
normalizeTmdl(path.join(root,'Tour de France.SemanticModel/definition'));
await client.close();
