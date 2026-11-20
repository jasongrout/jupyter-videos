"""Cut the JupyterLab release video from its takes and an edit file.

Usage:
  python cut.py <edit.json> <out.mp4> [--preview] [--only i,j] [--stills t1,t2,...] [--no-audio]

The edit file lists the items of the video in order: cards (rendered from
HTML) and segments of takes. A take is a raw screen recording of a live
JupyterLab (2880x1620 for a 1440x810 CSS viewport at 2x), its timeline of marks
and its log of mouse and key events. For each output frame at 60 fps the cut:

- picks the source frame of the take for that moment (speed spans map output
  time to take time),
- moves a camera over the stage: the app sits in a window with rounded corners
  on a dark background, and `focus` marks of the take (boxes in CSS px) are the
  camera's targets, followed by a critically damped spring on the centre and on
  the logarithm of the zoom,
- dims the rest of the window around a focus box marked `spot`,
- draws the pointer, its click ripples and the key labels from the event log,
  shifted by the capture delay that the take's start flash measures,
- draws the feature title, badges and cards, rendered by Chromium from HTML.

Nothing in a take is edited: a span can only be cut, sped up (with a badge), or
held on a frame.
"""

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time
import textwrap
import wave
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
HERE = Path(__file__).resolve().parent
WORK = Path(os.environ.get("RV_WORK", HERE.parent / "work"))
TAKES = Path(os.environ.get("RV_TAKES", WORK / "takes"))
PARTS = WORK / "parts"
W, H = 1920, 1080
YUV_IN = "in_color_matrix=bt709:in_range=tv:out_range=pc"
FONT_BOLD = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"

# The app window at rest, in output pixels: the band above it holds the title.
R0 = (120.0, 110.0, 1680.0, 945.0)
TITLE_AT = (120, 30)
# The band above the window holds the title; it is drawn over a zoomed window.
BAND = 100
STAGE_RGB = (238, 238, 238)  # --jp-layout-color2
BRAND_RGB = (25, 118, 210)  # --jp-brand-color1
# Where a focused box may sit: below the title band, inside the frame.
FOCUS_AREA = (60.0, 120.0, W - 60.0, H - 40.0)
OMEGA = 5.0  # spring of the camera: 90% of a move in 0.78 s
ZOOM_CAP = 1.12  # gentle zooms: the window stays mostly in view
MERGE = 2.5  # focus boxes this close in time are framed together
SPOT_LEAD = 0.1  # s before the action that ends a spotlight
SPOT_FADE = 0.15  # s
LINE_GAP = 0.3  # s between two narration lines of a shot
KEYS_BOTTOM = 216  # px from the bottom edge to the key caps: two caption lines fit below


def ease_out_cubic(u):
    u = min(1.0, max(0.0, u))
    return 1 - (1 - u) ** 3


def ease_in_out(u):
    u = min(1.0, max(0.0, u))
    return 4 * u * u * u if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


# ---------------------------------------------------------------- overlays


class Overlays:
    """HTML overlays rendered to PNG by render_overlays.js, cached by their HTML."""

    def __init__(self):
        self.spec = {}
        self.images = {}

    def add(self, key, html, width, height):
        file = PARTS / "overlays" / f"{key}.png"
        self.spec[key] = {"file": str(file), "html": html, "width": width, "height": height}
        return key

    def render(self):
        PARTS.mkdir(parents=True, exist_ok=True)
        spec_file = PARTS / "overlays.json"
        spec_file.write_text(json.dumps(list(self.spec.values())))
        subprocess.run(["node", str(HERE / "render_overlays.js"), str(spec_file)], check=True)
        for key, item in self.spec.items():
            im = Image.open(item["file"]).convert("RGBA")
            self.images[key] = trim(im)

    def get(self, key):
        return self.images[key]


def trim(im):
    """Crop a transparent margin, keeping the top left corner where it was."""
    bbox = im.getchannel("A").getbbox()
    if not bbox:
        return im
    return im.crop((0, 0, bbox[2], bbox[3]))


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


KEY_NAMES = {
    "Control": "Ctrl", "Meta": "Cmd", "Alt": "Alt", "Shift": "Shift", "Enter": "Enter", "Escape": "Esc",
    "Backspace": "Backspace", "Tab": "Tab", "ArrowDown": "↓", "ArrowUp": "↑", "ArrowLeft": "←",
    "ArrowRight": "→", " ": "Space", "Delete": "Delete", "Home": "Home", "End": "End",
}


def key_label(combo):
    parts = combo.split("+") if combo != "+" else ["+"]
    # "Alt+-" splits into ["Alt", "-"]; "Control++" into ["Control", "", ""].
    if combo.endswith("++"):
        parts = combo[:-2].split("+") + ["+"]
    names = []
    for p in parts:
        if p == "":
            continue
        names.append(KEY_NAMES.get(p, p.upper() if len(p) == 1 else p))
    return names


# JupyterLab binds these with Accel, so a Mac takes Cmd for Ctrl; Run Cell also keeps Ctrl Enter there.
SAME_ON_MAC = {"Control+Enter"}
MAC_NAMES = {"Ctrl": "Cmd", "Alt": "Option"}


def mac_label(combo):
    """The Mac keys of a combination, or None when they are the same."""
    names = key_label(combo)
    if combo in SAME_ON_MAC or not any(n in MAC_NAMES for n in names):
        return None
    return " + ".join(MAC_NAMES.get(n, n) for n in names)


def keys_html(names, count, mac=None):
    inner = '<span class="plus">+</span>'.join(f'<span class="key">{esc(n)}</span>' for n in names)
    if count > 1:
        inner += f'<span class="times">×{count}</span>'
    below = f'<div class="mac">Mac: {esc(mac)}</div>' if mac else ""
    return f'<div class="keyblock"><div class="keys">{inner}</div>{below}</div>'


# ---------------------------------------------------------------- takes


