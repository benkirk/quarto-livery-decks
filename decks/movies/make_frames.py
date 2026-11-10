#!/usr/bin/env python3
"""The movies cookbook's stills (movies.qmd), drawn at build time so no binary is committed: a traveling
wave in the livery's style (MATPLOTLIBRC, which Make.common exports: transparent figures, so
frames2movie.py lays them on the livery's background), at an odd pixel size on purpose (frames2movie.py
pads it to even). Make runs it before frames2movie.py (the deck's Makefile).

    python3 make_frames.py frames/wave [N]"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

out = Path(sys.argv[1])
n = int(sys.argv[2]) if len(sys.argv) > 2 else 24
out.mkdir(parents=True, exist_ok=True)
x = np.linspace(0, 4 * np.pi, 400)
for k in range(n):
    fig, ax = plt.subplots(figsize=(6.41, 3.21))
    phase = 2 * np.pi * k / n
    ax.plot(x, np.sin(x - phase), label="u")
    ax.plot(x, 0.6 * np.sin(2 * x + phase), label="v")
    ax.set_ylim(-1.2, 1.2)
    ax.set_xlabel("x")
    ax.set_title(f"t = {k / n:.2f}")
    ax.legend(loc="upper right")
    fig.savefig(out / f"frame_{k}.png", dpi=100)   # 641 x 321 px, odd both ways; frame_9 before frame_10: frames2movie.py reads numbers as numbers
    plt.close(fig)
print(f"make_frames: {n} frame(s) → {out}")
