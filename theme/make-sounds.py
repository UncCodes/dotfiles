#!/usr/bin/env python3
"""Make the fui sound theme: deep, spacious interface cues.

Original synthesis in the spirit of late-90s console system menus: slow-swelling detuned
pads over a sub-bass, glassy FM bell tones with long tails, soft filtered "air", all placed
in a wide stereo hall. Rendered to Ogg Vorbis under the freedesktop sound names, so every app
that plays system sounds (and fui sound) uses them.

  python3 theme/make-sounds.py      # writes fui/.local/share/sounds/fui/
Needs ffmpeg (libvorbis). Deterministic: every random choice uses a fixed seed.
"""
import math
import random
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

RATE = 44100
OUT = Path(__file__).resolve().parent.parent / "fui/.local/share/sounds/fui"
TAU = 2 * math.pi


# ── voices (mono buffers) ───────────────────────────────────────────────
def env_ad(t, attack, decay):
    """A smooth attack, then an exponential decay to silence over `decay` seconds."""
    if t < attack:
        return math.sin(0.5 * math.pi * t / attack) ** 2
    return math.exp(-5.0 * (t - attack) / decay)


def bell(f, length, gain, ratio=1.4, index=2.6, attack=0.004):
    """A glassy FM bell: an inharmonic modulator whose depth fades faster than the note."""
    n = int(length * RATE)
    out = []
    for i in range(n):
        t = i / RATE
        mod = index * math.exp(-6.0 * t / length) * math.sin(TAU * f * ratio * t)
        out.append(gain * env_ad(t, attack, length) * math.sin(TAU * f * t + mod))
    return out


def pluck(f0, f1, length, gain):
    """A soft cursor blip: a sine that drops in pitch over its first 30 ms."""
    n = int(length * RATE)
    out, ph = [], 0.0
    for i in range(n):
        t = i / RATE
        f = f1 + (f0 - f1) * math.exp(-t / 0.012)
        ph += TAU * f / RATE
        out.append(gain * env_ad(t, 0.002, length) * (math.sin(ph) + 0.25 * math.sin(2 * ph)))
    return out


def pad(freqs, length, gain, attack, release, seed=3):
    """A slow, warm chord: three detuned sines per note, a gentle stereo-free swell."""
    rnd = random.Random(seed)
    voices = [(f * 2 ** (c / 1200), rnd.random() * TAU) for f in freqs for c in (-7, 0, 6)]
    n = int(length * RATE)
    out = []
    for i in range(n):
        t = i / RATE
        e = min(1.0, t / attack) ** 2 * (1.0 if t < length - release else max(0.0, (length - t) / release) ** 2)
        s = sum(math.sin(TAU * f * t + p) for f, p in voices) / len(voices)
        out.append(gain * e * s)
    return out


def sub(f, length, gain, attack, release):
    """A deep sub-bass swell under a cue."""
    n = int(length * RATE)
    return [gain * min(1.0, (i / RATE) / attack) ** 2 * max(0.0, min(1.0, (length - i / RATE) / release))
            * math.sin(TAU * f * i / RATE) for i in range(n)]


def air(length, gain, f0, f1, seed=11):
    """Soft filtered noise whose band sweeps from f0 to f1: a breath, a whoosh."""
    rnd = random.Random(seed)
    n = int(length * RATE)
    out, lp, bp = [], 0.0, 0.0
    for i in range(n):
        t = i / RATE
        fc = f0 * (f1 / f0) ** (t / length)
        a = math.exp(-TAU * fc / RATE)
        x = rnd.uniform(-1, 1)
        lp = (1 - a) * x + a * lp
        bp = (1 - a) * lp + a * bp
        e = math.sin(math.pi * min(1.0, t / length)) ** 2
        out.append(gain * e * (lp - bp) * 4)
    return out


