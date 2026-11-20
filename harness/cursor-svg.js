'use strict';
// The pointer drawn in recordings: a black arrow with an even white edge and a soft shadow.
// Coordinates in a 24 x 24 box with the tip at (2, 2).
const ARROW = 'M2 2 L2 19.5 L6.3 15.6 L9.2 22.3 L12.3 21 L9.5 14.6 L15.4 14.6 Z';
function cursorSvg(size = 24) {
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24">` +
    '<defs><filter id="s" x="-50%" y="-50%" width="200%" height="200%">' +
    '<feDropShadow dx="0" dy="0.8" stdDeviation="0.9" flood-color="#000" flood-opacity="0.35"/></filter></defs>' +
    `<path d="${ARROW}" fill="#111" stroke="#fff" stroke-width="1.5" stroke-linejoin="round" filter="url(#s)"/>` +
    '</svg>'
  );
}
/** An init script that draws the pointer in the page, for GIFs made from screenshots. */
function pageCursorScript() {
  return `(() => {
    if (window.__rvCursor) return; window.__rvCursor = true;
    const el = document.createElement('div');
    el.id = 'rv-cursor';
    el.innerHTML = ${JSON.stringify(cursorSvg(24))} + '<div class="ring"></div>';
    const style = document.createElement('style');
    style.textContent = '#rv-cursor{position:fixed;left:-100px;top:-100px;width:24px;height:24px;margin:-2px 0 0 -2px;pointer-events:none;z-index:2147483647}' +
      '#rv-cursor .ring{position:absolute;left:-10px;top:-10px;width:24px;height:24px;border-radius:50%;border:2px solid rgba(25,118,210,.75);opacity:0;transition:opacity .15s}' +
      '#rv-cursor.down .ring{opacity:1}';
    const add = () => { document.head.appendChild(style); document.documentElement.appendChild(el); };
    if (document.head) add(); else document.addEventListener('DOMContentLoaded', add);
    const move = e => { el.style.left = e.clientX + 'px'; el.style.top = e.clientY + 'px'; };
    addEventListener('pointermove', move, true); addEventListener('mousemove', move, true);
    addEventListener('pointerdown', e => { move(e); el.classList.add('down'); }, true);
    addEventListener('pointerup', () => el.classList.remove('down'), true);
  })();`;
}
module.exports = { cursorSvg, pageCursorScript, ARROW };
