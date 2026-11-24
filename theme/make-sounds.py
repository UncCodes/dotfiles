#!/usr/bin/env python3
"""Make the fui sound theme: crisp synthetic interface cues for an issued workstation.

Enveloped sine and triangle notes, a short filtered feedback echo for a clean tail, and a
low swell under the sign-in arpeggio. Rendered to Ogg Vorbis under the freedesktop sound
names, so every app that plays system sounds (and fui sound) uses them.

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
    """The low swell under the sign-in cue: four detuned voices (C3, G3, C4, G4) through a
    low-pass that sweeps 320 -> 1500 -> 500 Hz, swelling in over 0.55 s and out by 3.2 s.
    down=True: a shorter version with the filter closing."""
    rnd = random.Random(7)
    length = 2.2 if down else 3.3
    n = int(length * RATE)
    voices = [(130.8, "sine", 1.0), (196, "sine", 0.7), (261.6, "triangle", 0.35), (392, "sine", 0.2)]
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


# the cues
def arpeggio(freqs, step, length, gain, wet=True):
    return [(tone("sine", f, f, 0.012, length, gain), i * step, wet) for i, f in enumerate(freqs)]


SOUNDS = {
    # a dry, short blip: toggles, volume, buttons
    "tick":    lambda: sound([(tone("sine", 1760, 1760, 0.002, 0.04, 0.05), 0, False),
                              (tone("triangle", 3520, 3520, 0.001, 0.015, 0.012), 0, False)], 0.15),
    # an incoming notice: two notes up a fifth, a clean tail
    "select":  lambda: sound(arpeggio([880, 1318.5], 0.07, 0.42, 0.07), 1.3),
    # something opened
    "open":    lambda: sound(arpeggio([1174.7, 1568], 0.045, 0.12, 0.05, False), 0.35),
    # the edition changing: a quick filtered rise
    "move":    lambda: sound([(tone("sine", 600, 1200, 0.01, 0.18, 0.05), 0, True)], 0.9),
    "unmove":  lambda: sound([(tone("sine", 1200, 600, 0.01, 0.18, 0.05), 0, True)], 0.9),
    # signed in: an ascending major arpeggio over a low swell
    "startup": lambda: sound([(pad(), 0, True)] + arpeggio([523.3, 659.3, 784, 1046.5], 0.11, 0.9, 0.06), 3.8),
    # signing out: the same, falling
    "shutdown": lambda: sound(arpeggio([1046.5, 784, 659.3, 523.3], 0.1, 0.6, 0.055), 2.0),
    # a capture: a short bright glide down
    "clap":    lambda: sound([(tone("triangle", 2600, 1300, 0.002, 0.07, 0.06), 0, False),
                              (tone("sine", 1300, 1300, 0.002, 0.05, 0.03), 0.05, False)], 0.3),
    "key":     lambda: sound([(tone("sine", 2093, 2093, 0.001, 0.015, 0.02), 0, False)], 0.08),
    # attention: two even pulses
    "alert":   lambda: sound([(tone("triangle", 740, 740, 0.004, 0.11, 0.08), 0, True),
                              (tone("triangle", 740, 740, 0.004, 0.11, 0.08), 0.18, True)], 1.2),
    # an error: a falling minor third, low
    "error":   lambda: sound([(tone("sine", 392, 392, 0.006, 0.16, 0.09), 0, False),
                              (tone("sine", 329.6, 329.6, 0.006, 0.22, 0.09), 0.14, False)], 0.6),
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
        "[Sound Theme]\nName=fui\nComment=fui workstation interface cues (theme/make-sounds.py)\n"
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
