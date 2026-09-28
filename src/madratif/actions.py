"""The fixed, benign set of actions an agent can perform on request.

Deliberately limited to: open Chrome at a URL, open a screensaver window,
open a status window, and reply to a ping. There is no arbitrary command
execution -- this keeps MADRATIF a simple personal tool, not a remote shell.
"""

from __future__ import annotations

import os
import platform
import socket
import subprocess
import sys

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]


def _normalize_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return "about:blank"
    if "://" not in url:
        url = "https://" + url
    return url


def open_chrome(url: str) -> str:
    target = _normalize_url(url)
    for path in CHROME_CANDIDATES:
        if path and os.path.exists(path):
            subprocess.Popen([path, target])
            return f"Chrome dibuka -> {target}"
    if os.name == "nt":
        try:
            subprocess.Popen(["cmd", "/c", "start", "chrome", target])
            return f"Chrome dibuka (start) -> {target}"
        except Exception:
            pass
        try:
            os.startfile(target)  # type: ignore[attr-defined]
            return f"Browser default dibuka -> {target}"
        except Exception:
            pass
    import webbrowser

    webbrowser.open(target)
    return f"Browser dibuka -> {target}"


def _console_python() -> str:
    """Path to a *console* python (so a new window actually appears even when
    the agent itself was launched with pythonw.exe in the background)."""
    exe = sys.executable
    if os.name == "nt" and exe.lower().endswith("pythonw.exe"):
        candidate = exe[: -len("pythonw.exe")] + "python.exe"
        if os.path.exists(candidate):
            return candidate
    return exe


def _spawn_new_console(args) -> None:
    kwargs = {}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE  # type: ignore[attr-defined]
    subprocess.Popen(args, **kwargs)


def open_screensaver() -> str:
    _spawn_new_console([_console_python(), "-m", "madratif", "_screensaver"])
    return "jendela screensaver dibuka"


def open_status_panel() -> str:
    _spawn_new_console([_console_python(), "-m", "madratif", "_statuspanel"])
    return "jendela status dibuka"


def system_summary() -> dict:
    return {
        "host": socket.gethostname(),
        "os": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
    }
