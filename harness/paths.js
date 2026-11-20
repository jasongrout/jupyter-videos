'use strict';
// Where the harness reads and writes. RV_WORK holds the takes of a project and everything that its cut makes
// (default: work/<project>); RV_BASE holds the folders of the JupyterLab servers that all projects share (default:
// work/runtime). run_take.js sets RV_PROJECT from the path of the take script.
const fs = require('fs');
const path = require('path');

const REPO = path.resolve(__dirname, '..');
const PROJECT = process.env.RV_PROJECT || 'scratch';
const WORK = process.env.RV_WORK || path.join(REPO, 'work', PROJECT);
const BASE = process.env.RV_BASE || path.join(REPO, 'work', 'runtime');
const TAKES = process.env.RV_TAKES || path.join(WORK, 'takes');

/** PLAYWRIGHT_CORE, or the playwright-core that `npm install` put in this repository. */
function playwrightCore() {
  if (process.env.PLAYWRIGHT_CORE) return process.env.PLAYWRIGHT_CORE;
  const local = path.join(REPO, 'node_modules', 'playwright-core');
  return fs.existsSync(path.join(local, 'package.json')) ? local : null;
}

module.exports = { REPO, PROJECT, WORK, BASE, TAKES, PLAYWRIGHT_CORE: playwrightCore() };
