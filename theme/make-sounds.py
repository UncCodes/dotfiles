#!/usr/bin/env python3
"""Make the fui sound theme: aljulandani.dev's interface sounds, as files.

The site synthesises its sounds with the Web Audio API (public/js/sound.js): enveloped
sine and triangle notes, a short filtered feedback echo for the glassy tail, and a warm
detuned pad through a sweeping low-pass for the startup chime. This is the same synthesis
in Python, rendered to Ogg Vorbis under the freedesktop sound names, so every app that
plays system sounds (and fui sound) uses them.

  python3 theme/make-sounds.py      # writes fui/.local/share/sounds/fui/
Needs ffmpeg (libvorbis). Deterministic: the pad's random detune uses a fixed seed.
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
GAIN = 4.0          # the site plays quietly under a page; system sounds sit a little louder


class Mix:
    """A mono buffer with the site's graph: voices -> master, wet voices -> echo -> master."""

    def __init__(self, seconds):
        n = int(seconds * RATE)
        self.dry = [0.0] * n
        self.wet = [0.0] * n

    def add(self, buf, start, wet):
        i0 = int(start * RATE)
        for i, v in enumerate(buf):
            j = i0 + i
            if j < len(self.dry):
                self.dry[j] += v
                if wet:
                    self.wet[j] += v

    def render(self):
        # echo: delay 0.11 s -> low-pass 2600 Hz -> feedback 0.32 back into the delay; the
        # low-passed signal also goes to the master
        d = int(0.11 * RATE)
        a = math.exp(-2 * math.pi * 2600 / RATE)          # one-pole low-pass
        line = [0.0] * len(self.wet)
        echo = [0.0] * len(self.wet)
        lp = 0.0
        for i in range(len(self.wet)):
            delayed = line[i - d] if i >= d else 0.0
            lp = (1 - a) * delayed + a * lp
            echo[i] = lp
            line[i] = self.wet[i] + 0.32 * lp
        return [0.9 * (x + e) for x, e in zip(self.dry, echo)]


def osc(kind, phase):
    if kind == "sine":
        return math.sin(phase)
    t = (phase / (2 * math.pi)) % 1.0                    # triangle
    return 4 * abs(t - 0.5) - 1


def tone(kind, f0, f1, attack, length, gain):
    """One enveloped note: exponential attack to `gain`, exponential decay over `length`,
    the pitch gliding exponentially from f0 to f1 (Web Audio's exponentialRampToValueAtTime)."""
    n = int((attack + length + 0.05) * RATE)
    out, phase = [], 0.0
    for i in range(n):
        t = i / RATE
        f = f0 if f0 == f1 else f0 * (f1 / f0) ** min(t / length, 1.0)
        phase += 2 * math.pi * f / RATE
        if t < attack:
            env = 0.0001 * (gain / 0.0001) ** (t / attack)
        elif t < attack + length:
            env = gain * (0.0001 / gain) ** ((t - attack) / length)
        else:
            env = 0.0
        out.append(osc(kind, phase) * env)
    return out


def pad(down=False):
    """The startup chime: four detuned low voices (172/258/345/474 Hz) through a low-pass that
    sweeps 320 -> 1500 -> 500 Hz, swelling in over 0.55 s and fading out by 3.2 s.
    down=True: the logout version, shorter, the filter closing instead of opening."""
    rnd = random.Random(7)
    length = 2.2 if down else 3.3
    n = int(length * RATE)
    voices = [(172, "triangle", 1.0), (258, "triangle", 0.9), (345, "sine", 0.5), (474, "sine", 0.3)]
    det = [2 ** ((rnd.random() - 0.5) * 8 / 1200) for _ in voices]
    phases = [0.0] * len(voices)
    out = []
    x1 = x2 = y1 = y2 = 0.0
    for i in range(n):
        t = i / RATE
        s = 0.0
        for k, (f, kind, g) in enumerate(voices):
            phases[k] += 2 * math.pi * f * det[k] / RATE
            s += osc(kind, phases[k]) * g
        if down:
            fc = 1500 * (320 / 1500) ** min(t / 1.6, 1.0)
            env = (0.0001 * (0.07 / 0.0001) ** (t / 0.2)) if t < 0.2 else 0.07 * (0.0001 / 0.07) ** min((t - 0.2) / 1.9, 1.0)
        else:
            fc = 320 * (1500 / 320) ** (t / 1.1) if t < 1.1 else 1500 * (500 / 1500) ** min((t - 1.1) / 1.9, 1.0)
            if t < 0.55:
                env = 0.0001 * (0.07 / 0.0001) ** (t / 0.55)
            elif t < 1.2:
                env = 0.07
            else:
                env = 0.07 * (0.0001 / 0.07) ** min((t - 1.2) / 2.0, 1.0)
        # biquad low-pass, Q = 1 (Web Audio's default)
        w = 2 * math.pi * fc / RATE
        alpha = math.sin(w) / 2
        cw = math.cos(w)
        b0, b1, b2 = (1 - cw) / 2, 1 - cw, (1 - cw) / 2
        a0, a1, a2 = 1 + alpha, -2 * cw, 1 - alpha
        y = (b0 * s + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2) / a0
        x2, x1, y2, y1 = x1, s, y1, y
        out.append(y * env)
    return out


