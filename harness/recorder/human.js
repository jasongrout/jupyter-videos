'use strict';
// Pointer and keyboard input that moves like a person, for a 1920x1080 CSS
// viewport. Every helper takes the Playwright page first and resolves when the
// movement is over.
//
//   const h = require('./human');
//   await h.place(page, 960, 700);            // before the recording starts
//   await h.click(page, page.getByRole('button', { name: 'Load' }));
//   await h.type(page, 'Does wt82_71 differ by qsmk?');
//   await h.drag(page, column, cell);
//
// Playwright does not expose the pointer position, so this module keeps it
// per page, starting at (0, 0) as Playwright does. Call place() once before
// recording, and sync() after a reload (a new document draws the cursor only
// after the next mouse event).

const positions = new WeakMap();

// What writes each move and press of the pointer into the take's timeline:
// record_take.js gives rec.mark. The cut (cutplan.py) ends a zoom before the
// pointer moves out of it, so that the viewer sees where it goes.
let marker = null;
/** Write each move ('move') and press ('press') into the timeline with `mark(kind, data)`. */
function setMarker(mark) {
  marker = mark;
}
function note(kind, data) {
  if (marker) marker(kind, data);
}
const r1 = v => Math.round(v * 10) / 10;

// A small seeded generator, so that a take moves the same way each time.
let seed = 0x5eed1234;
function random() {
  seed = (seed + 0x6d2b79f5) | 0;
  let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
}
/** Restart the random generator (jitter, arcs, typing rhythm) from `n`. */
function setSeed(n) {
  seed = n | 0;
}
const between = (a, b) => a + (b - a) * random();
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const sleep = ms => new Promise(resolve => setTimeout(resolve, Math.max(0, ms)));
const easeInOutCubic = u => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);

/** The pointer position that this module last sent to `page`. */
function position(page) {
  return positions.get(page) || { x: 0, y: 0 };
}

/** Move the pointer to (x, y) at once, with no path. */
async function place(page, x, y) {
  await page.mouse.move(x, y);
  positions.set(page, { x, y });
}

/** Send the pointer position again, so that a newly loaded document draws the cursor. */
async function sync(page) {
  const { x, y } = position(page);
  await page.mouse.move(x, y);
}

/** Milliseconds that a person takes to move the pointer over `distance` CSS px. */
function moveDuration(distance) {
  return clamp(250 + 15 * Math.sqrt(distance), 350, 900);
}

/**
 * Move the pointer to (x, y) along an eased path (cubic in and out) with a
 * slight arc, one point about every 16 ms. Options: ms (the duration; by
 * default 350 to 900 ms, growing with the distance), arc (the bend as a
 * fraction of the distance, by default 0.04 to 0.1 to a random side, at most
 * 60 px).
 */
async function moveTo(page, x, y, options = {}) {
  const from = position(page);
  const dx = x - from.x;
  const dy = y - from.y;
  const distance = Math.hypot(dx, dy);
  if (distance < 1) {
    await place(page, x, y);
    return;
  }
  const ms = options.ms ?? moveDuration(distance);
  note('move', { from: [r1(from.x), r1(from.y)], to: [r1(x), r1(y)], ms: Math.round(ms) });
  const bend = clamp((options.arc ?? between(0.04, 0.1)) * distance, -60, 60) * (random() < 0.5 ? -1 : 1);
  // A quadratic Bezier curve whose control point sits off the straight line.
  const cx = from.x + dx / 2 + (-dy / distance) * bend;
  const cy = from.y + dy / 2 + (dx / distance) * bend;
  const start = Date.now();
  for (;;) {
    // The point for the time now, so that a slow event keeps the speed right.
    const u = Math.min(1, (Date.now() - start) / ms);
    const s = easeInOutCubic(u);
    const px = (1 - s) * (1 - s) * from.x + 2 * (1 - s) * s * cx + s * s * x;
    const py = (1 - s) * (1 - s) * from.y + 2 * (1 - s) * s * cy + s * s * y;
    await page.mouse.move(px, py);
    positions.set(page, { x: px, y: py });
    if (u >= 1) break;
    const next = start + Math.ceil((Date.now() - start + 1) / 16) * 16;
    await sleep(Math.min(next, start + ms) - Date.now());
  }
}

async function viewport(page) {
  return page.viewportSize() || page.evaluate(() => ({ width: innerWidth, height: innerHeight }));
}

/**
 * The point to aim at on `locator`: its centre plus (dx, dy), or `position`
 * from its top left corner as in Playwright; by default a few px off the
 * centre, as a person aims. Scrolls the element into view when it is outside.
 */
