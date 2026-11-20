'use strict';
// Screen recorder for a Playwright page.
//
// The DevTools screencast sends a JPEG frame when the page changes. A timer in
// Node writes one JPEG to ffmpeg's stdin per 1/fps s (the newest frame, or a
// duplicate of it when the page did not change), so the video timeline equals
// wall-clock time: `now()` at an action is the time of that action in the
// video. ffmpeg encodes while recording (libx264); no frame touches the disk.
//
//   const { launch, startRecording } = require('./recorder');
//   const { browser, page } = await launch({ dsf: 2 });
//   const rec = await startRecording(page, { file: 'take.mp4' });
//   rec.mark('narration', { id: 'intro_1' });
//   ...
//   const stats = await rec.stop();
//
// The measurements and the limits are in ../notes/recorder-report.md.

const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

const FFMPEG = process.env.FFMPEG || 'ffmpeg';
const { CHROMIUM, FULL_CHROMIUM, PLAYWRIGHT_CORE } = require('./browser');
const BROWSERS = {
  // RV_CHROMIUM, or the newest headless shell (browser.js).
  shell: CHROMIUM,
  full: FULL_CHROMIUM
};

// The screencast's JPEGs are full-range YCbCr with the BT.601 matrix.
// 'bt709' converts them to the usual HD format (limited range, BT.709 matrix,
// tagged as such), which players, editors and YouTube all read correctly.
// 'source' passes them through: ffmpeg then writes full-range BT.601
// (yuvj420p), which shows the right colours only where the player reads the
// tags; a player that assumes BT.709 shifts saturated colours by up to 22 of
// 255 levels.
const COLOUR = {
  bt709:
    'format=rgb24,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,' +
    'setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709',
  source: null
};

/**
 * Launch Chromium for a recording, with a CSS viewport of width x height and a
 * real device scale factor `dsf`, so that the screencast sends frames of
 * (width * dsf) x (height * dsf) device pixels.
 *
 * Do not emulate the viewport (`newContext({ viewport })` or
 * `page.setViewportSize()`): Playwright then sets an emulated device scale
 * factor (1 when none is given), and the screencast sends frames of the
 * window size (1920x1080) even at an emulated factor of 2.
 *
 * Options: browser ('shell', the default, 'full', or a path), dsf (1),
 * width (1920), height (1080), scrollbars (false: Playwright hides them in
 * headless mode), args (more Chromium switches), and any other option of
 * chromium.launch(). Returns { browser, context, page }.
 */
async function launch(options = {}) {
  const { browser = 'shell', dsf = 1, width = 1920, height = 1080, scrollbars = false, args = [], ...rest } = options;
  const { chromium } = require(PLAYWRIGHT_CORE);
  const b = await chromium.launch({
    executablePath: BROWSERS[browser] || browser,
    headless: true,
    args: [`--force-device-scale-factor=${dsf}`, `--window-size=${width},${height}`, ...args],
    ignoreDefaultArgs: scrollbars ? ['--hide-scrollbars'] : undefined,
    ...rest
  });
  const context = await b.newContext({ viewport: null });
  const page = await context.newPage();
  await fitWindow(page, width, height);
  return { browser: b, context, page };
}

/**
 * Resize the window until the page's CSS viewport is width x height. The full
 * browser counts its hidden toolbar (87 px) in the window size; the headless
 * shell does not.
 */
async function fitWindow(page, width, height) {
  for (let attempt = 0; attempt < 3; attempt++) {
    const [iw, ih] = await page.evaluate(() => [innerWidth, innerHeight]);
    if (iw === width && ih === height) return;
    const cdp = await page.context().newCDPSession(page);
    const { windowId, bounds } = await cdp.send('Browser.getWindowForTarget');
    await cdp.send('Browser.setWindowBounds', {
      windowId,
      bounds: { width: bounds.width + width - iw, height: bounds.height + height - ih }
    });
    await cdp.detach();
    await page.waitForTimeout(100);
  }
  const [iw, ih] = await page.evaluate(() => [innerWidth, innerHeight]);
  if (iw !== width || ih !== height) throw new Error(`fitWindow: the viewport is ${iw}x${ih}, not ${width}x${height}`);
}

/** Width and height of a JPEG, from its SOF marker. */
function jpegSize(buf) {
  let i = 2;
  while (i + 9 < buf.length) {
    if (buf[i] !== 0xff) {
      i++;
      continue;
    }
    const m = buf[i + 1];
    if (m >= 0xc0 && m <= 0xcf && m !== 0xc4 && m !== 0xc8 && m !== 0xcc) {
      return { width: buf.readUInt16BE(i + 7), height: buf.readUInt16BE(i + 5) };
    }
    i += 2 + buf.readUInt16BE(i + 2);
  }
  return null;
}

