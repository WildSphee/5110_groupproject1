import {Client} from '@modelcontextprotocol/sdk/client/index.js';
import {StdioClientTransport} from '@modelcontextprotocol/sdk/client/stdio.js';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url));
export async function connect(){
 const client=new Client({name:'bt5110-task3',version:'1.0.0'},{capabilities:{}});
 const transport=new StdioClientTransport({command:process.execPath,args:[path.join(dir,'node_modules/@microsoft/powerbi-modeling-mcp/index.js'),'--start','--accepteula'],stderr:'pipe'});
 fs.mkdirSync(path.join(dir,'runtime'),{recursive:true});
 transport.stderr?.on('data',d=>fs.appendFileSync(path.join(dir,'runtime/server.log'),d));
 await client.connect(transport);
 return {client,transport};
}
export async function call(client,name,request){
 const r=await client.callTool({name,arguments:{request}},undefined,{timeout:240000});
 if(r.isError)throw new Error(JSON.stringify(r));
 return r;
}
if(process.argv[2]==='serve'){
 const {client}=await connect();
 fs.writeFileSync(path.join(dir,'runtime/schemas.json'),JSON.stringify(await client.listTools(),null,2));
 console.log('Power BI MCP ready');
 for(;;){
  const file=path.join(dir,'runtime/request.json');
  if(fs.existsSync(file)){
   const r=JSON.parse(fs.readFileSync(file,'utf8'));fs.unlinkSync(file);
   try{fs.writeFileSync(path.join(dir,'runtime',r.id+'.json'),JSON.stringify(await call(client,r.name,r.request),null,2));}
   catch(e){fs.writeFileSync(path.join(dir,'runtime',r.id+'.json'),JSON.stringify({error:String(e)}));}
  }
  await new Promise(r=>setTimeout(r,150));
 }
}
