"""A live, refreshing status panel shown in its own terminal window."""

from __future__ import annotations

import platform
import socket
import sys
import time
from datetime import datetime

from . import config as cfgmod
from .screensaver import bring_to_front, enable_vt

RESET = "\033[0m"
HIDE = "\033[?25l"
SHOW = "\033[?25h"
CLEAR = "\033[2J"
HOME = "\033[H"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
GREY = "\033[90m"
WHITE = "\033[97m"
BOLD = "\033[1m"


def _local_ip() -> str:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return "n/a"


def run() -> int:
    enable_vt()
    bring_to_front()
    cfg = cfgmod.load()
    cid = cfg.get("client_id") or cfgmod.default_client_id()
    host = socket.gethostname()
    osname = f"{platform.system()} {platform.release()}"
    py = platform.python_version()
    ip = _local_ip()
    broker = f"{cfg.get('broker')}:{cfg.get('port')}"
    start = time.time()
    out = sys.stdout.write
    flush = sys.stdout.flush
    width = 52
    out(HIDE)

    try:
        while True:
            up = int(time.time() - start)
            clock = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rows = [
                f"{BOLD}{CYAN}MADRATIF — STATUS CLIENT{RESET}",
                "",
                f"{GREY}Client ID   :{RESET} {GREEN}{cid}{RESET}",
                f"{GREY}Hostname    :{RESET} {WHITE}{host}{RESET}",
                f"{GREY}Sistem      :{RESET} {WHITE}{osname}{RESET}",
                f"{GREY}IP lokal    :{RESET} {WHITE}{ip}{RESET}",
                f"{GREY}Python      :{RESET} {WHITE}{py}{RESET}",
                f"{GREY}Broker      :{RESET} {WHITE}{broker}{RESET}",
                f"{GREY}Status      :{RESET} {GREEN}● AKTIF{RESET}",
                f"{GREY}Panel uptime:{RESET} {YELLOW}{up}s{RESET}",
                f"{GREY}Waktu       :{RESET} {WHITE}{clock}{RESET}",
                "",
                f"{GREY}tekan Ctrl+C untuk menutup jendela ini{RESET}",
            ]
            out(CLEAR)
            out(HOME)
            out(f"  {CYAN}┌{'─' * width}┐{RESET}\n")
            for line in rows:
                out(f"  {CYAN}│{RESET}  {line}\n")
            out(f"  {CYAN}└{'─' * width}┘{RESET}\n")
            flush()
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        out(SHOW)
        out(RESET)
        flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
