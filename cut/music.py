"""A placeholder music bed for the rough cut, synthesized with numpy.

Usage: python music.py <out.wav> <length s> [--bpm 104] [--intro s] [--hit s] [--outro s]

It is a stand-in so that the cut can be timed to a beat grid: replace it with
a licensed track of the same tempo before publishing. Sections:
  0 .. intro   pad and a soft pulse (the cold open)
  hit          an impact on the downbeat (the title card)
  hit .. outro the groove: kick, hats, clap, bass, pad and a plucked arpeggio
  outro .. end the groove thins out and the last chord rings out
"""

import argparse
import wave

import numpy as np
from scipy.signal import fftconvolve, lfilter

SR = 48000
RNG = np.random.default_rng(47)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def env(n, a, d, s, r, hold):
    """ADSR envelope of n samples: attack, decay, sustain level, release; hold = samples before release."""
    out = np.zeros(n)
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    t = 0
    seg = min(a, n)
    out[:seg] = np.linspace(0, 1, seg, endpoint=False)
    t = seg
    seg = min(d, max(0, n - t))
    out[t:t + seg] = np.linspace(1, s, seg, endpoint=False)
    t += seg
    seg = max(0, min(hold, n) - t)
    out[t:t + seg] = s
    t += seg
    seg = min(r, max(0, n - t))
    out[t:t + seg] = np.linspace(s, 0, seg, endpoint=False) if seg else []
    return out


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    return lfilter([1 - a], [1, -a], x)


def highpass(x, cutoff):
    return x - lowpass(x, cutoff)


def saw(freq, n, detune=0.0):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for d in (-detune, 0.0, detune):
        f = freq * (1 + d)
        phase = RNG.random()
        out += 2 * ((t * f + phase) % 1.0) - 1
    return out / 3


def add(buf, start, sig):
    start = int(start)
    if start >= len(buf):
        return
    end = min(len(buf), start + len(sig))
    buf[start:end] += sig[: end - start]


def kick(gain=1.0):
    n = int(0.42 * SR)
    t = np.arange(n) / SR
    f = 46 + 95 * np.exp(-t * 32)
    phase = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(phase) * np.exp(-t * 7.5)
    click = RNG.standard_normal(n) * np.exp(-t * 400) * 0.25
    return gain * (body + lowpass(click, 4000))


def hat(gain=1.0, open_=False):
    n = int((0.22 if open_ else 0.06) * SR)
    t = np.arange(n) / SR
    noise = highpass(RNG.standard_normal(n), 7000)
    return gain * noise * np.exp(-t * (14 if open_ else 70))


def clap(gain=1.0):
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    noise = highpass(lowpass(RNG.standard_normal(n), 5000), 900)
    e = np.exp(-t * 22)
    for k in (0.0, 0.011, 0.022):
        e += 0.6 * np.exp(-np.maximum(0, t - k) * 180) * (t >= k)
    return gain * noise * e * 0.5


def pluck(freq, dur, gain=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t) + 0.12 * np.sin(6 * np.pi * freq * t)
    return gain * tone * np.exp(-t * 9) * np.minimum(1, t * 400)