# ── the hall: a stereo reverb (four combs and two all-passes per side) ──
class Hall:
    def __init__(self, seconds):
        n = int(seconds * RATE)
        self.L, self.R = [0.0] * n, [0.0] * n
        self.sendL, self.sendR = [0.0] * n, [0.0] * n

    def add(self, buf, start, pan=0.0, wet=0.6):
        gl, gr = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        i0 = int(start * RATE)
        for i, v in enumerate(buf):
            j = i0 + i
            if j >= len(self.L):
                break
            self.L[j] += v * gl
            self.R[j] += v * gr
            self.sendL[j] += v * gl * wet
            self.sendR[j] += v * gr * wet

    @staticmethod
    def _reverb(x, combs, allpasses, feedback, damp):
        out = [0.0] * len(x)
        for d in combs:
            buf, store, k = [0.0] * d, 0.0, 0
            for i, v in enumerate(x):
                y = buf[k]
                store = y * (1 - damp) + store * damp
                buf[k] = v + store * feedback
                out[i] += y
                k = (k + 1) % d
        for d in allpasses:
            buf, k = [0.0] * d, 0
            for i, v in enumerate(out):
                b = buf[k]
                buf[k] = v + b * 0.5
                out[i] = b - v
                k = (k + 1) % d
        return [v / len(combs) for v in out]

    def render(self, size=0.86, damp=0.35, mix=0.55):
        wl = self._reverb(self.sendL, [1557, 1617, 1491, 1422], [556, 441], size, damp)
        wr = self._reverb(self.sendR, [1580, 1640, 1514, 1445], [579, 464], size, damp)
        return [a + mix * b for a, b in zip(self.L, wl)], [a + mix * b for a, b in zip(self.R, wr)]


def scene(seconds, parts, **hall):
    h = Hall(seconds)
    for p in parts:
        h.add(*p)
    return h.render(**hall)


# ── the cues ────────────────────────────────────────────────────────────
A2, E3, B3, Cs4, Gs4, E5, B5, Cs6, E6, Gs6, B6 = 110.0, 164.81, 246.94, 277.18, 415.3, 659.26, 987.77, 1108.73, 1318.51, 1661.22, 1975.53

SOUNDS = {
    # signed in: a sub swell, a warm pad (A major 9), a breath of air, glass bells rising
    "startup": lambda: scene(7.0, [
        (sub(55.0, 5.0, 0.30, 1.6, 2.4), 0.0, 0.0, 0.2),
        (pad([A2, E3, B3, Cs4, Gs4], 5.2, 0.22, 1.8, 2.6), 0.2, 0.0, 0.7),
        (air(2.4, 0.10, 300, 3600), 0.3, 0.0, 0.8),
        (bell(E5, 3.2, 0.10), 1.3, -0.35, 0.9),
        (bell(B5, 3.0, 0.08), 1.65, 0.35, 0.9),
        (bell(E6, 3.4, 0.07, ratio=2.0), 2.0, -0.15, 1.0),
        (bell(Gs6, 3.6, 0.05, ratio=2.0), 2.4, 0.25, 1.0),
    ], size=0.88, mix=0.6),
    # signing out: the pad settles and the bells fall away
    "shutdown": lambda: scene(5.0, [
        (pad([A2, E3, B3, Cs4], 3.4, 0.18, 0.4, 2.6), 0.0, 0.0, 0.7),
        (bell(E6, 2.6, 0.07, ratio=2.0), 0.0, 0.3, 0.9),
        (bell(B5, 2.6, 0.07), 0.3, -0.3, 0.9),
        (bell(E5, 3.0, 0.08), 0.6, 0.0, 0.9),
        (air(1.6, 0.06, 2400, 300, seed=5), 0.1, 0.0, 0.8),
    ], size=0.86),
    # an incoming notice: two glass bells, a fifth apart, in the hall
    "select": lambda: scene(2.6, [
        (bell(E6, 1.4, 0.10, ratio=2.0), 0.0, -0.25, 0.8),
        (bell(B6, 1.6, 0.08, ratio=2.0), 0.09, 0.25, 0.8),
    ], size=0.8),
    # a toggle, a volume step, a button: a soft cursor blip with a little room
    "tick": lambda: scene(0.5, [
        (pluck(1480, 1110, 0.09, 0.16), 0.0, 0.0, 0.25),
    ], size=0.6, mix=0.3),
    # something opened: a breath rising into a bell
    "open": lambda: scene(1.4, [
        (air(0.35, 0.07, 600, 5200, seed=2), 0.0, 0.0, 0.6),
        (bell(B5, 0.9, 0.06, ratio=2.0), 0.12, 0.1, 0.7),
    ], size=0.72),
    # the edition changing: a whoosh and a short pad bloom
    "move": lambda: scene(2.2, [
        (air(0.7, 0.10, 400, 4200, seed=9), 0.0, -0.2, 0.7),
        (pad([E3, B3, Gs4], 1.2, 0.12, 0.25, 0.8, seed=4), 0.15, 0.2, 0.7),
        (bell(E6, 1.2, 0.05, ratio=2.0), 0.35, 0.0, 0.8),
    ], size=0.8),
    "unmove": lambda: scene(1.8, [
        (air(0.7, 0.10, 4200, 400, seed=9), 0.0, 0.2, 0.7),
        (pad([A2, E3, B3], 1.0, 0.12, 0.15, 0.8, seed=4), 0.1, -0.2, 0.7),
    ], size=0.8),
    # a capture: a crisp breath and a bright bell
    "clap": lambda: scene(1.2, [
        (air(0.12, 0.12, 2400, 9000, seed=6), 0.0, 0.0, 0.4),
        (bell(Cs6, 0.7, 0.06, ratio=3.5, index=1.2), 0.03, 0.0, 0.5),
    ], size=0.65),
    # a key: the smallest blip
    "key": lambda: scene(0.3, [(pluck(2200, 1760, 0.04, 0.06), 0.0, 0.0, 0.15)], size=0.5, mix=0.2),
    # attention: two even, round low bells
    "alert": lambda: scene(2.0, [
        (bell(659.26, 0.8, 0.11, ratio=1.0, index=1.4), 0.0, -0.15, 0.6),
        (bell(659.26, 0.8, 0.11, ratio=1.0, index=1.4), 0.32, 0.15, 0.6),
    ], size=0.75),
    # an error: a low, muted fall
    "error": lambda: scene(1.6, [
        (bell(311.13, 0.7, 0.12, ratio=1.0, index=0.9), 0.0, 0.0, 0.4),
        (bell(277.18, 0.9, 0.12, ratio=1.0, index=0.9), 0.16, 0.0, 0.4),
    ], size=0.7, mix=0.4),
}