class Take:
    def __init__(self, name):
        self.name = name
        self.dir = TAKES / name
        self.meta = json.loads((self.dir / "meta.json").read_text())
        self.marks = [json.loads(line) for line in (self.dir / "raw.mp4.timeline.jsonl").read_text().splitlines() if line.strip()]
        self.events = [json.loads(line) for line in (self.dir / "input.jsonl").read_text().splitlines() if line.strip()]
        self.css_w, self.css_h, self.dsf = self.meta["width"], self.meta["height"], self.meta["dsf"]
        self.src_w, self.src_h = int(self.css_w * self.dsf), int(self.css_h * self.dsf)
        self.fps = self.meta.get("fps", 30)
        self.duration = self.meta["stats"]["durationS"]
        self.age = self.measure_age()

    def measure_age(self):
        """Seconds from a mark to the frame that shows its effect, from the start flash."""
        flash = next(m for m in self.marks if m["kind"] == "flash" and m.get("name") == "start")
        size = int(8 * self.dsf)
        cmd = [FFMPEG, "-v", "error", "-t", str(flash["at"] + 2.0), "-i", str(self.dir / "raw.mp4"),
               "-vf", f"crop={size}:{size}:0:0,scale={YUV_IN},format=rgb24", "-f", "rawvideo", "-"]
        raw = subprocess.run(cmd, capture_output=True, check=True).stdout
        n = len(raw) // (size * size * 3)
        frames = np.frombuffer(raw[: n * size * size * 3], np.uint8).reshape(n, size, size, 3).astype(int)
        for i in range(n):
            r, g, b = frames[i, size // 2, size // 2]
            if r > 200 and g < 80 and b > 200:
                age = i / self.fps - flash["at"]
                return max(0.0, age)
        print(f"warning: no flash found in {self.name}; using 0.2 s")
        return 0.2

    def time(self, ref):
        """Content time (seconds of raw.mp4) of a reference: a number, or 'kind:name+offset'."""
        if isinstance(ref, (int, float)):
            return float(ref)
        offset = 0.0
        body = ref
        for sign in ("+", "-"):
            idx = body.rfind(sign)
            if idx > body.find(":"):
                try:
                    offset = float(body[idx:])
                    body = body[:idx]
                    break
                except ValueError:
                    pass
        kind, _, name = body.partition(":")
        for m in self.marks:
            if m["kind"] == kind and (not name or m.get("name") == name):
                return m["t"] + self.age + offset
        raise KeyError(f"{self.name}: no mark {ref}")

    def focus_marks(self):
        out = []
        for m in self.marks:
            if m["kind"] == "focus":
                out.append(dict(m, t=m["t"] + self.age + m.get("lead", 0.0)))
        return out


class Reader:
    """Sequential RGB frames of a take from a start index."""

    def __init__(self, take, start_index):
        self.take = take
        self.index = start_index - 1
        self.frame = None
        size = take.src_w * take.src_h * 3
        self.size = size
        self.proc = subprocess.Popen(
            [FFMPEG, "-v", "error", "-ss", f"{start_index / take.fps + 0.001:.4f}", "-i", str(take.dir / "raw.mp4"),
             "-vf", f"scale={YUV_IN},format=rgb24", "-f", "rawvideo", "-"],
            stdout=subprocess.PIPE, bufsize=size * 2)

    def get(self, index):
        while self.index < index:
            raw = self.proc.stdout.read(self.size)
            if len(raw) < self.size:
                break
            self.frame = np.frombuffer(raw, np.uint8).reshape(self.take.src_h, self.take.src_w, 3)
            self.index += 1
        return self.frame

    def close(self):
        self.proc.stdout.close()
        self.proc.kill()
        self.proc.wait()


# ---------------------------------------------------------------- geometry


def stage_box(take, box, pad=0.0):
    """A CSS px box of the take as a box on the stage at rest."""
    sx = R0[2] / take.css_w
    sy = R0[3] / take.css_h
    x, y, w, h = box["x"] - pad, box["y"] - pad, box["width"] + 2 * pad, box["height"] + 2 * pad
    return (R0[0] + x * sx, R0[1] + y * sy, w * sx, h * sy)


def clamp_axis(start, size, lo, hi):
    """Place a span of `size` so that it covers [lo, hi] when it can, else centre it there."""
    if size <= hi - lo:
        return lo + (hi - lo - size) / 2
    return min(lo, max(hi - size, start))


def camera_for(box_s, zoom_max):
    """Camera (cx, cy, k) that shows a stage box inside FOCUS_AREA."""
    ax0, ay0, ax1, ay1 = FOCUS_AREA
    bx, by, bw, bh = box_s
    k = min((ax1 - ax0) / max(bw, 1), (ay1 - ay0) / max(bh, 1), zoom_max)
    k = max(1.0, k)
    # Put the box centre on the area's centre.
    acx, acy = (ax0 + ax1) / 2, (ay0 + ay1) / 2
    bcx, bcy = bx + bw / 2, by + bh / 2
    cx = bcx - (acx - W / 2) / k
    cy = bcy - (acy - H / 2) / k
    return clamp_camera(cx, cy, k)


def clamp_camera(cx, cy, k):
    """Keep the window over the frame: no background shows beside or below a zoomed window."""
    wx = k * (R0[0] - cx) + W / 2
    wy = k * (R0[1] - cy) + H / 2
    ww, wh = k * R0[2], k * R0[3]
    nx = clamp_axis(wx, ww, R0[0] if k <= 1.0001 else 0.0, W - (R0[0] if k <= 1.0001 else 0.0))
    ny = clamp_axis(wy, wh, R0[1], H - (H - R0[1] - R0[3]))
    cx = R0[0] - (nx - W / 2) / k
    cy = R0[1] - (ny - H / 2) / k
    return cx, cy, k


REST = (W / 2, H / 2, 1.0)


# ---------------------------------------------------------------- drawing helpers


def corner_mask(r):
    """An anti-aliased quarter disc of radius r (top left corner), as an L image of r x r."""
    r = max(1, int(round(r)))
    s = 4
    big = Image.new("L", (r * s, r * s), 0)
    d = ImageDraw.Draw(big)
    d.ellipse((0, 0, 2 * r * s - 1, 2 * r * s - 1), fill=255)
    return big.resize((r, r), Image.LANCZOS)


_corner_cache = {}


def corners(r):
    r = max(1, int(round(r)))
    if r not in _corner_cache:
        tl = corner_mask(r)
        _corner_cache[r] = {
            "tl": tl,
            "tr": tl.transpose(Image.FLIP_LEFT_RIGHT),
            "bl": tl.transpose(Image.FLIP_TOP_BOTTOM),
            "br": tl.transpose(Image.ROTATE_180),
        }
    return _corner_cache[r]


def make_shadow():
    """The window's shadow at rest, as an RGBA image covering R0 with a margin."""
    m = 60
    w, h = int(R0[2]) + 2 * m, int(R0[3]) + 2 * m
    small = Image.new("L", (w // 4, h // 4), 0)
    d = ImageDraw.Draw(small)
    d.rectangle((m // 4, (m + 6) // 4, (m + R0[2]) // 4, (m + 6 + R0[3]) // 4), fill=95)
    small = small.filter(ImageFilter.GaussianBlur(4))
    alpha = small.resize((w, h), Image.BILINEAR)
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shadow.putalpha(alpha)
    return shadow, m


ARROW = "M2 2 L2 19.5 L6.3 15.6 L9.2 22.3 L12.3 21 L9.5 14.6 L15.4 14.6 Z"


def cursor_html(size):
    """The pointer: a black arrow with an even white edge and a soft shadow, in a 24 x 24 box."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24">'
            '<defs><filter id="s" x="-50%" y="-50%" width="200%" height="200%">'
            '<feDropShadow dx="0" dy="0.8" stdDeviation="0.9" flood-color="#000" flood-opacity="0.35"/></filter></defs>'
            f'<path d="{ARROW}" fill="#111" stroke="#fff" stroke-width="1.5" stroke-linejoin="round" filter="url(#s)"/></svg>')


# ---------------------------------------------------------------- segments


class Segment:
    """One stretch of a take: time map, camera track, events, title."""

    def __init__(self, item, overlays, fps):
        self.item = item
        self.take = Take(item["take"])
        t = self.take
        self.fps = fps
        self.t_from = t.time(item["from"])
        self.t_to = t.time(item["to"])
        spans = []
        for sp in item.get("speed", []):
            spans.append((t.time(sp["from"]), t.time(sp["to"]), float(sp["x"]), sp.get("badge", True)))
        spans.sort()
        # Pieces of take time with a speed each.
        pieces = []
        cursor = self.t_from
        for a, b, x, badge in spans:
            a, b = max(a, self.t_from), min(b, self.t_to)
            if b <= a:
                continue
            if a > cursor:
                pieces.append((cursor, a, 1.0, False))
            pieces.append((a, b, x, badge))
            cursor = b
        if cursor < self.t_to:
            pieces.append((cursor, self.t_to, 1.0, False))
        self.pieces = pieces
        self.length = sum((b - a) / x for a, b, x, _ in pieces) + item.get("hold_end", 0.0)
        self.frames = int(round(self.length * fps))
        self.focus = [m for m in t.focus_marks() if m.get("name") not in set(item.get("ignore_focus", []))]
        if item.get("spot") is False:
            # JupyterLab's own focus ring already marks the element.
            self.focus = [dict(m, spot=False) for m in self.focus]
        for extra in item.get("camera", []):
            self.focus.append({"t": t.time(extra["at"]), "name": extra.get("name", "edit"),
                               "box": extra.get("box") and {"x": extra["box"][0], "y": extra["box"][1], "width": extra["box"][2], "height": extra["box"][3]},
                               "zoom": extra.get("zoom", 1.8), "pad": extra.get("pad", 12), "spot": extra.get("spot", False)})
        clicks = sorted(e["t"] + t.age for e in t.events if e["k"] == "down")
        for m in self.focus:
            if m.get("spot") or not m.get("box"):
                continue
            before = [c for c in clicks if m["t"] - 1.0 <= c <= m["t"]]
            if before:
                m["t"] = before[-1] - 0.3
        self.focus.sort(key=lambda m: m["t"])
        # A click, or a key other than an arrow, ends a spotlight: arrows move inside it.
        boxed = [m for m in self.focus if m.get("box")]
        for m in boxed:
            near = [n["box"] for n in boxed if abs(n["t"] - m["t"]) <= MERGE and not n.get("alone")]
            if m.get("alone") or not near:
                near = [m["box"]]
            x0 = min(b["x"] for b in near)
            y0 = min(b["y"] for b in near)
            x1 = max(b["x"] + b["width"] for b in near)
            y1 = max(b["y"] + b["height"] for b in near)
            m["ubox"] = {"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0}
        actions = sorted(e["t"] + t.age for e in t.events
                         if e["k"] == "down" or (e["k"] == "press" and not e["key"].startswith("Arrow")))
        for m in self.focus:
            if m.get("spot"):
                # The outline is gone before the action changes the screen, so it never frames a dialog.
                m["spot_until"] = next((a for a in actions if a > m["t"] + 0.2), 1e9) - SPOT_LEAD
        self.events = [dict(e, t=e["t"] + t.age) for e in t.events]
        self.moves = [e for e in self.events if e["k"] == "move"]
        self.move_t = np.array([e["t"] for e in self.moves]) if self.moves else np.zeros(0)
        self.downs = [e for e in self.events if e["k"] == "down"]
        self.ups = [e for e in self.events if e["k"] == "up"]
        self.keys = self.key_labels(overlays)
        self.title_key = None
        if item.get("title"):
            html = title_html(item)
            self.title_key = overlays.add(f"title-{key_hash(html)}", html, 1700, 90)
        self.badge_keys = {}
        for a, b, x, badge in pieces:
            if x != 1.0 and badge:
                label = badge if isinstance(badge, str) else f"{x:g}× speed"
                html = f'<div class="badge">{esc(label)}</div>'
                self.badge_keys[(a, b)] = overlays.add(f"badge-{key_hash(html)}", html, 600, 80)
        self.label_keys = []
        for lab in item.get("labels", []):
            html = f'<div class="badge">{esc(lab["text"])}</div>'
            self.label_keys.append((t.time(lab["from"]), t.time(lab["to"]), lab.get("at", "top-right"),
                                    overlays.add(f"label-{key_hash(html)}", html, 900, 80)))

    def key_labels(self, overlays):
        """Key presses worth a label (combinations and special keys), merged when repeated."""
        out = []
        hidden = set(self.item.get("hide_keys", []))
        for e in self.events:
            if e["k"] != "press" or e["key"] in hidden:
                continue
            key = e["key"]
            names = key_label(key)
            special = len(names) > 1 or (names and len(names[0]) > 1) or key.startswith("Arrow")
            if not special:
                continue
            if out and out[-1]["key"] == key and e["t"] - out[-1]["last"] < 1.0:
                out[-1]["count"] += 1
                out[-1]["last"] = e["t"]
                out[-1]["steps"].append(e["t"])
                continue
            out.append({"key": key, "names": names, "t": e["t"], "last": e["t"], "count": 1, "steps": [e["t"]]})
        for lab in out:
            lab["overlays"] = []
            for n in range(1, lab["count"] + 1):
                html = keys_html(lab["names"], n, mac_label(lab["key"]))
                lab["overlays"].append(overlays.add(f"keys-{key_hash(html)}", html, 900, 170))
        return out

    def source_time(self, tau):
        """Take time for output time tau (seconds from the segment start)."""
        acc = 0.0
        for a, b, x, _ in self.pieces:
            span = (b - a) / x
            if tau <= acc + span:
                return a + (tau - acc) * x
            acc += span
        return self.t_to

    def target(self, s):
        """Camera target and spotlight for take time s."""
        current = None
        for m in self.focus:
            if m["t"] <= s:
                current = m
            else:
                break
        if not current or not current.get("box"):
            return REST, None
        box_s = stage_box(self.take, current.get("ubox") or current["box"], current.get("pad", 12))
        cam = camera_for(box_s, min(current.get("zoom", 1.8), self.item.get("zoom_cap", ZOOM_CAP)))
        spot_s = stage_box(self.take, current["box"], current.get("pad", 12))
        spot = spot_s if current.get("spot") and s < current.get("spot_until", 1e9) else None
        return cam, spot

    def camera_track(self):
        """Per output frame: (cx, cy, k, spot box, spot alpha)."""
        dt = 1.0 / self.fps
        s0 = self.source_time(0.0)
        cam0, spot0 = self.target(s0)
        if self.item.get("start_rest"):
            cam0 = REST
        x = np.array([cam0[0], cam0[1], math.log(cam0[2])])
        v = np.zeros(3)
        spot_a = 1.0 if spot0 else 0.0
        spot_box = spot0
        track = []
        for i in range(self.frames):
            s = self.source_time(i * dt)
            cam, spot = self.target(s)
            g = np.array([cam[0], cam[1], math.log(cam[2])])
            a = OMEGA * OMEGA * (g - x) - 2 * OMEGA * v
            v = v + a * dt
            x = x + v * dt
            if spot:
                spot_box = spot
                spot_a = min(1.0, spot_a + dt / 0.35)
            else:
                spot_a = max(0.0, spot_a - dt / SPOT_FADE)
            track.append((x[0], x[1], math.exp(x[2]), spot_box, spot_a))
        return track

    def pointer(self, s):
        """Pointer position (CSS px) at take time s, and its opacity."""
        if not self.moves:
            return None, 0.0
        i = int(np.searchsorted(self.move_t, s, side="right")) - 1
        if i < 0:
            return None, 0.0
        e = self.moves[i]
        if i + 1 < len(self.moves):
            n = self.moves[i + 1]
            if n["t"] - e["t"] < 0.12 and n["t"] > e["t"]:
                u = (s - e["t"]) / (n["t"] - e["t"])
                pos = (e["x"] + (n["x"] - e["x"]) * u, e["y"] + (n["y"] - e["y"]) * u)
            else:
                pos = (e["x"], e["y"])
        else:
            pos = (e["x"], e["y"])
        # Visible around mouse activity; hidden while only the keyboard works.
        last = max([ev["t"] for ev in self.events if ev["k"] in ("move", "down", "up") and ev["t"] <= s] or [-1e9])
        nxt = min([ev["t"] for ev in self.events if ev["k"] in ("move", "down", "up") and ev["t"] > s] or [1e9])
        idle = s - last
        alpha = 1.0
        hide_after = self.item.get("cursor_idle", 1.6)
        if idle > hide_after:
            alpha = max(0.0, 1 - (idle - hide_after) / 0.3)
        if nxt - s < 0.3:
            alpha = max(alpha, 1 - (nxt - s) / 0.3)
        if self.item.get("cursor") is False:
            alpha = 0.0
        return pos, alpha


# ---------------------------------------------------------------- the compositor


class Compositor:
    def __init__(self, overlays, background):
        self.overlays = overlays
        self.background = background
        self.bg_array = np.asarray(background.convert("RGB"))
        self.shadow, self.shadow_margin = make_shadow()
        self.cursor = overlays.get("cursor")
        self.hotspot = (2 * 8, 2 * 8)  # the tip, at (2, 2) of the 24 x 24 box drawn at 8x
        self.cursor_h = 24 * 8
        self._cursor_cache = {}

    def cursor_at(self, height):
        key = int(round(height * 2))
        if key not in self._cursor_cache:
            scale = height / self.cursor_h
            size = (max(1, int(self.cursor.width * scale)), max(1, int(self.cursor.height * scale)))
            self._cursor_cache[key] = (self.cursor.resize(size, Image.LANCZOS), (self.hotspot[0] * scale, self.hotspot[1] * scale))
        return self._cursor_cache[key]

    def take_frame(self, seg, src, cam, s, tau, quality):
        cx, cy, k, spot_box, spot_a = cam
        take = seg.take
        frame = Image.fromarray(self.bg_array.copy())
        # The window on the stage after the camera.
        wx = k * (R0[0] - cx) + W / 2
        wy = k * (R0[1] - cy) + H / 2
        ww, wh = k * R0[2], k * R0[3]
        covers = wx <= 0 and wy <= 0 and wx + ww >= W and wy + wh >= H
        if not covers:
            sw, sh = self.shadow.size
            m = self.shadow_margin
            box = (int(round(wx - m * k)), int(round(wy - m * k)), int(round(sw * k)), int(round(sh * k)))
            sh_im = self.shadow if abs(k - 1) < 1e-3 else self.shadow.resize((box[2], box[3]), Image.BILINEAR)
            frame.paste(sh_im, (box[0], box[1]), sh_im)
        # The visible part of the window, in whole output pixels.
        ox0, oy0 = max(0, math.floor(wx)), max(0, math.floor(wy))
        ox1, oy1 = min(W, math.ceil(wx + ww)), min(H, math.ceil(wy + wh))
        if ox1 > ox0 and oy1 > oy0:
            sx = take.src_w / ww
            sy = take.src_h / wh
            box = ((ox0 - wx) * sx, (oy0 - wy) * sy, (ox1 - wx) * sx, (oy1 - wy) * sy)
            box = (max(0.0, box[0]), max(0.0, box[1]), min(take.src_w, box[2]), min(take.src_h, box[3]))
            img = Image.fromarray(src)
            resample = Image.LANCZOS if quality == "final" else Image.BILINEAR
            part = img.resize((ox1 - ox0, oy1 - oy0), resample, box=box, reducing_gap=None if quality == "final" else 2.0)
            if not covers:
                mask = Image.new("L", part.size, 255)
                r = 2 * (R0[2] / take.css_w) * k
                c = corners(r)
                ri = c["tl"].width
                # Corners that are inside the frame.
                if wx >= -1 and wy >= -1:
                    mask.paste(c["tl"], (0, 0))
                if wx + ww <= W + 1 and wy >= -1:
                    mask.paste(c["tr"], (part.width - ri, 0))
                if wx >= -1 and wy + wh <= H + 1:
                    mask.paste(c["bl"], (0, part.height - ri))
                if wx + ww <= W + 1 and wy + wh <= H + 1:
                    mask.paste(c["br"], (part.width - ri, part.height - ri))
                frame.paste(part, (ox0, oy0), mask)
            else:
                frame.paste(part, (ox0, oy0))
        # Spotlight: a light veil around the focus box and a focus outline in JupyterLab's brand blue.
        if spot_box and spot_a > 0.01:
            bx, by, bw, bh = spot_box
            fx0 = k * (bx - cx) + W / 2
            fy0 = k * (by - cy) + H / 2
            fx1, fy1 = fx0 + bw * k, fy0 + bh * k
            mask = Image.new("L", (W, H), int(255 * 0.16 * spot_a))
            ImageDraw.Draw(mask).rectangle((fx0, fy0, fx1, fy1), fill=0)
            frame = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), frame, mask)
            # The veil alone marks the element; a shot can ask for an outline too with "outline": True.
            if seg.item.get("outline", False):
                ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(ring).rounded_rectangle((fx0 - 2, fy0 - 2, fx1 + 2, fy1 + 2), radius=3,
                                                       outline=(*BRAND_RGB, int(255 * spot_a)), width=3)
                frame.paste(ring, (0, 0), ring)
        # The pointer and its click ripples.
        pos, alpha = seg.pointer(s)
        if pos and alpha > 0.01:
            px = k * (R0[0] + pos[0] * R0[2] / take.css_w - cx) + W / 2
            py = k * (R0[1] + pos[1] * R0[3] / take.css_h - cy) + H / 2
            for down in seg.downs:
                u = (s - down["t"]) / 0.5
                if 0 <= u <= 1:
                    rad = (8 + 26 * ease_out_cubic(u)) * k
                    a = int(200 * (1 - u))
                    ring = Image.new("RGBA", (int(2 * rad + 8), int(2 * rad + 8)), (0, 0, 0, 0))
                    ImageDraw.Draw(ring).ellipse((4, 4, 4 + 2 * rad, 4 + 2 * rad), outline=(*BRAND_RGB, a), width=max(2, int(3 * k)))
                    frame.paste(ring, (int(px - rad - 4), int(py - rad - 4)), ring)
            pressed = any(d["t"] <= s and not any(u["t"] > d["t"] and u["t"] <= s for u in seg.ups) for d in seg.downs if s - d["t"] < 2)
            height = 24 * 1.15 * (R0[2] / take.css_w) * k * (0.9 if pressed else 1.0)
            sprite, hot = self.cursor_at(height)
            if alpha < 0.99:
                sprite = sprite.copy()
                sprite.putalpha(sprite.getchannel("A").point(lambda v: int(v * alpha)))
            frame.paste(sprite, (int(round(px - hot[0])), int(round(py - hot[1]))), sprite)
        # The key labels, centred above the bottom fifth, where players draw captions.
        for lab in seg.keys:
            end = max(lab["last"] + 1.1, lab["t"] + 1.3)
            if lab["t"] <= s <= end + 0.25:
                n = sum(1 for t in lab["steps"] if t <= s)
                im = self.overlays.get(lab["overlays"][max(0, n - 1)])
                a = 1.0 if s <= end else 1 - (s - end) / 0.25
                a *= ease_out_cubic((s - lab["t"]) / 0.12)
                # "keys_x" moves the block off content that looks like key caps, such as the shortcuts table.
                kx = seg.item.get("keys_x", 0.5)
                self.paste(frame, im, (int(W * kx - im.width / 2), H - im.height - KEYS_BOTTOM), a)
        # The title band covers what a zoomed window shows above the window's place at rest.
        if wy < BAND:
            frame.paste(STAGE_RGB, (0, 0, W, BAND))
        if seg.title_key:
            im = self.overlays.get(seg.title_key)
            a = ease_out_cubic((tau - 0.05) / 0.4)
            self.paste(frame, im, TITLE_AT, a)
        # Badges of sped up spans and labels.
        for (a0, b0), key in seg.badge_keys.items():
            if a0 <= s <= b0:
                im = self.overlays.get(key)
                fade = min(1.0, (s - a0) / 0.2, (b0 - s) / 0.2)
                self.paste(frame, im, (int(R0[0] + R0[2] - im.width), 38), fade)
        for a0, b0, where, key in seg.label_keys:
            if a0 <= s <= b0:
                im = self.overlays.get(key)
                fade = min(1.0, (s - a0) / 0.2, (b0 - s) / 0.2)
                pos = (int(R0[0] + R0[2] - im.width), 40) if where == "top-right" else (int((W - im.width) / 2), H - im.height - 40)
                self.paste(frame, im, pos, fade)
        return frame

    @staticmethod
    def paste(frame, im, pos, alpha=1.0):
        if alpha <= 0.01:
            return
        if alpha < 0.99:
            im = im.copy()
            im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
        frame.paste(im, pos, im)


# ---------------------------------------------------------------- cards


WORDMARK = (HERE / "jupyterlab-wordmark.svg").read_text()


def wordmark(width):
    return WORDMARK.replace('width="200"', f'width="{width}"', 1)


def card_html(item):
    kind = item["card"]
    if kind == "title":
        return ('<div class="stage"></div><div class="card"><div class="lockup">' + wordmark(760) +
                '<div class="ver">4.7</div></div>'
                f'<div class="line">{esc(item.get("line", ""))}</div></div>')
    if kind == "html":
        return '<div class="stage"></div>' + item["html"].replace("WORDMARK", wordmark(560))
    raise ValueError(kind)


class Card:
    def __init__(self, item, overlays, fps):
        self.item = item
        self.length = float(item["length"])
        self.frames = int(round(self.length * fps))
        self.key = overlays.add(f"card-{key_hash(json.dumps(item, sort_keys=True))}", card_html(item), W, H)

    def frame(self, overlays, tau, background):
        im = overlays.images[self.key]
        frame = background.copy()
        content = im
        a = ease_out_cubic(tau / 0.5)
        exit_at = self.item.get("fade_out")
        if exit_at:
            a *= 1 - ease_in_out((tau - (self.length - exit_at)) / exit_at) if tau > self.length - exit_at else 1
        Compositor.paste(frame, content, ((W - content.width) // 2, (H - content.height) // 2), a)
        return frame



def title_html(item):
    html = '<div class="title">'
    if item.get("kicker"):
        html += f'<div class="kicker">{esc(item["kicker"])}</div>'
    html += f'<div class="headline">{esc(item["title"])}</div>'
    return html + "</div>"


def segment_jobs(self, ctx):
    comp, fps, quality = ctx["comp"], ctx["fps"], ctx["quality"]
    track = self.camera_track()
    first = int(math.floor(self.source_time(0.0) * self.take.fps + 1e-6))
    reader = Reader(self.take, first)
    try:
        for i in range(self.frames):
            tau = i / fps
            s = self.source_time(min(tau, self.length - self.item.get("hold_end", 0.0)))
            src = reader.get(int(math.floor(s * self.take.fps + 1e-6)))
            yield comp.take_frame, (self, src, track[i], s, tau, quality)
    finally:
        reader.close()


def segment_still(self, i, ctx):
    track = self.camera_track()
    s = self.source_time(i / ctx["fps"])
    idx = int(math.floor(s * self.take.fps + 1e-6))
    reader = Reader(self.take, idx)
    src = reader.get(idx)
    reader.close()
    return ctx["comp"].take_frame(self, src, track[i], s, i / ctx["fps"], ctx["quality"])


Segment.jobs = segment_jobs
Segment.still = segment_still


def card_jobs(self, ctx):
    for i in range(self.frames):
        yield self.frame, (ctx["overlays"], i / ctx["fps"], ctx["background"])


def card_still(self, i, ctx):
    return self.frame(ctx["overlays"], i / ctx["fps"], ctx["background"])


Card.jobs = card_jobs
Card.still = card_still


def perspective_coeffs(dst, src):
    """Coefficients for Image.transform(PERSPECTIVE) that map the four dst corners onto the four src corners."""
    rows, rhs = [], []
    for (x, y), (u, v) in zip(dst, src):
        rows.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        rows.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        rhs += [u, v]
    return np.linalg.solve(np.array(rows, float), np.array(rhs, float)).tolist()


def tilted_quad(x0, y0, w, h, deg=-7.0, dist=3200.0, origin=(1152.0, 540.0)):
    """Corners of a w x h window at (x0, y0) turned about its left edge, as the deck's title slide draws it."""
    th = math.radians(deg)
    out = []
    for u, v in ((0, 0), (w, 0), (w, h), (0, h)):
        x, y, z = x0 + u * math.cos(th), y0 + v, -u * math.sin(th)
        k = dist / (dist - z)
        out.append((origin[0] + (x - origin[0]) * k, origin[1] + (y - origin[1]) * k))
    return out


def key_hash(text):
    """A short hash that stays the same between runs, unlike hash(): the overlay cache is keyed by it."""
    return int(hashlib.sha1(text.encode()).hexdigest()[:12], 16) % 10**10


def lerp(a, b, t):
    return a + (b - a) * t


class Race:
    """Two takes side by side, started together at a beat, each with a timer."""

    def __init__(self, item, overlays, fps):
        self.item = item
        self.fps = fps
        self.pre = item.get("pre", 0.8)
        self.post = item.get("post", 1.8)
        # An opening card: the app beside a title, then the app moves into place, the other one slides in,
        # and a pointer in each window clicks Run at the start.
        self.intro = item.get("intro")
        if self.intro:
            self.pre = self.intro["hold"] + self.intro["move"] + self.intro["point"]
            self.intro_key = overlays.add(f"intro-{key_hash(self.intro['html'])}", self.intro["html"], 1000, H)
            self.sprites = {}
            self.quad_masks = {}
        gap, top, margin = 36, item.get("top", 180), 48
        rw = (W - 2 * margin - gap) / 2
        crop = item.get("crop")
        first = Take(item["left"]["take"])
        rh = rw * (crop[3] / crop[2] if crop else first.css_h / first.css_w)
        self.sides = []
        for n, key in enumerate(("left", "right")):
            spec = item[key]
            take = first if n == 0 else Take(spec["take"])
            result = next(m for m in take.marks if m["kind"] == "result")
            side = {
                "take": take,
                "t_run": take.time(item.get("sync", "beat:run")),
                "elapsed": result["finished"] / 1000.0,
                "rect": (margin + n * (rw + gap), top, rw, rh),
                "label": overlays.add(f"race-label-{key_hash(spec['label'])}",
                                      f'<div class="label">{esc(spec["label"])}</div>', 800, 80),
            }
            self.sides.append(side)
        r_end = max(sd["elapsed"] for sd in self.sides) + self.post
        self.pieces = []
        cursor = -self.pre
        for sp in item.get("speed", []):
            a = float(sp["from"])
            slowest = max(sd["elapsed"] for sd in self.sides)
            b = r_end if sp["to"] == "end" else slowest + 0.1 if sp["to"] == "slowest" else float(sp["to"])
            if a > cursor:
                self.pieces.append((cursor, a, 1.0))
            self.pieces.append((a, b, float(sp["x"])))
            cursor = b
        if cursor < r_end:
            self.pieces.append((cursor, r_end, 1.0))
        self.length = sum((b - a) / x for a, b, x in self.pieces)
        self.frames = int(round(self.length * fps))
        self.speed_keys = {}
        for a, b, x in self.pieces:
            label = "Real time" if x == 1.0 else f"{x:g}× speed"
            html = f'<div class="badge">{esc(label)}</div>'
            self.speed_keys[(a, b)] = overlays.add(f"badge-{key_hash(html)}", html, 600, 80)
        self.title_key = overlays.add(f"title-{key_hash(title_html(item))}", title_html(item), 1700, 90) if item.get("title") else None
        self.badge_key = None
        if item.get("badge"):
            html = f'<div class="badge">{esc(item["badge"])}</div>'
            self.badge_key = overlays.add(f"badge-{key_hash(html)}", html, 600, 80)
        self.note_key = None
        if item.get("note"):
            html = f'<div class="note">{esc(item["note"])}</div>'
            self.note_key = overlays.add(f"note-{key_hash(html)}", html, 1800, 60)
        self.font = ImageFont.truetype(FONT_REGULAR, 62)
        self.small_font = ImageFont.truetype(FONT_REGULAR, 24)
        self.result_font = ImageFont.truetype(FONT_REGULAR, 44)
        end = f'<div class="badge">{esc(item.get("end_badge", "Timers show elapsed time"))}</div>'
        self.end_badge = overlays.add(f"badge-{key_hash(end)}", end, 700, 80)
        self.check_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 56)
        self.crop = item.get("crop")
        self.shadows = {}

    def window(self, frame, src, rect, take):
        x, y, w, h = rect
        ix, iy, iw, ih = int(round(x)), int(round(y)), int(round(w)), int(round(h))
        if (iw, ih) not in self.shadows:
            m = 50
            small = Image.new("L", ((iw + 2 * m) // 4, (ih + 2 * m) // 4), 0)
            ImageDraw.Draw(small).rectangle((m // 4, (m + 5) // 4, (m + iw) // 4, (m + 5 + ih) // 4), fill=95)
            small = small.filter(ImageFilter.GaussianBlur(4)).resize((iw + 2 * m, ih + 2 * m), Image.BILINEAR)
            sh = Image.new("RGBA", small.size, (0, 0, 0, 0))
            sh.putalpha(small)
            mask = Image.new("L", (iw, ih), 255)
            c = corners(3)
            r = c["tl"].width
            mask.paste(c["tl"], (0, 0))
            mask.paste(c["tr"], (iw - r, 0))
            mask.paste(c["bl"], (0, ih - r))
            mask.paste(c["br"], (iw - r, ih - r))
            self.shadows[(iw, ih)] = (sh, m, mask)
        sh, m, mask = self.shadows[(iw, ih)]
        frame.paste(sh, (ix - m, iy - m), sh)
        img = Image.fromarray(src)
        if self.crop:
            k = take.dsf
            cx, cy, cw, ch = self.crop
            part = img.resize((iw, ih), Image.LANCZOS, box=(cx * k, cy * k, (cx + cw) * k, (cy + ch) * k))
        else:
            part = img.resize((iw, ih), Image.LANCZOS)
        frame.paste(part, (ix, iy), mask)

    def quad_window(self, frame, src, quad, lift):
        xs, ys = [q[0] for q in quad], [q[1] for q in quad]
        bx0, by0 = int(math.floor(min(xs))), int(math.floor(min(ys)))
        bw, bh = int(math.ceil(max(xs))) - bx0, int(math.ceil(max(ys))) - by0
        dst = [(x - bx0, y - by0) for x, y in quad]
        # Shadow: lift 1 is the deck's raised window, lift 0 the window of the race.
        m, off = 120, lerp(5, 40, lift)
        small = Image.new("L", ((bw + 2 * m) // 4, (bh + 2 * m) // 4), 0)
        ImageDraw.Draw(small).polygon([((x + m) / 4, (y + m + off) / 4) for x, y in dst], fill=int(lerp(95, 80, lift)))
        small = small.filter(ImageFilter.GaussianBlur(lerp(4, 14, lift))).resize((bw + 2 * m, bh + 2 * m), Image.BILINEAR)
        shadow = Image.new("RGBA", small.size, (0, 0, 0, 0))
        shadow.putalpha(small)
        frame.paste(shadow, (bx0 - m, by0 - m), shadow)
        # Scale first, then warp: the perspective warp samples without averaging.
        img = Image.fromarray(src)
        sw, sh = max(2, int(bw)), max(2, int(bh))
        # The edge pixels repeat outward, so that the warp does not blend the border of the window with black.
        pad = 4
        arr = np.pad(np.asarray(img.resize((sw, sh), Image.LANCZOS)), ((pad, pad), (pad, pad), (0, 0)), mode="edge")
        inner = [(pad, pad), (sw + pad, pad), (sw + pad, sh + pad), (pad, sh + pad)]
        warped = Image.fromarray(arr).transform((bw, bh), Image.PERSPECTIVE, perspective_coeffs(dst, inner), Image.BICUBIC)
        frame.paste(warped, (bx0, by0), self.quad_mask(dst, (bw, bh), (sw, sh), pad, inner))

    def quad_mask(self, dst, size, src_size, pad, inner):
        """The rounded corners of the flat window, warped at 4x and scaled down, so that the edges are smooth."""
        key = (tuple((round(x, 2), round(y, 2)) for x, y in dst), size)
        if key not in self.quad_masks:
            (bw, bh), (sw, sh), s = size, src_size, 4
            rounded = Image.new("L", ((sw + 2 * pad) * s, (sh + 2 * pad) * s), 0)
            ImageDraw.Draw(rounded).rounded_rectangle((pad * s, pad * s, (sw + pad) * s - 1, (sh + pad) * s - 1), radius=3 * s, fill=255)
            coeffs = perspective_coeffs([(x * s, y * s) for x, y in dst], [(u * s, v * s) for u, v in inner])
            mask = rounded.transform((bw * s, bh * s), Image.PERSPECTIVE, coeffs, Image.BILINEAR).resize((bw, bh), Image.LANCZOS)
            if len(self.quad_masks) > 4:
                self.quad_masks.clear()
            self.quad_masks[key] = mask
        return self.quad_masks[key]

    def sprite(self, overlays, size):
        size = max(8, int(round(size)))
        if size not in self.sprites:
            self.sprites[size] = overlays.get("cursor").resize((size, size), Image.LANCZOS)
        return self.sprites[size]

    def intro_state(self, tau):
        """Progress of the move (0 to 1), and the opacity of the race labels."""
        if not self.intro:
            return 1.0, 1.0
        hold, move = self.intro["hold"], self.intro["move"]
        p = min(1.0, max(0.0, (tau - hold) / move))
        ui = min(1.0, max(0.0, (tau - hold - 0.55 * move) / 0.45))
        return p, ui

    def draw_intro(self, frame, srcs, tau, overlays, p):
        left, right = self.sides
        # The text of the card fades in, then moves out to the left as the windows move.
        im = overlays.get(self.intro_key)
        out = ease_in_out((tau - self.intro["hold"] + 0.3) / 0.55)
        a = ease_out_cubic((tau - 0.15) / 0.6) * (1 - out)
        Compositor.paste(frame, im, (int(-60 * out), 0), a)
        # The JupyterLab 4.6 window slides in from the left edge.
        x, y, w, h = left["rect"]
        lx = lerp(-w - 80, x, ease_out_cubic(p))
        if lx + w > 0:
            self.window(frame, srcs[0], (lx, y, w, h), left["take"])
        # The JupyterLab 4.7 window turns flat as it moves from the card into the race.
        x, y, w, h = right["rect"]
        card = self.intro.get("card", [872, 262, 941])
        start = tilted_quad(card[0], card[1], card[2], card[2] * h / w)
        end = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        e = ease_in_out(p)
        if e >= 1.0:
            self.window(frame, srcs[1], right["rect"], right["take"])
        else:
            self.quad_window(frame, srcs[1], [(lerp(a[0], b[0], e), lerp(a[1], b[1], e)) for a, b in zip(start, end)], 1 - e)

    def draw_pointers(self, frame, tau, overlays):
        """A pointer in each window moves to Run and clicks it as the race starts."""
        r = self.race_time(tau)
        point = self.intro["point"]
        if r < -point or r > 1.0:
            return
        x0, y0 = self.intro.get("pointer_from", [430, 330])
        x1, y1 = self.intro["click"]
        # The pointer shows 0.3 s before it moves, and reaches Run 0.15 s before the click.
        move = min(0.8, point - 0.45)
        u = ease_in_out(min(1.0, max(0.0, (r + 0.15 + move) / move)))
        alpha = ease_out_cubic((r + 0.15 + move + 0.3) / 0.2) * (1 - min(1.0, max(0.0, (r - 0.6) / 0.3)))
        for side in self.sides:
            x, y, w, h = side["rect"]
            take = side["take"]
            sx, sy = w / take.css_w, h / take.css_h
            px, py = x + lerp(x0, x1, u) * sx, y + lerp(y0, y1, u) * sy
            if 0 <= r <= 0.5:
                q = r / 0.5
                rad = 6 + 26 * ease_out_cubic(q)
                ring = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
                ImageDraw.Draw(ring).ellipse((40 - rad, 40 - rad, 40 + rad, 40 + rad), outline=(*BRAND_RGB, int(220 * (1 - q))), width=3)
                frame.paste(ring, (int(px - 40), int(py - 40)), ring)
            size = 24 * 1.15 * sx * (0.9 if 0 <= r < 0.12 else 1.0)
            sprite = self.sprite(overlays, size)
            hot = 2 * size / 24
            Compositor.paste(frame, sprite, (int(round(px - hot)), int(round(py - hot))), alpha)

    def frame_at(self, srcs, tau, overlays, background):
        frame = background.copy()
        p, ui = self.intro_state(tau)
        if self.intro and p < 1.0:
            self.draw_intro(frame, srcs, tau, overlays, p)
        for side, src in zip(self.sides, srcs):
            x, y, w, h = side["rect"]
            if not (self.intro and p < 1.0):
                self.window(frame, src, side["rect"], side["take"])
            lab = overlays.get(side["label"])
            Compositor.paste(frame, lab, (int(x), int(y - lab.height - 16)), ui)
            if ui <= 0.01:
                continue
            elapsed = max(0.0, self.race_time(tau))
            done = elapsed >= side["elapsed"]
            value = min(elapsed, side["elapsed"])
            # Two decimals, so the ratio below can be checked from the two timers.
            text = f"{value:.2f} s"
            d = ImageDraw.Draw(frame)
            fastest = min(sd["elapsed"] for sd in self.sides)
            winner = side["elapsed"] == fastest
            colour = (BRAND_RGB if winner else (117, 117, 117)) if done else (33, 33, 33)
            colour = tuple(int(c * ui + bg * (1 - ui)) for c, bg in zip(colour, STAGE_RGB))
            tw = d.textlength(text, font=self.font)
            ty = int(y + h + 22)
            d.text((x + w / 2 - tw / 2, ty), text, font=self.font, fill=colour)
            if done and winner:
                d.text((x + w / 2 + tw / 2 + 16, ty + 6), "\u2713", font=self.check_font, fill=colour)
            speed = self.speed_at(self.race_time(tau))
            if not done and speed != 1.0:
                label = f"shown at {speed:g}× speed"
                lw = d.textlength(label, font=self.small_font)
                d.text((x + w / 2 - lw / 2, ty + 84), label, font=self.small_font, fill=(117, 117, 117))
        if self.title_key:
            im = overlays.get(self.title_key)
            a = ease_out_cubic((tau - 0.05) / 0.45) if not self.intro else ui
            Compositor.paste(frame, im, (48, TITLE_AT[1]), a)
        if self.intro:
            self.draw_pointers(frame, tau, overlays)
        r = self.race_time(tau)
        slowest = max(sd["elapsed"] for sd in self.sides)
        fastest = min(sd["elapsed"] for sd in self.sides)
        if r >= slowest:
            im = overlays.get(self.end_badge)
            Compositor.paste(frame, im, (W - 48 - im.width, 38))
            label = self.item.get("result", "{ratio:.1f}× faster in this run").format(ratio=round(slowest, 2) / round(fastest, 2))
            a = ease_out_cubic((r - slowest) / 0.4)
            d = ImageDraw.Draw(frame)
            lw = d.textlength(label, font=self.result_font)
            ly = int(self.sides[0]["rect"][1] + self.sides[0]["rect"][3] + 108)
            colour = tuple(int(c * a + bg * (1 - a)) for c, bg in zip((33, 33, 33), STAGE_RGB))
            d.text(((W - lw) / 2, ly), label, font=self.result_font, fill=colour)
        else:
            for (a, b), key in self.speed_keys.items():
                if a <= r <= b:
                    im = overlays.get(key)
                    Compositor.paste(frame, im, (W - 48 - im.width, 38), ui)
                    break
        if self.note_key:
            im = overlays.get(self.note_key)
            Compositor.paste(frame, im, ((W - im.width) // 2, H - im.height - 22), ui)
        return frame

    def speed_at(self, r):
        for a, b, x in self.pieces:
            if a <= r < b:
                return x
        return 1.0

    def race_time(self, tau):
        """Seconds after the run starts, for output time tau."""
        acc = 0.0
        for a, b, x in self.pieces:
            span = (b - a) / x
            if tau <= acc + span:
                return a + (tau - acc) * x
            acc += span
        return self.pieces[-1][1]

    def source_times(self, tau):
        r = self.race_time(tau)
        out = []
        for side in self.sides:
            s = side["t_run"] + r
            # Hold the last frame before the end flash, which marks the corner.
            limit = side["take"].time("flash:end") - 0.15
            first = side["take"].time("flash:start") + 0.5
            out.append(min(max(first, s), limit))
        return out

    def jobs(self, ctx):
        fps = ctx["fps"]
        readers = []
        for side, s in zip(self.sides, self.source_times(0.0)):
            readers.append(Reader(side["take"], int(math.floor(s * side["take"].fps + 1e-6))))
        try:
            for i in range(self.frames):
                tau = i / fps
                srcs = [r.get(int(math.floor(s * side["take"].fps + 1e-6))) for r, side, s in zip(readers, self.sides, self.source_times(tau))]
                yield self.frame_at, (srcs, tau, ctx["overlays"], ctx["background"])
        finally:
            for r in readers:
                r.close()

    def still(self, i, ctx):
        tau = i / ctx["fps"]
        srcs = []
        for side, s in zip(self.sides, self.source_times(tau)):
            idx = int(math.floor(s * side["take"].fps + 1e-6))
            r = Reader(side["take"], idx)
            srcs.append(r.get(idx))
            r.close()
        return self.frame_at(srcs, tau, ctx["overlays"], ctx["background"])



def output_time(seg, s):
    """Output time within a segment for take time s, or None outside it."""
    acc = 0.0
    for a, b, x, _ in seg.pieces:
        if a <= s <= b:
            return acc + (s - a) / x
        acc += (b - a) / x
    return None


def extend(part, seconds, fps):
    """Make a part longer by holding its end."""
    if isinstance(part, Segment):
        part.item["hold_end"] = part.item.get("hold_end", 0.0) + seconds
    elif isinstance(part, Race):
        part.post += seconds
    else:
        part.item["length"] = part.length + seconds
    part.length += seconds
    part.frames = int(round(part.length * fps))


def snap_to_beats(parts, bpm, fps):
    """End every part but the last on a beat of the music: a cut lands on the beat."""
    beat = 60.0 / bpm
    t = 0.0
    for p in parts[:-1]:
        end = t + p.frames / fps
        snapped = math.ceil(end / beat - 1e-6) * beat
        if snapped - end > 1e-6:
            extend(p, snapped - end, fps)
        t += p.frames / fps


def click_sound():
    n = int(0.012 * 48000)
    t = np.arange(n) / 48000
    rng = np.random.default_rng(3)
    tone = np.sin(2 * np.pi * 2600 * t) * np.exp(-t * 900)
    noise = rng.standard_normal(n) * np.exp(-t * 1500) * 0.4
    return (tone + noise) * 0.16



def read_wav(path):
    """A WAV file as float32 samples (frames x channels) and its rate."""
    import wave
    with wave.open(str(path)) as w:
        rate, ch, width = w.getframerate(), w.getnchannels(), w.getsampwidth()
        data = np.frombuffer(w.readframes(w.getnframes()), "<i2" if width == 2 else "<i4").astype(np.float32)
        data /= 32768.0 if width == 2 else 2147483648.0
    return data.reshape(-1, ch), rate


def to_rate(audio, rate, target=48000):
    from math import gcd
    from scipy.signal import resample_poly
    if rate == target:
        return audio
    g = gcd(rate, target)
    return resample_poly(audio, target // g, rate // g, axis=0).astype(np.float32)


CAPTION_WIDTH = 42  # characters per caption line, as in common subtitle guidelines


SMALL_WORDS = {"a", "an", "the", "of", "to", "in", "on", "at", "and", "or", "with", "for", "as", "its", "your"}
BREAK_BEFORE = {"and", "or", "but", "so", "while", "when", "where", "as", "of", "in", "on", "at", "for",
                "with", "from", "that", "unless", "if", "under", "into"}
KEEP_TOGETHER = {("arrow", "keys"), ("CSV", "file")}


def break_cost(left, right, cue=False):
    """Cost of a caption line break, or of a cue break with cue=True, between `left` and `right`."""
    cost = abs(len(left) - len(right)) * (0.3 if cue else 0.6)
    last, first = left.split()[-1], right.split()[0]
    if left[-1] in ".?!:;":
        cost -= 40 if cue else 25
    elif left[-1] == ",":
        cost -= 25 if cue else 15
    if last.lower() in SMALL_WORDS:
        cost += 30
    if first.lower() in BREAK_BEFORE:
        cost -= 6
    # Names such as "Settings Editor", and a few word pairs, stay on one line.
    if last[:1].isupper() and first[:1].isupper():
        cost += 20
    if (last.strip(",.:;?!"), first) in KEEP_TOGETHER:
        cost += 20
    return cost


def caption_lines(text):
    """The text as one caption line, or as two lines with a good break; None when there is none."""
    if len(text) <= CAPTION_WIDTH:
        return [text]
    words = text.split()
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        if max(len(a), len(b)) <= CAPTION_WIDTH and (best is None or break_cost(a, b) < best[0]):
            best = (break_cost(a, b), [a, b])
    return best[1] if best and best[0] < 25 else None


def caption_parts(text):
    """Split a narration line into cues of at most two caption lines."""
    if caption_lines(text):
        return [text]
    words = text.split()
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        cost = break_cost(a, b, cue=True) + (0 if caption_lines(a) else 100) + (0 if caption_lines(b) else 100)
        if best is None or cost < best[0]:
            best = (cost, i)
    i = best[1]
    return caption_parts(" ".join(words[:i])) + caption_parts(" ".join(words[i:]))


def part_time(part, ref, default):
    """Seconds from the start of a part for a line's "at": a take time for a segment, "+s" otherwise."""
    if ref is None:
        return default
    if isinstance(ref, str) and ref.startswith("+"):
        return float(ref[1:])
    if isinstance(part, Segment):
        o = output_time(part, part.take.time(ref))
        return default if o is None else o
    return float(ref)


def extend_segment(seg, extra, fps):
    """Make a segment longer: more of the take first, then a held last frame."""
    limit = seg.take.time("flash:end") - 0.2
    use = max(0.0, min(extra, limit - seg.t_to))
    if use > 0:
        a, b, x, badge = seg.pieces[-1]
        if x == 1.0:
            seg.pieces[-1] = (a, b + use, x, badge)
        else:
            seg.pieces.append((b, b + use, 1.0, False))
        seg.t_to += use
        seg.length += use
    if extra - use > 1e-6:
        seg.item["hold_end"] = seg.item.get("hold_end", 0.0) + (extra - use)
        seg.length += extra - use
    seg.frames = int(round(seg.length * fps))


def place_lines(parts, voice_dir, fps):
    """Give each part its narration lines, (id, start s, length s, text), and lengthen parts to fit them."""
    durations = json.loads((voice_dir / "durations.json").read_text())
    for p in parts:
        p.lines = []
        t_free = 0.0
        for line in p.item.get("say", []):
            d = durations[line["id"]]["seconds"]
            # Pauses between lines give the viewer time to take in each one.
            start = part_time(p, line.get("at"), t_free + (0.35 if not p.lines else LINE_GAP))
            start = max(start, t_free + (0.0 if not p.lines else LINE_GAP) + line.get("pause", 0.0))
            p.lines.append((line["id"], start, d, line["text"]))
            t_free = start + d
        need = t_free + p.item.get("tail", 0.8) if p.lines else 0.0
        if need > p.length + 1e-6:
            extra = need - p.length
            if isinstance(p, Segment):
                extend_segment(p, extra, fps)
            else:
                extend(p, extra, fps)

def build_audio(parts, edit, fps, work):
    """The music bed and the clicks, loudness-normalized; returns the WAV path or None."""
    music = edit.get("music")
    if not music:
        return None
    total = sum(p.frames for p in parts) / fps
    starts, t = [], 0.0
    for p in parts:
        starts.append(t)
        t += p.frames / fps
    hit = next((st for st, p in zip(starts, parts) if p.item.get("music_hit")), 8.0)
    outro = next((st for st, p in zip(starts, parts) if p.item.get("music_outro")), total - 8.0)
    raw = work / "music.wav"
    if music == "generate":
        subprocess.run([sys.executable, str(HERE / "music.py"), str(raw), f"{total:.3f}", "--bpm", str(edit.get("bpm", 104)),
                        "--hit", f"{hit:.3f}", "--outro", f"{outro:.3f}"], check=True)
    else:
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", music, "-t", f"{total:.3f}", "-ar", "48000", "-ac", "2", str(raw)], check=True)
    music_audio, rate = read_wav(raw)
    music_audio = to_rate(music_audio, rate)
    if music_audio.shape[1] == 1:
        music_audio = np.repeat(music_audio, 2, axis=1)
    n = int(total * 48000)
    if len(music_audio) < n:
        # Loop a short track with a one-second crossfade.
        fade = 48000
        pieces = [music_audio]
        while sum(len(x) for x in pieces) - fade * (len(pieces) - 1) < n:
            pieces.append(music_audio)
        joined = pieces[0]
        ramp = np.linspace(0, 1, fade, dtype=np.float32)[:, None]
        for x in pieces[1:]:
            joined = np.concatenate([joined[:-fade], joined[-fade:] * (1 - ramp) + x[:fade] * ramp, x[fade:]])
        music_audio = joined
    music_audio = music_audio[:n].copy()
    if music != "generate":
        tail = min(n, int(3.0 * 48000))
        music_audio[-tail:] *= np.linspace(1, 0, tail, dtype=np.float32)[:, None] ** 2
    voice = np.zeros((n, 2), np.float32)
    voice_dir = edit.get("_voice_dir")
    if voice_dir:
        for st, p in zip(starts, parts):
            for line_id, start, d, text in getattr(p, "lines", []):
                clip, r = read_wav(voice_dir / f"{line_id}.wav")
                clip = to_rate(clip, r)
                if clip.shape[1] == 1:
                    clip = np.repeat(clip, 2, axis=1)
                i = int((st + start) * 48000)
                j = min(n, i + len(clip))
                if 0 <= i < j:
                    voice[i:j] += clip[: j - i]
        # Duck the music while the voice speaks: 50 ms windows, a fast attack and a slow release.
        hop = 2400
        frames_n = n // hop + 1
        rms = np.array([np.sqrt(np.mean(voice[k * hop:(k + 1) * hop, 0] ** 2) + 1e-12) for k in range(frames_n)])
        active = (rms > 0.01).astype(np.float32)
        env = np.zeros_like(active)
        level = 0.0
        for k, a in enumerate(active):
            level = level + (a - level) * (0.6 if a > level else 0.1)
            env[k] = level
        gain = np.repeat(1.0 - edit.get("duck", 0.55) * env, hop)[:n].astype(np.float32)
        music_audio *= (edit.get("music_gain", 0.32) * gain)[:, None]
    audio = music_audio + voice
    if edit.get("clicks", True):
        click = click_sound() * edit.get("click_gain", 0.6)
        for st, p in zip(starts, parts):
            if not isinstance(p, Segment):
                continue
            for e in p.downs:
                o = output_time(p, e["t"])
                if o is None:
                    continue
                i = int((st + o) * 48000)
                j = min(len(audio), i + len(click))
                if 0 <= i < j:
                    audio[i:j, 0] += click[: j - i]
                    audio[i:j, 1] += click[: j - i]
    mix = work / "mix.wav"
    with wave.open(str(mix), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(48000)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
    # Two-pass loudness normalization to -14 LUFS, with headroom for the AAC encoder's peaks.
    probe = subprocess.run([FFMPEG, "-hide_banner", "-i", str(mix), "-af", "loudnorm=I=-14:TP=-2.6:LRA=11:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
    stats = json.loads(probe[probe.rindex("{"):probe.rindex("}") + 1])
    final = work / "audio.wav"
    filt = (f"loudnorm=I=-14:TP=-2.6:LRA=11:measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
            f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:offset={stats['target_offset']}:linear=true,"
            "alimiter=limit=0.79:level=false:attack=2:release=50")
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", str(mix), "-af", filt, "-ar", "48000", str(final)], check=True)
    return final


# ---------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edit")
    ap.add_argument("out")
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--only", default="")
    ap.add_argument("--stills", default="")
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--no-audio", action="store_true")
    args = ap.parse_args()
    edit = json.loads(Path(args.edit).read_text())
    fps = edit.get("preview_fps", 30) if args.preview else edit.get("fps", 60)
    quality = "preview" if args.preview else "final"
    items = edit["sequence"]
    if args.only:
        keep = {int(i) for i in args.only.split(",")}
        items = [it for i, it in enumerate(items) if i in keep]

    overlays = Overlays()
    overlays.add("stage", '<div class="stage"></div>', W, H)
    overlays.add("cursor", cursor_html(24 * 8), 24 * 8, 24 * 8)
    parts = []
    for it in items:
        if "take" in it:
            parts.append(Segment(it, overlays, fps))
        elif "left" in it:
            parts.append(Race(it, overlays, fps))
        else:
            parts.append(Card(it, overlays, fps))
    overlays.render()
    background = overlays.images["stage"].convert("RGB")
    if background.size != (W, H):
        bg = Image.new("RGB", (W, H))
        bg.paste(background, (0, 0))
        background = bg
    comp = Compositor(overlays, background)
    if edit.get("voice"):
        voice_dir = (Path(args.edit).parent / edit["voice"]).resolve()
        edit["_voice_dir"] = voice_dir
        place_lines(parts, voice_dir, fps)
    if edit.get("bpm"):
        snap_to_beats(parts, edit["bpm"], fps)
    total = sum(p.frames for p in parts)
    for p in parts:
        if isinstance(p, Segment):
            print(f"{p.take.name}: {p.length:.2f} s, capture delay {p.take.age * 1000:.0f} ms, {len(p.focus)} focus marks")
        elif isinstance(p, Race):
            print("race: " + ", ".join(f"{sd['take'].name} {sd['elapsed']:.2f} s (delay {sd['take'].age * 1000:.0f} ms)" for sd in p.sides))
        else:
            print(f"card {p.item['card']}: {p.length:.2f} s")
    print(f"total {total / fps:.2f} s, {total} frames at {fps} fps")
    plan, t = [], 0.0
    for p in parts:
        it = p.item
        plan.append({"start": round(t, 3), "length": round(p.frames / fps, 3),
                     "what": it.get("take") or ("race" if isinstance(p, Race) else "card " + it.get("card", "")),
                     "kicker": it.get("kicker"), "title": it.get("title"), "sub": it.get("sub"), "chapter": it.get("chapter"),
                     "lines": [{"id": i, "start": round(t + a, 3), "length": d, "text": x} for i, a, d, x in getattr(p, "lines", [])],
                     "keys": [{"key": lab["key"], "at": round(t + output_time(p, lab["t"]), 2)} for lab in getattr(p, "keys", [])
                              if output_time(p, lab["t"]) is not None]})
        t += p.frames / fps
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out + ".plan.json").write_text(json.dumps(plan, indent=1))
    def stamp(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    cues = []
    spoken = [line for row in plan for line in row["lines"]]
    for line in spoken:
        # Each cue shows at most two lines; its time is the share of the line's characters.
        chunks = caption_parts(line["text"])
        total = sum(len(x) for x in chunks)
        start = line["start"]
        for x in chunks:
            end = start + line["length"] * len(x) / total
            cues.append(f"{len(cues) + 1}\n{stamp(start)} --> {stamp(end)}\n" + "\n".join(caption_lines(x)) + "\n")
            start = end
    for row in ([] if spoken else plan):
        text = [x for x in (row.get("title"), row.get("sub")) if x]
        if row["what"] == "card title":
            text = ["JupyterLab 4.7: highlights of the release"]
        if text:
            cues.append(f"{len(cues) + 1}\n{stamp(row['start'] + 0.1)} --> {stamp(row['start'] + row['length'] - 0.05)}\n" + "\n".join(text) + "\n")
    Path(args.out + ".srt").write_text("\n".join(cues))

    if args.stills == "auto":
        # Three frames per part: just in, the middle, just before the end.
        stills, t = [], 0.0
        for p in parts:
            length = p.frames / fps
            stills += [round(t + min(0.7, length / 4), 2), round(t + length * 0.55, 2), round(t + length - 0.35, 2)]
            t += length
    else:
        stills = [float(x) for x in args.stills.split(",") if x.strip()]
    if stills:
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        ctx = {"comp": comp, "overlays": overlays, "background": background, "fps": fps, "quality": quality}
        render_stills(parts, ctx, stills, out_dir)
        return

    work = Path(args.out + ".parts")
    work.mkdir(parents=True, exist_ok=True)
    audio = None if args.no_audio else build_audio(parts, edit, fps, work)
    audio_in = ["-i", str(audio)] if audio else []
    audio_out = ["-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "192k", "-ar", "48000"] if audio else []
    encoder = subprocess.Popen(
        [FFMPEG, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "pipe:0", *audio_in,
         "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p,setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709",
         "-c:v", "libx264", "-preset", "veryfast" if args.preview else "slow", "-crf", "22" if args.preview else "16",
         "-profile:v", "high", "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
         "-color_range", "tv", *audio_out, "-movflags", "+faststart", args.out],
        stdin=subprocess.PIPE, bufsize=1 << 22)
    pool = ThreadPoolExecutor(args.threads)
    pending = deque()
    started = time.time()
    done = 0
    chapters = []
    t_out = 0.0
    ctx = {"comp": comp, "overlays": overlays, "background": background, "fps": fps, "quality": quality}
    for p in parts:
        if p.item.get("chapter"):
            chapters.append((t_out, p.item["chapter"]))
        for func, fargs in p.jobs(ctx):
            pending.append(pool.submit(func, *fargs))
            while len(pending) > args.threads * 3:
                encoder.stdin.write(pending.popleft().result().tobytes())
                done += 1
        t_out += p.frames / fps
        print(f"  queued {p.item.get('take') or p.item.get('card') or 'race'} ({time.time() - started:.0f} s)", flush=True)
    while pending:
        encoder.stdin.write(pending.popleft().result().tobytes())
        done += 1
    encoder.stdin.close()
    encoder.wait()
    elapsed = time.time() - started
    print(f"wrote {args.out}: {done} frames in {elapsed:.0f} s ({done / max(elapsed, 1e-3):.1f} fps)")
    Path(args.out + ".chapters.txt").write_text(
        "".join(f"{int(t // 60)}:{int(t % 60):02d} {name}\n" for t, name in chapters))


def render_stills(parts, ctx, stills, out_dir):
    """Draw the frames at the given output times, as PNGs."""
    fps = ctx["fps"]
    starts = []
    acc = 0
    for p in parts:
        starts.append(acc)
        acc += p.frames
    for t in stills:
        f = int(round(t * fps))
        for p, start in zip(parts, starts):
            if start <= f < start + p.frames:
                im = p.still(f - start, ctx)
                path = out_dir / f"still-{t:07.2f}.png"
                im.save(path)
                print("still", path)
                break


if __name__ == "__main__":
    main()