def reverb_ir(seconds=2.2):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    left = RNG.standard_normal(n) * np.exp(-t * 3.2)
    right = RNG.standard_normal(n) * np.exp(-t * 3.2)
    left, right = lowpass(left, 6000), lowpass(right, 6000)
    return left / np.sqrt(np.sum(left ** 2)), right / np.sqrt(np.sum(right ** 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("length", type=float)
    ap.add_argument("--bpm", type=float, default=104)
    ap.add_argument("--intro", type=float, default=8.0)
    ap.add_argument("--hit", type=float, default=None)
    ap.add_argument("--outro", type=float, default=None)
    args = ap.parse_args()
    beat = 60 / args.bpm
    n = int((args.length + 3) * SR)
    hit = args.hit if args.hit is not None else args.intro
    outro = args.outro if args.outro is not None else args.length - 8 * beat
    drums = np.zeros(n)
    bass = np.zeros(n)
    pad_l, pad_r = np.zeros(n), np.zeros(n)
    arp = np.zeros(n)
    fx = np.zeros(n)
    # Am F C G, one bar each.
    chords = [[57, 60, 64], [53, 57, 60], [48, 55, 60], [55, 59, 62]]
    roots = [45, 41, 48, 43]
    bar = 4 * beat
    nbars = int(np.ceil(args.length / bar)) + 1
    for b in range(nbars):
        t_bar = b * bar
        chord = chords[b % 4]
        in_groove = hit <= t_bar < outro
        in_intro = t_bar < hit
        # Pad: every bar, softer in the intro, filtered.
        length = int(bar * SR) + int(0.8 * SR)
        e = env(length, 0.35 if in_intro else 0.08, 0.4, 0.75, 0.8, int(bar * SR))
        for i, note in enumerate(chord + [chord[0] + 12]):
            f = midi(note)
            sig = lowpass(saw(f, length, 0.004), 1100 if in_intro else 1700) * e
            pan = 0.5 + 0.35 * (i - 1.5) / 1.5
            g = 0.055 if in_intro else 0.045
            add(pad_l, t_bar * SR, sig * g * (1 - pan) * 2)
            add(pad_r, t_bar * SR, sig * g * pan * 2)
        # Bass: eighths in the groove, a held root in the intro.
        if in_groove or (t_bar >= outro and t_bar < args.length):
            for k in range(8):
                t = t_bar + k * beat / 2
                if t >= args.length:
                    break
                ln = int(beat / 2 * SR)
                f = midi(roots[b % 4] - 12 + (12 if k in (3, 7) else 0))
                tt = np.arange(ln) / SR
                sig = (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt)) * env(ln, 0.005, 0.08, 0.6, 0.05, ln - int(0.05 * SR))
                add(bass, t * SR, sig * 0.20)
        # Drums.
        for k in range(4):
            t = t_bar + k * beat
            if t >= args.length + 2:
                break
            if in_groove:
                add(drums, t * SR, kick(0.55))
                if k in (1, 3):
                    add(drums, t * SR, clap(0.30))
                add(drums, (t + beat / 2) * SR, hat(0.11))
                add(drums, t * SR, hat(0.05))
            elif in_intro and k in (0, 2) and t_bar >= max(0.0, hit - 2 * bar):
                add(drums, t * SR, kick(0.30))
                add(drums, (t + beat / 2) * SR, hat(0.05))
            elif t_bar >= outro and t < args.length - bar and k == 0:
                add(drums, t * SR, kick(0.4))
        # Plucked arpeggio in sixteenths, in the groove.
        if in_groove:
            pattern = [0, 1, 2, 3, 2, 1, 2, 3]
            notes = [n_ + 12 for n_ in chord] + [chord[0] + 24]
            for k in range(8):
                t = t_bar + k * beat / 2
                add(arp, t * SR, pluck(midi(notes[pattern[k] % 4]), 0.5, 0.05))
    # A riser into the hit and an impact on it.
    if hit > 1:
        ln = int(min(bar, hit) * SR)
        tt = np.arange(ln) / SR
        noise = highpass(RNG.standard_normal(ln), 2500) * (tt / tt[-1]) ** 3 * 0.03
        add(fx, hit * SR - ln, noise)
        add(fx, hit * SR, kick(0.9))
        imp = int(1.8 * SR)
        tt = np.arange(imp) / SR
        add(fx, hit * SR, lowpass(RNG.standard_normal(imp), 1500) * np.exp(-tt * 3) * 0.12)
    # Sidechain: duck the pad and bass after each kick in the groove.
    duck = np.ones(n)
    for b in range(nbars):
        for k in range(4):
            t = b * bar + k * beat
            if hit <= t < outro:
                i = int(t * SR)
                ln = int(beat * SR)
                tt = np.arange(min(ln, n - i)) / SR
                duck[i:i + len(tt)] = np.minimum(duck[i:i + len(tt)], 1 - 0.45 * np.exp(-tt * 9))
    pad_l *= duck
    pad_r *= duck
    bass *= duck
    # Reverb on the pad and the arpeggio, and a dotted eighth delay on the arpeggio.
    delay = int(0.75 * beat * SR)
    arp_d = arp.copy()
    arp_d[delay:] += 0.35 * arp[:-delay]
    ir_l, ir_r = reverb_ir()
    wet_l = fftconvolve(pad_l + arp_d * 0.8, ir_l)[:n] * 0.5
    wet_r = fftconvolve(pad_r + arp_d * 0.8, ir_r)[:n] * 0.5
    left = pad_l + wet_l + bass + drums + arp_d * 0.8 + fx
    right = pad_r + wet_r + bass + drums + np.roll(arp_d, int(0.012 * SR)) * 0.8 + fx
    # Fade out the tail after the end of the cut.
    end = int(args.length * SR)
    fade = np.ones(n)
    fade[end - int(2.5 * SR):end] = np.linspace(1, 0, int(2.5 * SR)) ** 2
    fade[end:] = 0
    left, right = left * fade, right * fade
    mix = np.stack([left, right], axis=1)[:end]
    mix = np.tanh(mix * 1.4) / 1.4
    mix /= np.max(np.abs(mix)) + 1e-9
    mix *= 0.89
    with wave.open(args.out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((mix * 32767).astype("<i2").tobytes())
    print(f"wrote {args.out}: {args.length:.1f} s at {args.bpm} bpm, hit at {hit:.2f} s, outro from {outro:.2f} s")


if __name__ == "__main__":
    main()