# freedesktop names -> cue
NAMES = {
    "desktop-login": "startup", "service-login": "startup",
    "desktop-logout": "shutdown", "service-logout": "shutdown",
    "message-new-instant": "select", "message": "select", "complete": "select", "dialog-information": "select",
    "dialog-warning": "alert", "dialog-error": "error", "suspend-error": "error",
    "audio-volume-change": "tick", "button-pressed": "tick", "bell": "tick", "bell-window-system": "tick",
    "window-new": "open", "theme-change": "move", "device-added": "move", "device-removed": "unmove",
    "screen-capture": "clap", "camera-shutter": "clap", "keypress": "key",
}


def write_ogg(stereo, path, level=0.7):
    L, R = stereo
    peak = max(1e-9, max(max(abs(v) for v in L), max(abs(v) for v in R)))
    g = level / peak
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav = tmp.name
    with wave.open(wav, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<hh", int(max(-1, min(1, a * g)) * 32767), int(max(-1, min(1, b * g)) * 32767))
                               for a, b in zip(L, R)))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", wav, "-c:a", "libvorbis", "-q:a", "5",
                    "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact", str(path)], check=True)
    Path(wav).unlink()


LEVEL = {"tick": 0.45, "key": 0.3, "startup": 0.75, "shutdown": 0.7}   # small cues sit quieter


def main():
    (OUT / "stereo").mkdir(parents=True, exist_ok=True)
    (OUT / "index.theme").write_text(
        "[Sound Theme]\nName=fui\nComment=fui workstation interface cues (theme/make-sounds.py)\n"
        "Inherits=freedesktop\nDirectories=stereo\n\n[stereo]\nOutputProfile=stereo\n")
    made = {}
    for name, cue in NAMES.items():
        if cue not in made:
            made[cue] = SOUNDS[cue]()
        write_ogg(made[cue], OUT / "stereo" / f"{name}.oga", LEVEL.get(cue, 0.6))
    print(f"wrote {len(NAMES)} sounds ({len(made)} cues) into {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
