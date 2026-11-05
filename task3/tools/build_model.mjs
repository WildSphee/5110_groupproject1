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
  const dataType=sample===undefined?'Int64':typeof sample==='number'?(Number.isInteger(sample)&&n!=='Distance km'?'Int64':'Double'):'String';
  return {name:n,sourceColumn:n,dataType,...(name==='Stage choice'&&n==='Choice'?{sortByColumn:'Order'}:{}),...(name==='Country'&&n==='Country'?{dataCategory:'Country'}:{}),summarizeBy:'None',isHidden:['Bib','Stage'].includes(n)&&!['Rider','Stage','As Of'].includes(name)};
 });
 const val=v=>v===null?'null':typeof v==='string'?'"'+v.replaceAll('"','""')+'"':String(v);
 const mExpression='let Source = #table(type table ['+cols.map(c=>'#"'+c.name+'" = '+(c.dataType==='String'?'nullable text':c.dataType==='Int64'?'Int64.Type':'number')).join(', ')+'], {\n'+rows.map(r=>'{'+cols.map(c=>val(r[c.name])).join(',')+'}').join(',\n')+'\n}) in Source';
 return {name,description:'2025 Tour de France database export. See task3/docs/semantics.md for grain and rules.',mExpression,columns:cols};
});
if(!process.argv.includes('--update-measures'))await op('table_operations',{operation:'Create',definitions:process.argv.includes('--resume')?definitions.filter(d=>d.name==='Metrics'):definitions});
const rels=[['Stage choice','Stage','Stage','Stage']];
for(const fact of ['Result','Standing','Withdrawal'])for(const [dim,col] of [['Rider','Bib'],['Stage','Stage']])rels.push([fact,col,dim,col]);
for(const fact of ['Team Stage','Team Standing'])for(const [dim,col] of [['Team','Team'],['Stage','Stage']])rels.push([fact,col,dim,col]);
if(!process.argv.includes('--resume')&&!process.argv.includes('--update-measures'))await op('relationship_operations',{operation:'Create',definitions:rels.map(([fromTable,fromColumn,toTable,toColumn])=>({
 name:fromTable+'_'+toTable,fromTable,fromColumn,toTable,toColumn,fromCardinality:'Many',toCardinality:'One',crossFilteringBehavior:fromTable==='Stage choice'?'BothDirections':'OneDirection',isActive:true}))});
const measures=JSON.parse(fs.readFileSync(path.join(root,'data/measures.json'),'utf8'));
if(process.argv.includes('--update-measures')){
 const existing=await op('measure_operations',{operation:'List'});
 const text=JSON.stringify(existing);
 const added=measures.filter(m=>!text.includes(m.name));
 if(added.length)await op('measure_operations',{operation:'Create',definitions:added});
 await op('measure_operations',{operation:'Update',definitions:measures});
}else await op('measure_operations',{operation:'Create',definitions:measures});
await op('model_operations',{operation:'RefreshWithXMLA',refreshType:'Full'});
await op('database_operations',{operation:'ExportToTmdlFolder',tmdlFolderPath:path.join(root,'Tour de France.SemanticModel/definition')});
function normalizeTmdl(dir){for(const entry of fs.readdirSync(dir,{withFileTypes:true})){const f=path.join(dir,entry.name);if(entry.isDirectory())normalizeTmdl(f);else if(f.endsWith('.tmdl'))fs.writeFileSync(f,fs.readFileSync(f,'utf8').replaceAll('\r\n','\n').trimEnd()+'\n');}}
normalizeTmdl(path.join(root,'Tour de France.SemanticModel/definition'));
await client.close();