async function pointOf(page, locator, options = {}) {
  await locator.waitFor({ state: 'visible' });
  let box = await locator.boundingBox();
  if (!box) throw new Error('human: the element has no box');
  const vp = await viewport(page);
  if (box.x < 0 || box.y < 0 || box.x + box.width > vp.width || box.y + box.height > vp.height) {
    await locator.scrollIntoViewIfNeeded();
    box = await locator.boundingBox();
  }
  if (options.position) return { x: box.x + options.position.x, y: box.y + options.position.y, box };
  const jx = options.dx ?? between(-1, 1) * Math.min(6, box.width * 0.15);
  const jy = options.dy ?? between(-1, 1) * Math.min(4, box.height * 0.15);
  return { x: box.x + box.width / 2 + jx, y: box.y + box.height / 2 + jy, box };
}

/**
 * Move the pointer onto `locator`. Options: dx, dy (from the centre),
 * position ({ x, y } from the top left corner), ms, arc. When the element
 * moved during the motion, a short second motion corrects it. Returns the point.
 */
async function moveToLocator(page, locator, options = {}) {
  const target = await pointOf(page, locator, options);
  await moveTo(page, target.x, target.y, options);
  const box = await locator.boundingBox();
  if (box && !(target.x >= box.x && target.x <= box.x + box.width && target.y >= box.y && target.y <= box.y + box.height)) {
    const again = await pointOf(page, locator, options);
    await moveTo(page, again.x, again.y, { ms: 250 });
    return again;
  }
  return target;
}

/**
 * Move onto `locator` and click it. Options: pauseBefore (ms between arriving
 * and pressing, 120 to 220 by default), hold (ms the button stays down, 60 to
 * 100), button, modifiers (keys held during the click, such as ['Shift']),
 * and those of moveToLocator.
 */
async function click(page, locator, options = {}) {
  await moveToLocator(page, locator, options);
  await sleep(options.pauseBefore ?? between(120, 220));
  const modifiers = options.modifiers || [];
  for (const key of modifiers) await page.keyboard.down(key);
  const at = position(page);
  note('press', { at: [r1(at.x), r1(at.y)], what: 'click' });
  await page.mouse.down({ button: options.button || 'left' });
  await sleep(options.hold ?? between(60, 100));
  await page.mouse.up({ button: options.button || 'left' });
  for (const key of modifiers.slice().reverse()) await page.keyboard.up(key);
}

/** Move onto `locator` and double-click it. Options as for click(). */
async function dblclick(page, locator, options = {}) {
  await moveToLocator(page, locator, options);
  await sleep(options.pauseBefore ?? between(120, 220));
  const at = position(page);
  note('press', { at: [r1(at.x), r1(at.y)], what: 'double click' });
  await page.mouse.down({ clickCount: 1 });
  await sleep(between(50, 80));
  await page.mouse.up({ clickCount: 1 });
  await sleep(between(70, 110));
  await page.mouse.down({ clickCount: 2 });
  await sleep(between(50, 80));
  await page.mouse.up({ clickCount: 2 });
}

/**
 * Press on the pointer's position and move it a few px toward (tx, ty), in
 * small steps, until Chromium starts the drag (its threshold is a few px).
 */
async function startDrag(page, tx, ty, options = {}) {
  const from = position(page);
  const d = Math.hypot(tx - from.x, ty - from.y) || 1;
  const ux = (tx - from.x) / d;
  const uy = (ty - from.y) / d;
  note('press', { at: [r1(from.x), r1(from.y)], what: 'drag', to: [r1(tx), r1(ty)] });
  await page.mouse.down();
  await sleep(options.holdBefore ?? between(90, 140));
  for (const step of options.startSteps || [2, 5, 9, 14]) {
    const px = from.x + ux * step;
    const py = from.y + uy * step + (step > 4 ? 1 : 0);
    await page.mouse.move(px, py);
    positions.set(page, { x: px, y: py });
    await sleep(30);
  }
}

/** Small moves on the spot for `ms`, so that the target keeps getting dragover events. */
async function hover(page, ms) {
  const { x, y } = position(page);
  const start = Date.now();
  let i = 0;
  while (Date.now() - start < ms) {
    const px = x + [0, 1, 0, -1][i % 4];
    const py = y + [1, 0, -1, 0][i % 4];
    await page.mouse.move(px, py);
    i++;
    await sleep(60);
  }
  await page.mouse.move(x, y);
}

