import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {connect,call} from './mcp.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const {client}=await connect();
await call(client,'connection_operations',{operation:'Connect',connectionString:process.argv[2]});
const results=[];
const dax=f=>{const v=f.Column||f.Measure;return `'${v.Expression.SourceRef.Entity.replaceAll("'","''")}'[${v.Property.replaceAll(']',']]')}]`;};
for(const page of fs.readdirSync(path.join(root,'Tour de France.Report/definition/pages'))){
 const dir=path.join(root,'Tour de France.Report/definition/pages',page,'visuals');if(!fs.existsSync(dir))continue;
 for(const name of fs.readdirSync(dir)){
  const v=JSON.parse(fs.readFileSync(path.join(dir,name,'visual.json'),'utf8')).visual;
  if(!v.query)continue;
  const fields=Object.values(v.query.queryState).flatMap(s=>s.projections.map(p=>p.field));
  const cols=[...new Set(fields.filter(f=>f.Column).map(dax))];
  const measures=[...new Set(fields.filter(f=>f.Measure).map(dax))];
  const expr=measures.map((m,i)=>`"value${i}",${m}`);
  const query='EVALUATE '+(cols.length?'SUMMARIZECOLUMNS('+[...cols,...expr].join(',')+')':'ROW('+expr.join(',')+')');
  try{
   const r=await call(client,'dax_query_operations',{operation:'Execute',query,resultMode:'Inline',maxRows:10000});
   const d=JSON.parse(r.content.find(x=>x.type==='text').text).data;
   results.push({page,name,passed:true,rows:d.rowCount,ms:d.executionTimeMs});
  }catch(e){results.push({page,name,passed:false,error:String(e)});}
 }
}
fs.writeFileSync(path.join(root,'review/visual-query-tests.json'),JSON.stringify({note:'Evaluates report field combinations at deepest configured drill level in the live engine; does not simulate UI clicks or rendering.',tests:results},null,2));
console.log(`${results.length} visual queries; ${results.filter(x=>!x.passed).length} failures`);
await client.close();process.exitCode=results.some(x=>!x.passed)?1:0;
