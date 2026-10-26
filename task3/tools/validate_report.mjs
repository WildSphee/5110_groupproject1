import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import Ajv from 'ajv';
import {execFileSync} from 'node:child_process';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
async function loadSchema(uri){
 const cache=path.join(root,'tools/schemas',encodeURIComponent(uri)+'.json');
 if(fs.existsSync(cache))return JSON.parse(fs.readFileSync(cache,'utf8'));
 let data;
 try{const r=await fetch(uri);if(!r.ok)throw Error(uri+' '+r.status);data=await r.json();}
 catch(e){
  if(process.platform!=='win32')throw e;
  data=JSON.parse(execFileSync('powershell.exe',['-NoProfile','-File',path.join(root,'tools/fetch_schema.ps1'),'-Uri',uri],{encoding:'utf8',maxBuffer:10e6}));
 }
 fs.mkdirSync(path.dirname(cache),{recursive:true});fs.writeFileSync(cache,JSON.stringify(data));return data;
}
const ajv=new Ajv({strict:false,allErrors:true,validateFormats:false,loadSchema});
const files=[];
function walk(dir){for(const d of fs.readdirSync(dir,{withFileTypes:true})){if(d.name==='.pbi')continue;const f=path.join(dir,d.name);if(d.isDirectory())walk(f);else if(f.endsWith('.json')||f.endsWith('.pbir'))files.push(f);}}
walk(path.join(root,'Tour de France.Report'));files.push(path.join(root,'Tour de France.pbip'),path.join(root,'Tour de France.SemanticModel/definition.pbism'));
const failures=[];
for(const f of files){const data=JSON.parse(fs.readFileSync(f));if(!data.$schema)continue;let validate=ajv.getSchema(data.$schema);if(!validate)validate=await ajv.compileAsync(await loadSchema(data.$schema));if(!validate(data))failures.push({file:path.relative(root,f),errors:validate.errors});}
const result={files:files.length,failures};
fs.writeFileSync(path.join(root,'review/schema-validation.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify(result));process.exitCode=failures.length?1:0;
