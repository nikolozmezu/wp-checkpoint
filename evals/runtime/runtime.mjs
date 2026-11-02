import fs from 'node:fs/promises';
import path from 'node:path';
import http from 'node:http';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { loadNodeRuntime } from '@php-wasm/node';
import { bootWordPressAndRequestHandler } from '@wp-playground/wordpress';
const here = path.dirname(fileURLToPath(import.meta.url));

export async function startFixture() {
  const config = JSON.parse(await fs.readFile(path.join(here, 'versions.json'), 'utf8'));
  const zip = await fs.readFile(path.join(here, '.cache', 'wordpress-' + config.wordpress + '.zip'));
  const digest = createHash('sha256').update(zip).digest('hex');
  if (!config.wordpress_sha256 || config.wordpress_sha256 !== digest) throw new Error('Verified WordPress archive missing/mismatched. Run npm run setup.');
  const sqlite = await fs.readFile(path.join(here, 'node_modules/@wp-playground/cli/sqlite-database-integration.zip'));
  let handler;
  const server = http.createServer(async (request, response) => {
    if (!handler) { response.writeHead(503); response.end('Fixture booting'); return; }
    try {
      const chunks = []; let length = 0;
      for await (const chunk of request) {
        length += chunk.length;
        if (length > 1024 * 1024) { response.writeHead(413); response.end(); return; }
        chunks.push(chunk);
      }
      const result = await handler.request({
        url: request.url, method: request.method, headers: request.headers,
        body: chunks.length ? Buffer.concat(chunks) : undefined
      });
      response.writeHead(result.httpStatusCode, result.headers);
      response.end(Buffer.from(result.bytes));
    } catch (error) { response.writeHead(500); response.end('Fixture transport failed'); console.error(error); }
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
  const url = 'http://127.0.0.1:' + server.address().port;
  try {
    handler = await bootWordPressAndRequestHandler({
      createPhpRuntime: () => loadNodeRuntime(config.php, { emscriptenOptions: { processId: 1 } }),
      phpVersion: config.php, maxPhpInstances: 1, cookieStore: false, siteUrl: url,
      wordPressZip: new File([zip], 'wordpress.zip'),
      sqliteIntegrationPluginZip: new File([sqlite], 'sqlite.zip'),
      constants: {
        WP_CHECKPOINT_FIXTURE: true, WP_ENVIRONMENT_TYPE: 'local', WP_HTTP_BLOCK_EXTERNAL: true,
        DISABLE_WP_CRON: true, AUTOMATIC_UPDATER_DISABLED: true, WP_AUTO_UPDATE_CORE: false,
        WP_DEBUG: true, WP_DEBUG_DISPLAY: false, WP_DEBUG_LOG: true
      }
    });
    const php = await handler.getPrimaryPhp();
    php.mkdirTree('/wordpress/wp-content/mu-plugins');
    php.writeFile('/wordpress/wp-content/mu-plugins/checkpoint-fixture.php', await fs.readFile(path.join(here, 'fixture.php'), 'utf8'));
    async function variant(name) {
      if (!['healthy', 'broken'].includes(name)) throw new Error('Unknown fixture variant');
      const result = await php.run({ code: '<?php require "/wordpress/wp-load.php"; update_option("checkpoint_fixture_variant", "' + name + '"); delete_option("checkpoint_fixture_message");' });
      if (result.exitCode) throw new Error('Cannot set fixture variant: ' + result.errors);
    }
    await variant('healthy');
    return {
      url, config, variant,
      async log() { try { return php.readFileAsText('/wordpress/wp-content/debug.log'); } catch { return ''; } },
      async close() {
        await new Promise(resolve => server.close(resolve));
        await handler[Symbol.asyncDispose]();
      }
    };
  } catch (error) {
    await new Promise(resolve => server.close(resolve));
    if (handler) await handler[Symbol.asyncDispose]();
    throw error;
  }
}
