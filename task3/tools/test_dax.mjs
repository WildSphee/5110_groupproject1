import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {connect,call} from './mcp.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const tests=JSON.parse(fs.readFileSync(path.join(root,'tests/dax_expected.json'),'utf8'));
const {client}=await connect();
await call(client,'connection_operations',{operation:'Connect',connectionString:process.argv[2]});
const results=[];
function normalized(rows){return rows.map(r=>Object.fromEntries(Object.entries(r).map(([k,v])=>[k.replace(/^\[|\]$/g,''),typeof v==='number'?Math.round(v*1e6)/1e6:v]))).map(r=>JSON.stringify(Object.fromEntries(Object.entries(r).sort()))).sort();}
for(const t of tests){
 try{
  const r=await call(client,'dax_query_operations',{operation:'Execute',query:t.query,resultMode:'Inline',maxRows:10000});
  const parsed=JSON.parse(r.content.find(c=>c.type==='text').text);const data=parsed.data;
  const actual=data.rows.map(r=>Object.fromEntries(Object.keys(t.expected[0]||{}).map(k=>[k,r['['+k+']']??null])));
  const passed=JSON.stringify(normalized(actual))===JSON.stringify(normalized(t.expected));
  results.push({name:t.name,passed,rows:data.rowCount,ms:data.executionTimeMs,...(!passed?{actual,expected:t.expected}:{})});
  console.log(passed?'PASS':'FAIL',t.name,data.rowCount+' rows',data.executionTimeMs+'ms');
 }catch(e){results.push({name:t.name,passed:false,error:String(e)});console.log('ERROR',t.name,String(e).slice(0,300));}
}
fs.writeFileSync(path.join(root,'review/dax-tests.json'),JSON.stringify({connection:process.argv[2],tests:results},null,2));
await client.close();process.exitCode=results.some(r=>!r.passed)?1:0;
