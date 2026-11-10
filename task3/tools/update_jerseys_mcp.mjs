import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {connect,call} from './mcp.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const folder=path.join(root,'Tour de France.SemanticModel/definition');
const rows=JSON.parse(fs.readFileSync(path.join(root,'data/jersey_leaders.json'),'utf8'));
if(rows.length!==42 || new Set(rows.map(r=>`${r.Stage}/${r.Classification}`)).size!==42)throw Error('Expected both classifications for all 21 stages');
const {client}=await connect();
const log=[];
async function op(name,request){
 const result=await call(client,name,request);
 const parsed=result.structuredContent ?? (result.content?.find(c=>c.type==='text') ? JSON.parse(result.content.find(c=>c.type==='text').text) : result);
 log.push({name,request,result:parsed});
 fs.writeFileSync(path.join(root,'review/jersey-mcp-update.json'),JSON.stringify(log,null,2));
 console.log(name,request.operation,JSON.stringify(parsed).slice(0,800));
 if(parsed.success===false || parsed.error || parsed.data?.results?.some(r=>r.success===false))throw Error(JSON.stringify(parsed));
 return parsed;
}
try {
 await op('database_operations',{operation:'ImportFromTmdlFolder',tmdlFolderPath:folder,connectionName:'jersey-update'});
 const columns=Object.keys(rows[0]).map(name=>({name,sourceColumn:name,dataType:['Stage','Points'].includes(name)?'Int64':'String',summarizeBy:'None'}));
 const literal=v=>typeof v==='string'?'"'+v.replaceAll('"','""')+'"':String(v);
 const mExpression='let Source = #table(type table ['+columns.map(c=>'#"'+c.name+'" = '+(c.dataType==='Int64'?'Int64.Type':'nullable text')).join(', ')+'], {\n'+rows.map(r=>'{'+columns.map(c=>literal(r[c.name])).join(',')+'}').join(',\n')+'\n}) in Source';
 await op('table_operations',{operation:'Create',definitions:[{name:'Jersey Leaders',description:'Published first-place Points and Mountains snapshots for Tour de France 2025 stages 1–21. Static, offline data; Source stores the stage citation. Official tie-break ordering is preserved.',isHidden:true,mExpression,columns}]});
 const definitions=JSON.parse(fs.readFileSync(path.join(root,'data/measures.json'),'utf8')).filter(m=>['Award leaders','Winning score','Winning rule'].includes(m.name));
 await op('measure_operations',{operation:'Update',definitions});
 const output=path.join(root,'tools/runtime/jersey-export');
 await op('database_operations',{operation:'ExportToTmdlFolder',tmdlFolderPath:output});
 const backup=path.join(root,'tools/runtime/before-jerseys');fs.mkdirSync(backup,{recursive:true});
 for(const relative of ['model.tmdl','tables/Metrics.tmdl','tables/Jersey Leaders.tmdl']){
   const source=path.join(output,relative),target=path.join(folder,relative);
   if(fs.existsSync(target))fs.copyFileSync(target,path.join(backup,path.basename(relative)));
   fs.copyFileSync(source,target);
 }
 console.log('Updated PBIP semantic model through Microsoft Power BI Modeling MCP.');
}finally{await client.close();}

