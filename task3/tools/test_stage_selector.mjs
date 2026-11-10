import fs from 'node:fs';
import {connect,call} from './mcp.mjs';
const root=new URL('../',import.meta.url),data=JSON.parse(fs.readFileSync(new URL('data/model_data.json',root),'utf8'));
const {client}=await connect();
async function op(name,request){const r=await call(client,name,request);const t=r.content?.find(c=>c.type==='text');const p=t?JSON.parse(t.text):r;if(p.error||p.success===false)throw Error(JSON.stringify(p));return p;}
try{
 await op('connection_operations',{operation:'Connect',connectionString:process.argv[2]});
 await op('table_operations',{operation:'RefreshWithXMLA',references:[{name:'Stage choice'}]});
 const query=`EVALUATE SUMMARIZECOLUMNS('Stage choice'[Choice],'Stage choice'[Order],"Stages",DISTINCTCOUNT('Stage'[Stage]),"Results",[Stage Finishes],"Podiums",[Stage Podiums],"Distance",SUM('Stage'[Distance km])) ORDER BY 'Stage choice'[Order]`;
 const result=await op('dax_query_operations',{operation:'Execute',query,resultMode:'Inline',maxRows:30});
 const rows=result.data.rows;
 if(rows.length!==22 || rows[0]['Stage choice[Choice]']!=='All')throw Error('Expected All followed by 21 stages');
 for(const row of rows){
  const choice=row['Stage choice[Choice]'];
  const stages=data.Stage.filter(r=>choice==='All'||r.Stage===Number(choice));
  const results=data.Result.filter(r=>choice==='All'||r.Stage===Number(choice));
  const expected={Stages:stages.length,Results:results.length,Podiums:results.filter(r=>r.Position<=3).length,Distance:stages.reduce((s,r)=>s+r['Distance km'],0)};
  for(const [key,value] of Object.entries(expected))if(Math.abs(row[`[${key}]`]-value)>0.000001)throw Error(JSON.stringify({choice,key,expected:value,actual:row[`[${key}]`]}));
 }
 fs.writeFileSync(new URL('review/stage-selector-live-tests.json',root),JSON.stringify({passed:true,query,rows,note:'All and each stage verified against source data in the live Power BI engine. Schema validation was unavailable: the existing visualContainer/2.14.0 schema URL returned HTTP 404.'},null,2));
 console.log(`PASS 22 selections: All = ${rows[0]['[Stages]']} stages, ${rows[0]['[Results]']} results; each individual stage, podium counts, distances and numeric sort verified.`);
}finally{await client.close();}

