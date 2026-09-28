"""Full-screen console prank animations: matrix, fake update, fake BSOD,
disco, countdown. All harmless and closeable (press a key / Ctrl+C).

Set env MADRATIF_PRANK_FRAMES=N to run only N frames then exit (used for
non-interactive testing)."""

from __future__ import annotations

import os
import random
import shutil
import sys
import time

from .screensaver import enable_vt

RESET = "\033[0m"
HIDE = "\033[?25l"
SHOW = "\033[?25h"
CLEAR = "\033[2J"
HOME = "\033[H"


def _frame_limit():
    try:
        n = int(os.environ.get("MADRATIF_PRANK_FRAMES", "0"))
        return n if n > 0 else None
    except ValueError:
        return None


def _maximize():
    if os.name == "nt":
        try:
            import ctypes

            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
        except Exception:
            pass


def _key_pressed() -> bool:
    if os.name == "nt":
        try:
            import msvcrt

            if msvcrt.kbhit():
                msvcrt.getch()
                return True
        except Exception:
            return False
    return False


def _size():
    s = shutil.get_terminal_size((100, 30))
    return max(s.columns, 20), max(s.lines, 10)


def _center(text, width):
    return max(0, (width - len(text)) // 2)


def _begin():
    enable_vt()
    _maximize()
    time.sleep(0.15)
    sys.stdout.write(HIDE)


def _end():
    sys.stdout.write(SHOW + RESET + CLEAR + HOME)
    sys.stdout.flush()


# --------------------------------------------------------------------------- matrix
def matrix() -> int:
    _begin()
    cols, rows = _size()
    drops = [random.randint(-rows, 0) for _ in range(cols)]
    chars = "01234567890ABCDEFｱｲｳｴｵｶｷｸ#$%&@*+=<>"
    limit = _frame_limit()
    frame = 0
    try:
        sys.stdout.write("\033[40m" + CLEAR)
        while not _key_pressed():
            out = []
            for c in range(cols):
                y = drops[c]
                if 0 <= y < rows:
                    out.append(f"\033[{y + 1};{c + 1}H\033[97m{random.choice(chars)}")
                    if 0 <= y - 1 < rows:
                        out.append(f"\033[{y};{c + 1}H\033[92m{random.choice(chars)}")
                    if 0 <= y - 6 < rows:
                        out.append(f"\033[{y - 5};{c + 1}H ")
                drops[c] += 1
                if drops[c] > rows + 6:
                    drops[c] = random.randint(-rows, 0)
            sys.stdout.write("".join(out))
            sys.stdout.flush()
            frame += 1
            if limit and frame >= limit:
                break
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        _end()
    return 0


# --------------------------------------------------------------------------- fake update
def fakeupdate() -> int:
    _begin()
    spin = "|/-\\"
    pct = 0
    limit = _frame_limit()
    frame = 0
    try:
        while not _key_pressed():
            cols, rows = _size()
            sys.stdout.write("\033[44m" + CLEAR)
            cy = rows // 2
            line1 = f"{spin[frame % 4]}  Working on updates  {pct}% complete"
            line2 = "Don't turn off your PC. This will take a while."
            sys.stdout.write(f"\033[{cy};{_center(line1, cols) + 1}H\033[97m\033[44m{line1}")
            sys.stdout.write(f"\033[{cy + 2};{_center(line2, cols) + 1}H\033[97m\033[44m{line2}")
            sys.stdout.flush()
            frame += 1
            if frame % 6 == 0 and pct < 99:
                pct += 1
            if limit and frame >= limit:
                break
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        _end()
    return 0


# --------------------------------------------------------------------------- fake BSOD
def bsod() -> int:
    _begin()
    pct = 0
    limit = _frame_limit()
    frame = 0
    lines = [
        ":(",
        "",
        "Your PC ran into a problem and needs to restart. We're",
        "just collecting some error info, and then we'll restart",
        "for you.",
        "",
        "{pct}% complete",
        "",
        "Stop code: MADRATIF_JUST_KIDDING",
        "",
        "(tekan tombol apa saja untuk keluar)",
    ]
    try:
        while not _key_pressed():
            cols, rows = _size()
            sys.stdout.write("\033[44m" + CLEAR)
            left = max(2, cols // 6)
            top = max(2, rows // 4)
            for i, raw in enumerate(lines):
                text = raw.format(pct=pct)
                size = "\033[1m" if i == 0 else ""
                sys.stdout.write(f"\033[{top + i};{left}H\033[97m\033[44m{size}{text}\033[22m")
            sys.stdout.flush()
            frame += 1
            if frame % 4 == 0 and pct < 100:
                pct += 1
            if limit and frame >= limit:
                break
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass
    finally:
        _end()
    return 0


# --------------------------------------------------------------------------- disco
def disco() -> int:
    _begin()
    bgs = [41, 42, 43, 44, 45, 46, 101, 102, 103, 104, 105, 106]
    limit = _frame_limit()
    frame = 0
    end = time.time() + 8  # otomatis berhenti setelah 8 detik
    try:
        while not _key_pressed() and time.time() < end:
            cols, rows = _size()
            bg = random.choice(bgs)
            sys.stdout.write(f"\033[{bg}m" + CLEAR)
            word = "* DISCO *"
            sys.stdout.write(f"\033[{rows // 2};{_center(word, cols) + 1}H\033[1m\033[97m{word}")
            sys.stdout.flush()
            frame += 1
            if limit and frame >= limit:
                break
            time.sleep(0.12)
    except KeyboardInterrupt:
        pass
    finally:
        _end()
    return 0


# --------------------------------------------------------------------------- countdown
_DIGITS = {
    "0": ["███", "█ █", "█ █", "█ █", "█ █", "███"],
    "1": [" █ ", "██ ", " █ ", " █ ", " █ ", "███"],
    "2": ["███", "  █", "███", "█  ", "█  ", "███"],
    "3": ["███", "  █", "███", "  █", "  █", "███"],
    "4": ["█ █", "█ █", "███", "  █", "  █", "  █"],
    "5": ["███", "█  ", "███", "  █", "  █", "███"],
    "6": ["███", "█  ", "███", "█ █", "█ █", "███"],
    "7": ["███", "  █", "  █", "  █", "  █", "  █"],
    "8": ["███", "█ █", "███", "█ █", "█ █", "███"],
    "9": ["███", "█ █", "███", "  █", "  █", "███"],
    " ": ["   ", "   ", "   ", "   ", "   ", "   "],
}
_DIGIT_H = 6


def _big_number(text: str):
    rows = ["" for _ in range(_DIGIT_H)]
    for i, ch in enumerate(str(text)):
        glyph = _DIGITS.get(ch, _DIGITS[" "])
        gap = "" if i == 0 else "  "
        for r in range(_DIGIT_H):
            rows[r] += gap + glyph[r]
    width = max((len(r) for r in rows), default=0)
    return [r.ljust(width) for r in rows], width


def countdown(seconds: int = 10) -> int:
    _begin()
    colors = ["\033[91m", "\033[93m", "\033[92m", "\033[96m", "\033[95m"]
    try:
        n = int(seconds)
    except (ValueError, TypeError):
        n = 10
    n = max(1, min(999, n))
    try:
        while n > 0 and not _key_pressed():
            cols, rows = _size()
            banner, bw = _big_number(n)
            color = colors[n % len(colors)]
            sys.stdout.write("\033[40m" + CLEAR)
            top = max(1, (rows - _DIGIT_H) // 2)
            left = _center(banner[0], cols) + 1
            for r in range(_DIGIT_H):
                sys.stdout.write(f"\033[{top + r};{left}H{color}{banner[r]}")
            tag = "SELF-DESTRUCT..."
            sys.stdout.write(f"\033[{top - 2};{_center(tag, cols) + 1}H\033[90m{tag}")
            sys.stdout.flush()
            time.sleep(1)
            n -= 1
        # ledakan bercanda
        cols, rows = _size()
        sys.stdout.write("\033[41m" + CLEAR)
        for msg, dy in [("*** BOOM ***", 0), ("... cuma bercanda :)", 2)]:
            sys.stdout.write(f"\033[{rows // 2 + dy};{_center(msg, cols) + 1}H\033[1m\033[97m{msg}")
        sys.stdout.flush()
        if not _frame_limit():
            time.sleep(3)
    except KeyboardInterrupt:
        pass
    finally:
        _end()
    return 0