/**
 * Drag `from` onto `to`, the way HTML5 drag and drop works in Chromium under
 * Playwright: move onto the source, press, a few small moves to start the
 * drag, an eased path to the target, a short hover there, release. Lumino's
 * own drags (tabs, cells) work the same way. Options: from and to (options of
 * moveToLocator for each end), pauseBefore, hoverMs (300 to 450), ms (of the
 * main path), modifiers (keys held from the press to the release, such as
 * ['Shift'] or ['Alt']), onHover (an async function called on arrival at the
 * target, before the hover: a place for a mark or a check).
 */
async function drag(page, from, to, options = {}) {
  await moveToLocator(page, from, options.from || {});
  await sleep(options.pauseBefore ?? between(150, 250));
  const modifiers = options.modifiers || [];
  for (const key of modifiers) await page.keyboard.down(key);
  const aim = await pointOf(page, to, options.to || {});
  await startDrag(page, aim.x, aim.y, options);
  // Where the target is now: a drag can open drop zones that move it.
  const target = await pointOf(page, to, options.to || {});
  await moveTo(page, target.x, target.y, { ms: options.ms, arc: options.arc });
  if (options.onHover) await options.onHover();
  await hover(page, options.hoverMs ?? between(300, 450));
  await page.mouse.up();
  for (const key of modifiers.slice().reverse()) await page.keyboard.up(key);
  await sleep(between(80, 140));
}

/**
 * Start a drag on `locator` and drop it back on the same element: press, move
 * out by about `away` px (14 by default) in a small arc, come back near the
 * press point, hover, release. Options: away, hoverMs, modifiers, onHover,
 * and those of moveToLocator.
 */
async function dragOntoSelf(page, locator, options = {}) {
  const p = await moveToLocator(page, locator, options);
  await sleep(options.pauseBefore ?? between(150, 250));
  const modifiers = options.modifiers || [];
  for (const key of modifiers) await page.keyboard.down(key);
  const away = options.away ?? 14;
  await startDrag(page, p.x + away, p.y + away * 0.6, options);
  await moveTo(page, p.x + away * 1.2, p.y + away * 0.2, { ms: 160, arc: 0 });
  await moveTo(page, p.x + between(-2, 2), p.y + between(-1, 1), { ms: 260, arc: 0.15 });
  if (options.onHover) await options.onHover();
  await hover(page, options.hoverMs ?? between(300, 450));
  await page.mouse.up();
  for (const key of modifiers.slice().reverse()) await page.keyboard.up(key);
  await sleep(between(80, 140));
}

/**
 * Type `text` one character at a time, about `cps` characters a second (10.5
 * by default) with jitter, a slightly longer pause after a space and after
 * punctuation. A newline presses Enter.
 */
async function type(page, text, options = {}) {
  const cps = options.cps ?? 10.5;
  for (const ch of text) {
    const start = Date.now();
    if (ch === '\n') await page.keyboard.press('Enter');
    else await page.keyboard.type(ch);
    let gap = (1000 / cps) * between(0.65, 1.35);
    if (ch === ' ') gap *= 1.5;
    else if (/[.,;:!?]/.test(ch)) gap *= 1.3;
    await sleep(gap - (Date.now() - start));
  }
}

/**
 * Scroll by `dy` CSS px (and `dx`) where the pointer is, in small wheel steps
 * with an eased speed. Options: ms (by default 250 to 1500, growing with the
 * distance), dx.
 */
async function wheel(page, dy, options = {}) {
  const dx = options.dx ?? 0;
  const distance = Math.hypot(dx, dy);
  const ms = options.ms ?? clamp(250 + distance * 0.6, 250, 1500);
  const start = Date.now();
  let doneX = 0;
  let doneY = 0;
  for (;;) {
    const u = Math.min(1, (Date.now() - start) / ms);
    const s = easeInOutCubic(u);
    const stepX = Math.round(dx * s) - doneX;
    const stepY = Math.round(dy * s) - doneY;
    if (stepX || stepY) {
      await page.mouse.wheel(stepX, stepY);
      doneX += stepX;
      doneY += stepY;
    }
    if (u >= 1) break;
    const next = start + Math.ceil((Date.now() - start + 1) / 16) * 16;
    await sleep(Math.min(next, start + ms) - Date.now());
  }
}

/** Wait like a person who reads: `ms`, or 400 to 700 ms. */
async function pause(ms) {
  await sleep(ms ?? between(400, 700));
}

module.exports = {
  place,
  sync,
  position,
  moveTo,
  moveToLocator,
  click,
  dblclick,
  drag,
  dragOntoSelf,
  hover,
  type,
  wheel,
  pause,
  setSeed,
  setMarker,
  moveDuration
};
