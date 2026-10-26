import {connect,call} from './mcp.mjs';
const {client}=await connect();
console.log(JSON.stringify(await call(client,'connection_operations',{operation:'ListLocalInstances'}),null,2));
await client.close();
