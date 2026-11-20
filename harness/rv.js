'use strict';
// Recording helpers for the JupyterLab 4.7 release video.
//
// A take is one feature, played on a live JupyterLab by Playwright and recorded
// with the screen recorder of recorder/ (CDP screencast, one frame per
// 1/30 s of wall time). The pointer, the click ripples and the key labels are
// not drawn in the page: every mouse and key event is logged with its time on
// the take's timeline, and the cut draws them at 60 fps over the frames.
//
//   const take = await startTake({ name: 'palette', port: 8963 });
//   await take.lab.open();            // before the recording starts
//   await take.record();              // the recording starts here
//   await H.click(take.page, ...);    // human.js moves are logged
//   await take.focus('palette', '.jp-ModalCommandPalette', { zoom: 1.6 });
//   await take.beat('done');
//   await take.stop();

const fs = require('fs');
const path = require('path');

const { TAKES } = require('./paths');
const { launch, startRecording } = require('./recorder/recorder');
const H = require('./recorder/human');
const { regionOf } = require('./recorder/regions');

const HIDE_DEV_BORDER = '.jp-LabShell.jp-mod-devMode { border-top: 0 !important; }';

function round1(v) {
  return Math.round(v * 10) / 10;
}

/** The union of boxes, ignoring missing ones. */
function union(boxes) {
  const xs = boxes.filter(Boolean);
  if (!xs.length) return null;
  const x = Math.min(...xs.map(b => b.x));
  const y = Math.min(...xs.map(b => b.y));
  const r = Math.max(...xs.map(b => b.x + b.width));
  const b = Math.max(...xs.map(b => b.y + b.height));
  return { x: round1(x), y: round1(y), width: round1(r - x), height: round1(b - y) };
}

/**
 * Wrap the page's mouse and keyboard so that every call is logged with its time
 * on the recording's timeline, before the call is sent. Until the recording
 * starts, events are logged with t = null and left out of the file.
 */
function instrument(page, take) {
  const log = take.input;
  const now = () => (take.rec ? take.rec.now() : null);
  const mouse = page.mouse;
  const keyboard = page.keyboard;
  const orig = {
    move: mouse.move.bind(mouse),
    down: mouse.down.bind(mouse),
    up: mouse.up.bind(mouse),
    wheel: mouse.wheel.bind(mouse),
    press: keyboard.press.bind(keyboard),
    kdown: keyboard.down.bind(keyboard),
    kup: keyboard.up.bind(keyboard),
    type: keyboard.type.bind(keyboard),
    insertText: keyboard.insertText.bind(keyboard)
  };
  let last = { x: 0, y: 0 };
  mouse.move = async (x, y, options) => {
    log.push({ t: now(), k: 'move', x: round1(x), y: round1(y) });
    last = { x, y };
    return orig.move(x, y, options);
  };
  mouse.down = async (options = {}) => {
    log.push({ t: now(), k: 'down', x: round1(last.x), y: round1(last.y), button: options.button || 'left', count: options.clickCount || 1 });
    return orig.down(options);
  };
  mouse.up = async (options = {}) => {
    log.push({ t: now(), k: 'up', x: round1(last.x), y: round1(last.y), button: options.button || 'left' });
    return orig.up(options);
  };
  mouse.wheel = async (dx, dy) => {
    log.push({ t: now(), k: 'wheel', dx, dy });
    return orig.wheel(dx, dy);
  };
  keyboard.press = async (key, options) => {
    log.push({ t: now(), k: 'press', key });
    return orig.press(key, options);
  };
  keyboard.down = async key => {
    log.push({ t: now(), k: 'kdown', key });
    return orig.kdown(key);
  };
  keyboard.up = async key => {
    log.push({ t: now(), k: 'kup', key });
    return orig.kup(key);
  };
  keyboard.type = async (text, options) => {
    log.push({ t: now(), k: 'type', text });
    return orig.type(text, options);
  };
  keyboard.insertText = async text => {
    log.push({ t: now(), k: 'type', text });
    return orig.insertText(text);
  };
}

/**
 * The box of what an element shows: its lines of text and its media (images,
 * formulas, form controls), clipped to the viewport, without the cell toolbar,
 * which sits at the far right of a cell and would stretch the box to its width.
 */
