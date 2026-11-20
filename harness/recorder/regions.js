// Regions of the screen that the cut can zoom on or highlight.
//
// markRegion(page, rec, name, locator) writes a `region` mark to the take's
// timeline: the element's box, and each visual line of text inside it with
// its words, all in CSS pixels of the viewport (a frame pixel is a CSS pixel
// times the take's scale). The narration names a region and a phrase; the
// assembler finds the words of the phrase in the region's lines and zooms on
// them or draws a box around them. Only what is inside the viewport counts.

async function regionOf(locator, { maxWords = 2000 } = {}) {
  const handle = await locator.elementHandle({ timeout: 2000 }).catch(() => null);
  if (!handle) return null;
  return handle.evaluate((element, maxWords) => {
    const view = { width: window.innerWidth, height: window.innerHeight };
    const clip = r => {
      const x = Math.max(0, r.x);
      const y = Math.max(0, r.y);
      const right = Math.min(view.width, r.x + r.width);
      const bottom = Math.min(view.height, r.y + r.height);
      return right > x && bottom > y ? { x, y, width: right - x, height: bottom - y } : null;
    };
    const round = r => ({
      x: Math.round(r.x * 10) / 10,
      y: Math.round(r.y * 10) / 10,
      width: Math.round(r.width * 10) / 10,
      height: Math.round(r.height * 10) / 10
    });
    const box = clip(element.getBoundingClientRect());
    if (!box) return null;
    // The words, each with its first visible client rect.
    const words = [];
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    const range = document.createRange();
    for (let node = walker.nextNode(); node && words.length < maxWords; node = walker.nextNode()) {
      const parent = node.parentElement;
      if (!parent || getComputedStyle(parent).visibility === 'hidden') continue;
      const text = node.textContent;
      const pattern = /\S+/g;
      let match;
      while ((match = pattern.exec(text)) && words.length < maxWords) {
        range.setStart(node, match.index);
        range.setEnd(node, match.index + match[0].length);
        const rect = Array.from(range.getClientRects()).find(r => r.width >= 1 && r.height >= 1);
        const seen = rect && clip(rect);
        if (seen) words.push({ t: match[0], ...round(seen) });
      }
    }
    // Words whose vertical centres are within half a line of each other share a line.
    words.sort((a, b) => a.y + a.height / 2 - (b.y + b.height / 2) || a.x - b.x);
    const lines = [];
    for (const word of words) {
      const middle = word.y + word.height / 2;
      const line = lines.find(l => Math.abs(l.middle - middle) < Math.min(l.height, word.height) / 2);
      if (line) {
        line.words.push(word);
        line.height = Math.max(line.height, word.height);
      } else {
        lines.push({ middle, height: word.height, words: [word] });
      }
    }
    return {
      box: round(box),
      lines: lines.map(l => {
        l.words.sort((a, b) => a.x - b.x);
        const x = Math.min(...l.words.map(w => w.x));
        const y = Math.min(...l.words.map(w => w.y));
        const right = Math.max(...l.words.map(w => w.x + w.width));
        const bottom = Math.max(...l.words.map(w => w.y + w.height));
        return {
          text: l.words.map(w => w.t).join(' '),
          box: round({ x, y, width: right - x, height: bottom - y }),
          words: l.words
        };
      })
    };
  }, maxWords);
}

async function markRegion(page, rec, name, locator, options = {}) {
  const region = await regionOf(locator, options).catch(() => null);
  if (region) rec.mark('region', { name, ...region });
  return region;
}

module.exports = { regionOf, markRegion };
