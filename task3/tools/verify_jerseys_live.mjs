import fs from 'node:fs';
import {connect,call} from './mcp.mjs';
const root=new URL('../',import.meta.url);
const snapshots=JSON.parse(fs.readFileSync(new URL('data/jersey_leaders.json',root),'utf8'));
const definitions=JSON.parse(fs.readFileSync(new URL('data/measures.json',root),'utf8')).filter(m=>['Award leaders','Winning score','Winning rule'].includes(m.name));
const {client}=await connect();
const results=[];
async function op(name,request){const r=await call(client,name,request);const t=r.content?.find(c=>c.type==='text');const p=t?JSON.parse(t.text):r;if(p.error||p.success===false)throw Error(JSON.stringify(p));return p;}
const query=`EVALUATE SUMMARIZECOLUMNS('As Of'[Stage],'Classification'[Classification],"Leader",[Award leaders],"Score",[Winning score],"Rule",[Winning rule])`;
try{
for(const port of process.argv.slice(2)){
 await op('connection_operations',{operation:'Connect',connectionString:`Data Source=localhost:${port}`});
 const before=(await op('dax_query_operations',{operation:'Execute',query,resultMode:'Inline',maxRows:100})).data.rows;
 const tables=JSON.stringify(await op('table_operations',{operation:'List'}));
 if(!tables.includes('Jersey Leaders')){
  const columns=Object.keys(snapshots[0]).map(name=>({name,sourceColumn:name,dataType:['Stage','Points'].includes(name)?'Int64':'String',summarizeBy:'None'}));
  const text=fs.readFileSync(new URL('Tour de France.SemanticModel/definition/tables/Jersey Leaders.tmdl',root),'utf8');
  const mExpression=text.replaceAll('\r\n','\n').split('\t\tsource =\n')[1].split('\n').map(l=>l.replace(/^\t{4}/,'')).join('\n').trim();
  await op('table_operations',{operation:'Create',definitions:[{name:'Jersey Leaders',isHidden:true,mExpression,columns}]});
 }
 await op('measure_operations',{operation:'Update',definitions});
 await op('table_operations',{operation:'RefreshWithXMLA',references:[{name:'Jersey Leaders'}]});
 const rows=(await op('dax_query_operations',{operation:'Execute',query,resultMode:'Inline',maxRows:100})).data.rows;
 if(rows.length!==84)throw Error(`Expected 84 stage/classification combinations, received ${rows.length}`);
 for(const expected of snapshots){
  const actual=rows.find(r=>r['As Of[Stage]']===expected.Stage && r['Classification[Classification]']===expected.Classification);
  if(actual?.['[Leader]']!==expected.Leader || actual?.['[Score]']!==`${expected.Points} pts`)throw Error(JSON.stringify({expected,actual,keys:Object.keys(rows[0])}));
 }
 const timeRows=rows.filter(r=>['General','Young Rider'].includes(r['Classification[Classification]']));
 if(JSON.stringify(timeRows)!==JSON.stringify(before.filter(r=>['General','Young Rider'].includes(r['Classification[Classification]']))))throw Error('Time classifications changed');
 for(const stages of [[],[6],[6,7]]){
   const expectedStage=stages.length?Math.max(...stages):21;
   const q=`EVALUATE CALCULATETABLE(SUMMARIZECOLUMNS('Classification'[Classification],"Leader",[Award leaders],"Score",[Winning score])${stages.length?`,TREATAS({${stages.join(',')}},'As Of'[Stage])`:''})`;
   const data=(await op('dax_query_operations',{operation:'Execute',query:q,resultMode:'Inline'})).data.rows;
   for(const e of snapshots.filter(r=>r.Stage===expectedStage)){
    const a=data.find(r=>r['Classification[Classification]']===e.Classification);
    if(a['[Leader]']!==e.Leader||a['[Score]']!==`${e.Points} pts`)throw Error('Selector behavior mismatch');
   }
 }
 results.push({port,passed:true,snapshotsVerified:42,timeClassificationsUnchanged:42,selectorCases:['cleared → stage 21','stage 6','stages 6+7 → stage 7'],rows});
 console.log(`PASS port ${port}: 42 jersey snapshots, 42 unchanged time rows, cleared/single/multiple stage selections`);
}
fs.writeFileSync(new URL('review/jersey-live-tests.json',root),JSON.stringify(results,null,2));
}finally{await client.close();}
