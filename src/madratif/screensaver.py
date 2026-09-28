"""Floating, bouncing, colour-cycling 'MADRATIF' banner for a terminal window.

Big block letters are assembled from '#'-style blocks and animated across the
screen (DVD-logo style). If the banner is wider than the window it falls back
to a smooth horizontal marquee so the word is always readable.
"""

from __future__ import annotations

import os
import shutil
import sys
import time

RESET = "\033[0m"
HIDE = "\033[?25l"
SHOW = "\033[?25h"
CLEAR = "\033[2J"
HOME = "\033[H"

COLORS = [
    "\033[91m", "\033[92m", "\033[93m", "\033[94m", "\033[95m", "\033[96m",
    "\033[97m", "\033[38;5;208m", "\033[38;5;201m", "\033[38;5;51m",
    "\033[38;5;46m", "\033[38;5;226m",
]

# Each glyph is GLYPH_H rows tall. Blocks use the full-block char.
B = "█"
FONT = {
    "M": ["#   #", "## ##", "# # #", "#   #", "#   #", "#   #"],
    "A": [" ### ", "#   #", "#   #", "#####", "#   #", "#   #"],
    "D": ["#### ", "#   #", "#   #", "#   #", "#   #", "#### "],
    "R": ["#### ", "#   #", "#   #", "#### ", "#  # ", "#   #"],
    "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "],
    "I": ["###", " # ", " # ", " # ", " # ", "###"],
    "F": ["#####", "#    ", "#    ", "#### ", "#    ", "#    "],
    " ": ["   ", "   ", "   ", "   ", "   ", "   "],
}
GLYPH_H = 6


def build_banner(text: str):
    rows = ["" for _ in range(GLYPH_H)]
    for i, ch in enumerate(text):
        glyph = FONT.get(ch.upper(), FONT[" "])
        gap = "" if i == 0 else "  "
        for r in range(GLYPH_H):
            rows[r] += gap + glyph[r]
    rows = [row.replace("#", B) for row in rows]
    width = max((len(r) for r in rows), default=0)
    rows = [r.ljust(width) for r in rows]
    return rows, width


def enable_vt():
    if os.name == "nt":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
            kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass


def _term_size():
    size = shutil.get_terminal_size((80, 24))
    return max(size.columns, 10), max(size.lines, 8)


def run(text: str = "MADRATIF") -> int:
    enable_vt()
    banner, bw = build_banner(text)
    bh = GLYPH_H
    out = sys.stdout.write
    flush = sys.stdout.flush
    out(HIDE)

    x, y = 2.0, 2.0
    dx, dy = 0.9, 0.5
    ci = 0
    frame = 0
    marquee_off = 0
    prev = None
    last_size = None
    hint = " MADRATIF  •  tekan Ctrl+C untuk keluar "

    try:
        while True:
            cols, lines = _term_size()
            if (cols, lines) != last_size:
                out(CLEAR)
                last_size = (cols, lines)
                prev = None

            if bw + 4 <= cols and bh + 3 <= lines:
                # --- bounce mode ---
                x_min, x_max = 2, cols - bw
                y_min, y_max = 2, lines - 1 - bh
                x += dx
                y += dy
                bounced = False
                if x <= x_min:
                    x, dx, bounced = x_min, abs(dx), True
                elif x >= x_max:
                    x, dx, bounced = x_max, -abs(dx), True
                if y <= y_min:
                    y, dy, bounced = y_min, abs(dy), True
                elif y >= y_max:
                    y, dy, bounced = y_max, -abs(dy), True
                if bounced:
                    ci = (ci + 1) % len(COLORS)

                ix, iy = int(x), int(y)
                if prev is not None:
                    pix, piy = prev
                    for r in range(bh):
                        out(f"\033[{piy + r};{pix}H{' ' * bw}")
                color = COLORS[ci]
                for r in range(bh):
                    out(f"\033[{iy + r};{ix}H{color}{banner[r]}")
                out(RESET)
                prev = (ix, iy)
            else:
                # --- marquee mode (banner bigger than window) ---
                if frame % 24 == 0:
                    ci = (ci + 1) % len(COLORS)
                color = COLORS[ci]
                period = bw + cols
                off = marquee_off % period
                top = max(1, (lines - bh) // 2)
                vis = min(bh, max(1, lines - 1))
                for r in range(vis):
                    strip = banner[r] + " " * cols
                    seg = (strip + strip)[off:off + cols]
                    out(f"\033[{top + r};1H{color}{seg}{RESET}")
                marquee_off += 1
                prev = None

            out(f"\033[{lines};1H\033[90m{hint[:cols]}\033[K{RESET}")
            flush()
            frame += 1
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        out(SHOW)
        out(RESET)
        out(CLEAR)
        out(HOME)
        flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