async function contentBox(locator) {
  const handle = await locator.elementHandle({ timeout: 2000 }).catch(() => null);
  if (!handle) return null;
  return handle.evaluate(el => {
    const skip = '.jp-cell-toolbar, .jp-Collapser, .jp-InputArea-prompt, .jp-OutputArea-prompt';
    const boxes = [];
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    const range = document.createRange();
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      if (!n.textContent.trim()) continue;
      const p = n.parentElement;
      if (!p || p.closest(skip)) continue;
      const cs = getComputedStyle(p);
      if (cs.visibility === 'hidden') continue;
      range.selectNodeContents(n);
      for (const r of range.getClientRects()) if (r.width > 0.5 && r.height > 0.5) boxes.push(r);
    }
    for (const m of el.querySelectorAll('img, canvas, mjx-math, input, select, textarea, .jp-RenderedMermaid svg, .lm-DataGrid')) {
      if (m.closest(skip)) continue;
      // A display formula's container spans the line; its mjx-math is the formula.
      const r = m.getBoundingClientRect();
      if (r.width > 1 && r.height > 1) boxes.push(r);
    }
    if (!boxes.length) {
      const r = el.getBoundingClientRect();
      boxes.push(r);
    }
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const r of boxes) {
      x0 = Math.min(x0, r.left);
      y0 = Math.min(y0, r.top);
      x1 = Math.max(x1, r.right);
      y1 = Math.max(y1, r.bottom);
    }
    // Clip to the element itself (its scrolled-away content is not shown) and to the viewport.
    const own = el.getBoundingClientRect();
    x0 = Math.max(0, own.left, x0);
    y0 = Math.max(0, own.top, y0);
    x1 = Math.min(innerWidth, own.right, x1);
    y1 = Math.min(innerHeight, own.bottom, y1);
    if (x1 <= x0 || y1 <= y0) return null;
    return { x: x0, y: y0, width: x1 - x0, height: y1 - y0 };
  });
}

/**
 * A box in CSS px for a locator, a selector, a box, or a list of them. With
 * content (the default for elements), the box of what the element shows.
 */
async function boxOf(page, target, content = true) {
  if (!target) return null;
  if (Array.isArray(target)) {
    const boxes = [];
    for (const t of target) boxes.push(await boxOf(page, t, content));
    return union(boxes);
  }
  if (typeof target === 'string') return boxOf(page, page.locator(target).first(), content);
  if (typeof target.boundingBox === 'function') {
    const b = content ? await contentBox(target).catch(() => null) : await target.boundingBox({ timeout: 2000 }).catch(() => null);
    return b ? union([b]) : null;
  }
  if ('x' in target && 'width' in target) return union([target]);
  return null;
}

/** JupyterLab helpers for the page of a take. */
function labHelpers(take) {
  const page = take.page;
  const base = `http://localhost:${take.port}`;
  const lab = {
    base,
    async open({ workspace, path: p = '', query = 'reset', keepLauncher = false, theme = 'JupyterLab Light' } = {}) {
      const ws = workspace || `rv-${take.name}`;
      const url = `${base}/lab/workspaces/${ws}${p ? '/tree/' + p : ''}?${query}`;
      await page.goto(url);
      await page.waitForFunction(() => window.jupyterapp && window.jupyterapp.restored);
      await page.evaluate(() => window.jupyterapp.restored);
      await page.addStyleTag({ content: HIDE_DEV_BORDER });
      await page.waitForSelector('#jupyterlab-splash', { state: 'detached' });
      const themeNow = await page.evaluate(() => document.body.dataset.jpThemeName);
      if (theme && themeNow !== theme) {
        await page.evaluate(t => window.jupyterapp.commands.execute('apputils:change-theme', { theme: t }), theme);
        await page.waitForFunction(t => document.body.dataset.jpThemeName === t, theme, { timeout: 15000 });
        await page.waitForTimeout(800);
      }
      await page.evaluate(async () => {
        const m = window.jupyterapp.serviceManager;
        await m.sessions.refreshRunning();
        for (const s of Array.from(m.sessions.running())) await m.sessions.shutdown(s.id);
        await m.kernels.refreshRunning();
        for (const k of Array.from(m.kernels.running())) await m.kernels.shutdown(k.id);
        if (m.terminals.isAvailable()) {
          await m.terminals.refreshRunning();
          for (const t of Array.from(m.terminals.running())) await m.terminals.shutdown(t.name);
        }
      });
      if (!keepLauncher) await lab.closeLauncher();
      await page.waitForTimeout(300);
    },
    async exec(command, args = {}) {
      return page.evaluate(([c, a]) => window.jupyterapp.commands.execute(c, a).then(() => true), [command, args]);
    },
    async closeLauncher() {
      await page.evaluate(() => {
        for (const w of Array.from(window.jupyterapp.shell.widgets('main'))) {
          if (w.title.label === 'Launcher') w.close();
        }
      });
    },
    async closeAll() {
      await lab.exec('application:close-all');
      await page.waitForTimeout(300);
    },
    async openFile(filePath, factory) {
      await lab.exec('docmanager:open', factory ? { path: filePath, factory } : { path: filePath });
      await page.waitForTimeout(300);
      await lab.closeLauncher();
    },
    async waitKernelIdle(timeout = 60000) {
      await page.waitForFunction(
        () => {
          const w = window.jupyterapp.shell.currentWidget;
          const s = w && w.sessionContext;
          return s && s.session && s.session.kernel && s.session.kernel.status === 'idle';
        },
        null,
        { timeout }
      );
    },
    async setSetting(plugin, key, value) {
      await page.evaluate(
        async ([plugin, key, value]) => {
          const app = window.jupyterapp;
          for (const token of app.pluginRegistry._services.keys()) {
            if (token.name === '@jupyterlab/settingregistry:ISettingRegistry' || token.name === '@jupyterlab/coreutils:ISettingRegistry') {
              const registry = await app.resolveRequiredService(token);
              await registry.set(plugin, key, value);
              return;
            }
          }
          throw new Error('no setting registry');
        },
        [plugin, key, value]
      );
    },
    /** Collapse or show the side bars: { left: false } hides the left panel. */
    async sidebars({ left, right } = {}) {
      await page.evaluate(
        ([left, right]) => {
          const shell = window.jupyterapp.shell;
          if (left === false) shell.collapseLeft();
          if (right === false) shell.collapseRight();
        },
        [left, right]
      );
      await page.waitForTimeout(200);
    }
  };
  return lab;
}

