import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
const here = path.dirname(fileURLToPath(import.meta.url));
const cache = path.join(here, '.cache');
await fs.mkdir(cache, { recursive: true });
const config = JSON.parse(await fs.readFile(path.join(here, 'versions.json'), 'utf8'));
const archive = path.join(cache, 'wordpress-' + config.wordpress + '.zip');
let bytes;
let downloadedAt=null;
try { bytes = await fs.readFile(archive); } catch (error) {
  if (error.code !== 'ENOENT') throw error;
  const response = await fetch(config.wordpress_url);
  if (!response.ok) throw new Error('WordPress download failed: HTTP ' + response.status);
  bytes = Buffer.from(await response.arrayBuffer());
  downloadedAt=new Date().toISOString();
  await fs.writeFile(archive + '.part', bytes, { flag: 'wx' });
  await fs.rename(archive + '.part', archive);
}
const sha256 = createHash('sha256').update(bytes).digest('hex');
if (!/^[a-f0-9]{64}$/.test(config.wordpress_sha256 || '') || config.wordpress_sha256 !== sha256) {
  throw new Error('WordPress archive hash differs; preserve it for inspection and use a verified download.');
}
try {
  const old=JSON.parse(await fs.readFile(path.join(cache,'download-receipt.json'),'utf8'));
  if(!downloadedAt&&old.sha256===sha256&&old.url===config.wordpress_url)downloadedAt=old.downloaded_at||null;
} catch(error) { if(error.code!=='ENOENT'&&!(error instanceof SyntaxError))throw error; }
await fs.writeFile(path.join(cache, 'download-receipt.json'), JSON.stringify({
  url: config.wordpress_url, sha256, bytes: bytes.length, downloaded_at:downloadedAt, verified_at:new Date().toISOString()
}, null, 2));
console.log('WordPress archive ready: ' + sha256);
const installed = spawnSync(process.execPath, [path.join(here, 'node_modules/playwright/cli.js'), 'install', 'chromium'], {
  cwd: here, stdio: 'inherit', windowsHide: true,
  env: { ...process.env, PLAYWRIGHT_BROWSERS_PATH: path.join(cache, 'browsers') }
});
if (installed.error) throw installed.error;
process.exitCode = installed.status ?? 1;
