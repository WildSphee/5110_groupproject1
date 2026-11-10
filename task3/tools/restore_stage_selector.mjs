import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {connect,call} from './mcp.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const folder=path.join(root,'Tour de France.SemanticModel/definition');
const rows=JSON.parse(fs.readFileSync(path.join(root,'data/model_data.json'),'utf8'))['Stage choice'];
const {client}=await connect();
async function op(name,request){const r=await call(client,name,request);const t=r.content?.find(c=>c.type==='text');const p=t?JSON.parse(t.text):r;if(p.error||p.success===false)throw Error(JSON.stringify(p));return p;}
try{
 await op('database_operations',{operation:'ImportFromTmdlFolder',tmdlFolderPath:folder});
 const tables=JSON.stringify(await op('table_operations',{operation:'List'}));
 if(!tables.includes('Stage choice')){
  const mExpression='let Source = #table(type table [Choice = nullable text, Stage = Int64.Type, Order = Int64.Type], {\n'+rows.map(r=>`{"${r.Choice}",${r.Stage},${r.Order}}`).join(',\n')+'\n}) in Source';
  await op('table_operations',{operation:'Create',definitions:[{name:'Stage choice',description:'Stage selector bridge: All maps to every stage, individual labels map to one stage.',mExpression,columns:[{name:'Choice',sourceColumn:'Choice',dataType:'String',sortByColumn:'Order',summarizeBy:'None'},{name:'Stage',sourceColumn:'Stage',dataType:'Int64',isHidden:true,summarizeBy:'None'},{name:'Order',sourceColumn:'Order',dataType:'Int64',isHidden:true,summarizeBy:'None'}]}]});
 }
 const relationships=JSON.stringify(await op('relationship_operations',{operation:'List'}));
 if(!relationships.includes('StageChoice_Stage'))await op('relationship_operations',{operation:'Create',definitions:[{name:'StageChoice_Stage',fromTable:'Stage choice',fromColumn:'Stage',toTable:'Stage',toColumn:'Stage',fromCardinality:'Many',toCardinality:'One',crossFilteringBehavior:'BothDirections',isActive:true}]});
 const output=path.join(root,'tools/runtime/stage-selector-export');
 await op('database_operations',{operation:'ExportToTmdlFolder',tmdlFolderPath:output});
 for(const relative of ['model.tmdl','relationships.tmdl','tables/Stage choice.tmdl'])fs.copyFileSync(path.join(output,relative),path.join(folder,relative));
 console.log('Restored Stage choice table and relationship through Microsoft Power BI Modeling MCP.');
}finally{await client.close();}