/**
 * Start a take: launch Chromium at width x height CSS px and `dsf`, open no
 * page yet. Returns the take object; call record() when the stage is set.
 */
async function startTake({ name, port, width = 1152, height = 648, dsf = 2.5, seed = 7, fps = 30 }) {
  const dir = path.join(TAKES, name);
  fs.mkdirSync(dir, { recursive: true });
  for (const f of ['raw.mp4', 'raw.mp4.timeline.jsonl', 'input.jsonl', 'meta.json']) {
    fs.rmSync(path.join(dir, f), { force: true });
  }
  const { browser, context, page } = await launch({ dsf, width, height });
  await context.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: `http://localhost:${port}` });
  page.setDefaultTimeout(20000);
  page.on('pageerror', e => console.log('PAGEERROR', e.message));
  H.setSeed(seed);
  // take.k scales coordinates written for a 1440 px wide viewport to this one.
  const take = { name, port, dir, browser, context, page, width, height, dsf, fps, k: width / 1440, rec: null, input: [], marks: 0 };
  instrument(page, take);
  take.lab = labHelpers(take);
  take.H = H;

  take.record = async () => {
    take.rec = await startRecording(page, {
      file: path.join(dir, 'raw.mp4'),
      fps,
      crf: 14,
      preset: 'veryfast',
      fragmented: true
    });
    take.rec.mark('setup', { name, port, width, height, dsf, fps });
    await take.flash('start');
    // The pointer starts where it is, with no path from (0, 0).
    const at = H.position(page);
    take.input.push({ t: take.rec.now(), k: 'move', x: round1(at.x), y: round1(at.y) });
  };

  /** A magenta square in the top left corner for 400 ms: the cut measures the capture delay from it. */
  take.flash = async label => {
    const t = take.rec.now();
    await page.evaluate(() => {
      const d = document.createElement('div');
      d.style.cssText = 'position:fixed;left:0;top:0;width:10px;height:10px;background:#ff00ff;z-index:2147483647;pointer-events:none';
      document.documentElement.appendChild(d);
      setTimeout(() => d.remove(), 400);
    });
    take.rec.mark('flash', { name: label, at: t });
    await page.waitForTimeout(450);
  };

  take.mark = (kind, data = {}) => take.rec.mark(kind, data);
  take.beat = name => take.rec.mark('beat', { name });

  /**
   * Ask the cut to frame `target` from now on: { zoom (the most it may
   * enlarge), pad (CSS px around the box), spot (dim the rest) }.
   */
  take.focus = async (name, target, options = {}) => {
    let box = await boxOf(page, target, options.content !== false);
    if (box && options.maxHeight && box.height > options.maxHeight) box = { ...box, height: options.maxHeight };
    if (box && options.maxWidth && box.width > options.maxWidth) box = { ...box, width: options.maxWidth };
    if (!box) {
      console.log('focus: no box for', name);
      return null;
    }
    take.rec.mark('focus', { name, box, ...options });
    return box;
  };
  take.unfocus = (name = 'full') => take.rec.mark('focus', { name, box: null });
  /** A region with its words, for outlining a phrase in the cut. */
  take.region = async (name, target) => {
    const locator = typeof target === 'string' ? page.locator(target).first() : target;
    const region = await regionOf(locator).catch(() => null);
    if (region) take.rec.mark('region', { name, ...region });
    return region;
  };
  take.boxOf = target => boxOf(page, target);

  take.stop = async () => {
    await take.flash('end');
    const stats = await take.rec.stop();
    const lines = take.input.filter(e => e.t !== null).map(e => JSON.stringify(e));
    fs.writeFileSync(path.join(dir, 'input.jsonl'), lines.join('\n') + '\n');
    fs.writeFileSync(
      path.join(dir, 'meta.json'),
      JSON.stringify({ name, port, width, height, dsf, fps, stats: { durationS: stats.durationS, framesReceived: stats.framesReceived, duplicates: stats.duplicates, late: stats.lateFrames } }, null, 1)
    );
    await browser.close();
    console.log(`take ${name}: ${stats.durationS.toFixed(1)} s, ${stats.framesReceived} frames received, ${stats.lateFrames} late`);
    return stats;
  };
  take.abort = async () => {
    try {
      if (take.rec) await take.rec.stop();
    } catch (e) {
      console.log('abort stop failed', e.message);
    }
    await browser.close();
  };
  return take;
}

module.exports = { startTake, H, union, boxOf, TAKES };
