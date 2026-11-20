'use strict';
// Record one take: node run_take.js <scenario module> [port]
// The module exports { name, port?, width?, height?, dsf?, setup(take), run(take) }.
const path = require('path');
const { startTake } = require('./rv');

(async () => {
  const file = path.resolve(process.argv[2]);
  const scenario = require(file);
  const port = Number(process.argv[3] || scenario.port || 8963);
  const opts = { name: scenario.name, port, seed: scenario.seed };
  for (const key of ['width', 'height', 'dsf']) if (scenario[key]) opts[key] = scenario[key];
  const take = await startTake(opts);
  const started = Date.now();
  try {
    await scenario.setup(take);
    await take.record();
    await scenario.run(take);
    await take.stop();
    console.log(`done in ${((Date.now() - started) / 1000).toFixed(1)} s`);
  } catch (e) {
    console.log('TAKE FAILED', e.stack || e);
    try {
      await take.page.screenshot({ path: path.join(take.dir, 'failure.png') });
    } catch {}
    await take.abort();
    process.exitCode = 1;
  }
})();