def sound(parts, seconds):
    m = Mix(seconds)
    for buf, start, wet in parts:
        m.add(buf, start, wet)
    return m.render()


# the site's cues, by name (sound.js), plus three made from them for the desktop
SOUNDS = {
    "tick":    lambda: sound([(tone("triangle", 1040, 1040, 0.003, 0.055, 0.06), 0, False),
                              (tone("sine", 760, 760, 0.003, 0.045, 0.035), 0, False)], 0.2),
    "select":  lambda: sound([(tone("sine", 668, 668, 0.05, 1.4, 0.09), 0, True), (tone("sine", 1336, 1336, 0.04, 1.0, 0.045), 0, True),
                              (tone("sine", 883, 883, 0.06, 0.6, 0.055), 0, True), (tone("sine", 1378, 1378, 0.05, 0.45, 0.032), 0, True)], 2.2),
    "open":    lambda: sound([(tone("sine", 668, 668, 0.012, 0.16, 0.09), 0, False),
                              (tone("sine", 1336, 1336, 0.01, 0.13, 0.045), 0.03, False)], 0.4),
    "move":    lambda: sound([(tone("sine", 520, 980, 0.01, 0.16, 0.06), 0, True)], 0.9),
    "unmove":  lambda: sound([(tone("sine", 980, 520, 0.01, 0.16, 0.06), 0, True)], 0.9),
    "startup": lambda: sound([(pad(), 0, True)], 3.8),
    "shutdown": lambda: sound([(pad(down=True), 0, True)], 2.7),
    "clap":    lambda: sound([(tone("sine", 400, 600, 0.008, 0.12, 0.1), 0, False)], 0.3),
    "key":     lambda: sound([(tone("triangle", 1200, 1200, 0.002, 0.02, 0.025), 0, False)], 0.1),
    # a warning: the open cue twice, a fourth lower
    "alert":   lambda: sound([(tone("sine", 501, 501, 0.012, 0.16, 0.1), 0, True), (tone("sine", 1002, 1002, 0.01, 0.13, 0.05), 0.03, True),
                              (tone("sine", 501, 501, 0.012, 0.16, 0.1), 0.22, True), (tone("sine", 1002, 1002, 0.01, 0.13, 0.05), 0.25, True)], 1.4),
    # an error: the clap falling
    "error":   lambda: sound([(tone("sine", 420, 260, 0.008, 0.22, 0.12), 0, False)], 0.4),
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


def write_ogg(samples, path):
    peak = max(1e-9, max(abs(s) for s in samples) * GAIN)
    g = GAIN if peak < 0.95 else GAIN * 0.95 / peak
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav = tmp.name
    with wave.open(wav, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<hh", v, v) for v in (int(max(-1, min(1, s * g)) * 32767) for s in samples)))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", wav, "-c:a", "libvorbis", "-q:a", "5",
                    "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact", str(path)], check=True)
    Path(wav).unlink()


def main():
    (OUT / "stereo").mkdir(parents=True, exist_ok=True)
    (OUT / "index.theme").write_text(
        "[Sound Theme]\nName=fui\nComment=aljulandani.dev's interface sounds (theme/make-sounds.py)\n"
        "Inherits=freedesktop\nDirectories=stereo\n\n[stereo]\nOutputProfile=stereo\n")
    made = {}
    for name, cue in NAMES.items():
        if cue not in made:
            made[cue] = SOUNDS[cue]()
        write_ogg(made[cue], OUT / "stereo" / f"{name}.oga")
    print(f"wrote {len(NAMES)} sounds ({len(made)} cues) into {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
