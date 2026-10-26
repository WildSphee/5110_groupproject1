import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const dir=path.join(path.dirname(fileURLToPath(import.meta.url)),'runtime');
const [id,name,input]=process.argv.slice(2);
const request=JSON.parse(fs.readFileSync(input,'utf8'));
const result=path.join(dir,id+'.json');
if(fs.existsSync(result))fs.unlinkSync(result);
fs.writeFileSync(path.join(dir,'request.json'),JSON.stringify({id,name,request}));
for(let i=0;i<480;i++){
 if(fs.existsSync(result)){console.log(fs.readFileSync(result,'utf8'));process.exit(0);}
 await new Promise(r=>setTimeout(r,500));
}
throw new Error('MCP request timeout');