function percentile(sorted, p) {
  if (!sorted.length) return null;
  return sorted[Math.min(sorted.length - 1, Math.floor(p * sorted.length))];
}

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Start recording `page` into an mp4. Resolves once the first frame is in.
 *
 * Options:
 * - file: the mp4 path (required). Marks go to `<file>.timeline.jsonl`.
 * - fps (30), quality (90, the JPEG quality of the screencast), crf (16),
 *   preset ('veryfast').
 * - width, height: the frame size in device pixels; by default the CSS
 *   viewport times the device scale factor.
 * - placement: 'capture' (the default) shows at video time t the newest frame
 *   that Chromium captured at or before t, by the frame's own timestamp, so
 *   that the time Chromium takes to encode a frame and a busy Node event loop
 *   do not shift what the video shows; the writer runs `delayMs` behind the
 *   clock to wait for frames still being encoded. 'arrival' shows the newest
 *   frame that reached Node before t, and writes with no delay.
 * - delayMs: for 'capture', 150 for frames up to 1920x1080, 300 above.
 * - phaseLock (true, for 'capture'): Chromium draws on a 60 Hz grid and the
 *   video takes every second frame. When the capture times sit close to the
 *   times of the video frames, a few ms of noise picks the frame before or
 *   the frame after, and the video steps by 17 and 50 ms instead of 33. The
 *   lock tracks the phase of the capture times on the grid and moves the
 *   boundary of each video frame half a grid step away from them (at most a
 *   step earlier or half a step later than the frame's time). A simulation,
 *   probes/phasesim.js, gives 0 to 1 uneven steps in 849 with the lock and up
 *   to 444 without it, for capture times with up to 3 ms of noise.
 * - vsyncMs: 1000 / 60, the grid of phaseLock.
 * - niceness (10): the scheduling priority of ffmpeg; it has a queue, so it
 *   can wait while Chromium uses the cores.
 * - colour: 'bt709' (the default) or 'source'; see COLOUR above.
 * - everyNthFrame (1): let Chromium capture only every n-th frame it draws
 *   (2 halves the cost of the screencast when the page draws at 60 fps).
 * - fragmented (false): write a fragmented mp4 in fragments of at most 1 s,
 *   flushed to the file as each is cut and synced to the disk every 2 s, so
 *   that a take cut short by a crash still plays up to about its last 2 to 3
 *   s; it cannot have +faststart. Without the flush, a killed ffmpeg left a
 *   file that does not play (its first 30 KB still in ffmpeg's buffer), and
 *   with fragments only at keyframes (every 8.3 s) up to 8 s are lost.
 * - keepLog (false): keep the arrival and capture time of every frame, in
 *   seconds of the timeline, in the `log` of stop()'s result.
 * - ffmpeg: the path of ffmpeg.
 *
 * Returns { now(), mark(kind, data), stats(), stop() }.
 */
async function startRecording(page, options = {}) {
  const file = options.file;
  if (!file) throw new Error('startRecording: options.file is required');
  const fps = options.fps ?? 30;
  const quality = options.quality ?? 90;
  const crf = options.crf ?? 16;
  const preset = options.preset ?? 'veryfast';
  const placement = options.placement ?? 'capture';
  if (placement !== 'capture' && placement !== 'arrival') throw new Error(`startRecording: unknown placement ${placement}`);
  const colour = options.colour ?? 'bt709';
  const everyNthFrame = options.everyNthFrame ?? 1;
  const phaseLock = placement === 'capture' && (options.phaseLock ?? true);
  const vsyncMs = options.vsyncMs ?? 1000 / 60;
  if (!(colour in COLOUR)) throw new Error(`startRecording: unknown colour ${colour}`);
  let { width, height } = options;
  if (!width || !height) {
    const [w, h, dpr] = await page.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]);
    width = width || Math.round(w * dpr);
    height = height || Math.round(h * dpr);
  }
  // Frames larger than 1920x1080 take Chromium longer to copy and encode: in
  // a take at 2880x1620, 1% of the frames came more than 150 ms after their
  // capture (the slowest 253 ms).
  const delayMs = placement === 'capture' ? (options.delayMs ?? (width * height > 1920 * 1080 ? 300 : 150)) : 0;
  fs.mkdirSync(path.dirname(path.resolve(file)), { recursive: true });

  // State of the clock, the frames and the writer.
  const wallOffset = Date.now() - performance.now(); // frame timestamps are wall-clock
  let t0 = null; // origin of the video timeline, on performance.now()
  const frames = []; // { at, buf }, oldest capture first ('capture')
  let latest = null; // the newest frame to arrive ('arrival')
  let received = 0;
  let lastArrival = null;
  let longestGapMs = 0;
  let late = 0;
  let firstSize = null;
  const latencies = [];
  const log = options.keepLog ? [] : null;
  const queue = []; // JPEGs for ffmpeg
  let enqueued = 0; // index of the next video frame to queue
  let written = 0;
  let duplicates = 0;
  let lastQueued = null;
  let writing = false;
  let drained = null;
  let timer = null;
  let stopped = false;
  let maxQueue = 0;
  // Phase of the capture times on the grid of vsyncMs: sums of unit vectors,
  // decayed by 0.9 a frame, so they follow a slow change.
  const phaseRef = performance.now();
  let phaseC = 0;
  let phaseS = 0;
  let phaseW = 0;
  let lockOffset = null; // boundary minus tick, while the lock is in effect
  let locked = 0;
  let gotFirst;
  const firstFrame = new Promise(resolve => (gotFirst = resolve));

  // ffmpeg: JPEGs on stdin at a constant rate, H.264 out.
  const vf = COLOUR[colour];
  const args = [
    '-hide_banner', '-nostats', '-loglevel', 'info', '-benchmark',
    '-f', 'image2pipe', '-c:v', 'mjpeg', '-framerate', String(fps), '-i', '-',
    ...(vf ? ['-vf', vf] : []),
    '-c:v', 'libx264', '-preset', preset, '-crf', String(crf), '-pix_fmt', 'yuv420p',
    ...(options.fragmented
      ? ['-movflags', '+frag_keyframe+empty_moov+default_base_moof', '-frag_duration', '1000000', '-flush_packets', '1']
      : ['-movflags', '+faststart']),
    '-y', file
  ];
  // Its own process group: Ctrl+C in a terminal stops Node only; ffmpeg then
  // reads the end of its input and finishes the file.
  const ff = spawn(options.ffmpeg || FFMPEG, args, { stdio: ['pipe', 'ignore', 'pipe'], detached: true });
  try {
    os.setPriority(ff.pid, options.niceness ?? 10);
  } catch {
    // Not allowed here: ffmpeg keeps the priority of Node.
  }
  let stderr = '';
  ff.stderr.on('data', d => {
    stderr += d;
    if (stderr.length > 200000) stderr = stderr.slice(-100000);
  });
  let ffError = null;
  // When ffmpeg is gone, nothing more can be written: drop the queue and
  // release a writer that waits for 'drain' and a stop() that waits for it.
  const abandon = error => {
    ffError = ffError || error;
    queue.length = 0;
    writing = false;
    if (drained) drained();
  };
  const ffClosed = new Promise(resolve =>
    ff.on('close', (code, signal) => {
      if (!stopped || code !== 0) {
        abandon(new Error(`ffmpeg exited during the recording with ${code ?? signal}`));
        if (!stopped) {
          try {
            writeLine({ t: Math.round(now() * 1000) / 1000, kind: 'ffmpeg-exit', code, signal });
          } catch {
            // The timeline is closed.
          }
        }
      }
      resolve({ code, signal });
    })
  );
  ff.on('error', e => abandon(e));
  ff.stdin.on('error', e => abandon(e));
  // A fragmented file: sync what ffmpeg wrote every 2 s (the kernel would keep
  // it in memory for up to 30 s), off the event loop.
  let syncing = false;
  const syncTimer = options.fragmented
    ? setInterval(() => {
        if (syncing) return;
        syncing = true;
        fs.open(file, 'r', (openError, fd) => {
          if (openError) {
            syncing = false;
            return;
          }
          fs.fsync(fd, () => fs.close(fd, () => (syncing = false)));
        });
      }, 2000)
    : null;

  // The timeline: one JSON object a line, written and synced at once, so that
  // a crash keeps every line logged before it.
  const timelinePath = `${file}.timeline.jsonl`;
  const timelineFd = fs.openSync(timelinePath, 'w');
  const writeLine = obj => {
    fs.writeSync(timelineFd, JSON.stringify(obj) + '\n');
    try {
      fs.fdatasyncSync(timelineFd);
    } catch {
      // No fdatasync on this file system: the write is enough.
    }
  };

  const now = () => (t0 === null ? 0 : (performance.now() - t0) / 1000);

  // Frames from Chromium: keep the buffer, then acknowledge at once (Chromium
  // holds back new frames while three are not acknowledged).
  const cdp = await page.context().newCDPSession(page);
  cdp.on('Page.screencastFrame', event => {
    const arrival = performance.now();
    const buf = Buffer.from(event.data, 'base64');
    cdp.send('Page.screencastFrameAck', { sessionId: event.sessionId }).catch(() => {});
    if (stopped) return;
    let at = event.metadata.timestamp ? event.metadata.timestamp * 1000 - wallOffset : arrival;
    // A frame is not captured after it arrives, nor seconds before.
    if (!(at <= arrival + 1 && at > arrival - 2000)) at = arrival;
    received++;
    if (lastArrival !== null) longestGapMs = Math.max(longestGapMs, arrival - lastArrival);
    lastArrival = arrival;
    latencies.push(arrival - at);
    if (log) log.push({ arrival: t0 === null ? 0 : (arrival - t0) / 1000, capture: t0 === null ? 0 : (at - t0) / 1000, bytes: buf.length });
    if (!firstSize) {
      firstSize = jpegSize(buf);
      if (firstSize && (firstSize.width !== width || firstSize.height !== height)) {
        console.warn(
          `recorder: the frames are ${firstSize.width}x${firstSize.height}, not ${width}x${height}; ` +
            'is the viewport emulated? See launch() in recorder.js.'
        );
      }
    }
    if (phaseLock) {
      const a = (2 * Math.PI * (at - phaseRef)) / vsyncMs;
      phaseC = phaseC * 0.9 + Math.cos(a);
      phaseS = phaseS * 0.9 + Math.sin(a);
      phaseW = phaseW * 0.9 + 1;
    }
    if (placement === 'capture') {
      // Late: a video frame that should show this one is already queued.
      if (t0 !== null && enqueued > 0 && at <= t0 + ((enqueued - 1) * 1000) / fps) late++;
      let i = frames.length;
      while (i > 0 && frames[i - 1].at > at) i--;
      frames.splice(i, 0, { at, buf });
    }
    latest = buf;
    gotFirst();
  });

  // The writer: hand the queued JPEGs to ffmpeg as fast as it reads them.
  const pump = () => {
    if (writing) return;
    writing = true;
    while (queue.length) {
      if (ffError) {
        queue.length = 0;
        break;
      }
      const buf = queue.shift();
      written++;
      if (!ff.stdin.write(buf)) {
        ff.stdin.once('drain', () => {
          writing = false;
          pump();
        });
        return;
      }
    }
    writing = false;
    if (drained) drained();
  };
  const push = buf => {
    if (buf === lastQueued) duplicates++;
    lastQueued = buf;
    queue.push(buf);
  };

  // Video frame k covers [k / fps, (k + 1) / fps) of the timeline and shows
  // the page as it was at k / fps. Queue every frame that starts at or before
  // `until` (a time on performance.now()).
  const enqueueUntil = until => {
    const due = Math.floor(((until - t0) * fps) / 1000) + 1;
    while (enqueued < due) {
      if (placement === 'capture') {
        const tickAt = t0 + (enqueued * 1000) / fps;
        // The newest frame captured at or before the tick (or before the
        // boundary of the phase lock). Before the first frame, the first one:
        // the page did not change in between, or Chromium would have sent one.
        let boundary = tickAt;
        if (phaseLock && phaseW > 3 && Math.hypot(phaseC, phaseS) / phaseW > 0.6) {
          // Boundaries half a grid step from the capture times; of those, the
          // one nearest to the previous boundary's place, so that noise in
          // the phase never makes it jump by a whole step. It stays within
          // a step before the tick and half a step after it.
          const phi = ((Math.atan2(phaseS, phaseC) / (2 * Math.PI)) * vsyncMs + vsyncMs) % vsyncMs;
          const mid = phi + vsyncMs / 2;
          const target = tickAt + (lockOffset ?? 0);
          let b = target - ((((target - phaseRef - mid) % vsyncMs) + vsyncMs) % vsyncMs);
          if (target - b > vsyncMs / 2) b += vsyncMs;
          let offset = b - tickAt;
          if (offset > vsyncMs / 2) offset -= vsyncMs;
          if (offset < -vsyncMs) offset += vsyncMs;
          lockOffset = offset;
          boundary = tickAt + offset;
          locked++;
        } else {
          lockOffset = null;
        }
        while (frames.length > 1 && frames[1].at <= boundary) frames.shift();
        if (!frames.length) return;
        push(frames[0].buf);
      } else {
        if (!latest) return;
        push(latest);
      }
      enqueued++;
    }
  };

  const tick = () => {
    if (stopped) return;
    enqueueUntil(performance.now() - delayMs);
    pump();
    maxQueue = Math.max(maxQueue, queue.length);
    const next = t0 + delayMs + (enqueued * 1000) / fps;
    timer = setTimeout(tick, Math.max(1, next - performance.now()));
  };

  await cdp.send('Page.startScreencast', { format: 'jpeg', quality, maxWidth: width, maxHeight: height, everyNthFrame });
  t0 = performance.now();
  // Chromium sends a first frame when the screencast starts. If none comes, a
  // screenshot makes the page draw one.
  const first = await Promise.race([firstFrame.then(() => true), sleep(1000).then(() => false)]);
  if (!first) {
    await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: 10 }).catch(() => {});
    await Promise.race([firstFrame, sleep(2000)]);
  }
  if (!received) {
    stopped = true;
    if (syncTimer) clearInterval(syncTimer);
    await cdp.send('Page.stopScreencast').catch(() => {});
    ff.stdin.end();
    fs.closeSync(timelineFd);
    throw new Error('startRecording: the screencast sent no frame');
  }
  writeLine({
    t: 0,
    kind: 'start',
    file: path.resolve(file),
    fps,
    width,
    height,
    quality,
    crf,
    preset,
    placement,
    delayMs,
    colour,
    everyNthFrame,
    phaseLock,
    fragmented: Boolean(options.fragmented),
    niceness: options.niceness ?? 10,
    wallClock: new Date(wallOffset + t0).toISOString(),
    epochMs: wallOffset + t0
  });
  tick();

  const stats = () => {
    const sorted = latencies.slice().sort((a, b) => a - b);
    return {
      file: path.resolve(file),
      timeline: path.resolve(timelinePath),
      fps,
      width,
      height,
      frameSize: firstSize,
      placement,
      framesReceived: received,
      framesWritten: written + queue.length,
      duplicates,
      longestGapMs: Math.round(longestGapMs),
      lateFrames: late,
      phaseLocked: locked,
      queue: queue.length,
      maxQueue,
      captureToNodeMs: {
        p50: Math.round(percentile(sorted, 0.5)),
        p95: Math.round(percentile(sorted, 0.95)),
        max: Math.round(sorted[sorted.length - 1])
      }
    };
  };

  return {
    /** Seconds on the video timeline. */
    now,
    /** Append { t, kind, ...data } to <file>.timeline.jsonl, synced at once. Returns t. */
    mark(kind, data = {}) {
      const entry = { t: Math.round(now() * 1000) / 1000, kind, ...data };
      writeLine(entry);
      return entry.t;
    },
    /** The counters so far. */
    stats,
    /**
     * Stop the screencast, write the frames up to now, and wait for ffmpeg to
     * finish the file. Returns stats() plus durationS (of the video), wallS
     * (now() at the call), bytes, and ffmpeg's CPU time.
     */
    async stop() {
      if (stopped) throw new Error('recorder: stop() was called twice');
      const end = performance.now();
      // Wait for the frames captured before the end.
      if (delayMs) await sleep(delayMs);
      stopped = true;
      clearTimeout(timer);
      if (syncTimer) clearInterval(syncTimer);
      await cdp.send('Page.stopScreencast').catch(() => {});
      await cdp.detach().catch(() => {});
      enqueueUntil(end);
      await new Promise(resolve => {
        drained = resolve;
        pump();
      });
      ff.stdin.end();
      const { code, signal } = await ffClosed;
      const result = stats();
      result.framesWritten = written;
      result.durationS = written / fps;
      result.wallS = (end - t0) / 1000;
      const bench = stderr.match(/bench: utime=([\d.]+)s stime=([\d.]+)s rtime=([\d.]+)s/);
      const rss = stderr.match(/bench: maxrss=(\d+)/);
      result.ffmpeg = bench ? { utimeS: +bench[1], stimeS: +bench[2], rtimeS: +bench[3], maxrssKiB: rss ? +rss[1] : null } : null;
      try {
        result.bytes = fs.statSync(file).size;
      } catch {
        result.bytes = null;
      }
      writeLine({ t: Math.round(result.wallS * 1000) / 1000, kind: 'stop', ...result });
      fs.closeSync(timelineFd);
      if (log) result.log = log;
      if (code !== 0 || ffError) {
        const tail = stderr.split('\n').filter(l => !l.startsWith('bench:')).slice(-15).join('\n');
        throw new Error(`recorder: ffmpeg exited with ${code ?? signal}${ffError ? ` (${ffError.message})` : ''}:\n${tail}`);
      }
      return result;
    }
  };
}

module.exports = { startRecording, launch, fitWindow, jpegSize, BROWSERS, FFMPEG };
