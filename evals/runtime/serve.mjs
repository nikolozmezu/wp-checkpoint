import { startFixture } from './runtime.mjs';
import readline from 'node:readline';
const variant=process.argv[2]||'healthy';
if(!['healthy','broken'].includes(variant))throw new Error('Usage: npm run serve -- healthy|broken');
const fixture=await startFixture();
await fixture.variant(variant);
console.log('Disposable WordPress fixture: '+fixture.url+'/checkpoint-fixture/');
console.log('In-memory data only; Ctrl+C stops this isolated server.');
console.log('Controller commands: healthy or broken, followed by Enter. Keep this console hidden from a blind evaluator.');
const input=readline.createInterface({input:process.stdin});
let queue=Promise.resolve();
input.on('line',line=>{const value=line.trim();if(!['healthy','broken'].includes(value)){console.log('Use healthy or broken.');return;}queue=queue.then(()=>fixture.variant(value)).then(()=>console.log('Controller state changed.')).catch(error=>console.error(error));});
let closing=false;
async function stop(){if(closing)return;closing=true;input.close();await queue;await fixture.close();}
process.on('SIGINT',()=>stop().then(()=>process.exit(0)));
process.on('SIGTERM',()=>stop().then(()=>process.exit(0)));
