"""Procedurally synthesized sound effects via pyglet.media.synthesis.

No audio assets: every sound is generated at startup. If the audio driver
is missing or synthesis fails, the bank silently no-ops so the game still
runs (e.g. headless or CI).
"""

from __future__ import annotations

import math


class SoundBank:
    def __init__(self):
        self._sounds = {}
        try:
            from pyglet.media import StaticSource
            from pyglet.media.synthesis import (
                Sine, Square, Sawtooth, WhiteNoise, LinearDecayEnvelope, ADSREnvelope,
            )

            decay = LinearDecayEnvelope()
            self._sounds = {
                # Emitter shot: short noise hiss
                "fire": StaticSource(WhiteNoise(0.25, envelope=decay)),
                # Player hit: low square thump
                "hit": StaticSource(Square(0.18, frequency=110, envelope=decay)),
                # Death: falling saw
                "death": StaticSource(Sawtooth(0.6, frequency=98, envelope=decay)),
                # Level portal chime
                "portal": StaticSource(Sine(0.35, frequency=880, envelope=decay)),
                # Final win
                "win": StaticSource(
                    Sine(0.9, frequency=660, envelope=ADSREnvelope(0.02, 0.2, 0.5)),
                ),
            }
        except Exception:
            self._sounds = {}

    def play(self, name: str, volume: float = 1.0):
        source = self._sounds.get(name)
        if source is None:
            return
        try:
            player = source.play()
            player.volume = max(0.0, min(1.0, volume))
        except Exception:
            pass

    def play_at(self, name: str, sx: float, sy: float, px: float, py: float):
        """Play with volume attenuated by distance from the player."""
        dist = math.hypot(sx - px, sy - py)
        self.play(name, volume=1.0 / (1.0 + dist * 0.35))
