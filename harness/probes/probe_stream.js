'use strict';
// The race without the recorder: node probe_stream.js <port> -> the times of one run.
const { startTake } = require('../rv');
const scenario = require('../../projects/4.7-release/takes/stream.js');
(async () => {
  const port = Number(process.argv[2]);
  const take = await startTake({ name: 'probe-' + port, port, width: 960, height: 540, dsf: 1 });
  try {
    await scenario.setup(take);
    let result = null;
    take.rec = { now: () => 0, mark: (k, d) => { if (k === 'result') result = d; return 0; } };
    take.beat = () => 0;
    take.mark = (k, d) => take.rec.mark(k, d);
    await scenario.run(take);
    console.log(port, 'finished', (result.finished / 1000).toFixed(2), 's; all text', (result.all / 1000).toFixed(2), 'links', (result.links / 1000).toFixed(2));
  } finally {
    await take.browser.close();
  }
})();
