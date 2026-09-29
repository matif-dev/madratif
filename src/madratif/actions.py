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
import threading

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


def open_chrome(url: str, fullscreen: bool = False) -> str:
    target = _normalize_url(url)
    # --guest = jendela tamu: tanpa profil, tanpa pemilihan akun / login.
    extra = ["--guest", "--new-window"]
    if fullscreen:
        extra.append("--start-fullscreen")
    for path in CHROME_CANDIDATES:
        if path and os.path.exists(path):
            subprocess.Popen([path] + extra + [target])
            return f"Chrome (guest) dibuka -> {target}"
    if os.name == "nt":
        try:
            subprocess.Popen(["cmd", "/c", "start", "chrome"] + extra + [target])
            return f"Chrome (guest) dibuka -> {target}"
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


def rickroll() -> str:
    open_chrome("https://www.youtube.com/watch?v=dQw4w9WgXcQ", fullscreen=True)
    return "rickroll dibuka :)"


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
    args = list(args)
    if os.name == "nt":
        flags = subprocess.CREATE_NEW_CONSOLE  # type: ignore[attr-defined]
        # Force the classic console host (conhost) so borderless-fullscreen and
        # window styling work even when Windows Terminal is the default terminal.
        conhost = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "conhost.exe")
        if os.path.exists(conhost):
            try:
                subprocess.Popen([conhost] + args, creationflags=flags)
                return
            except Exception:
                pass
        subprocess.Popen(args, creationflags=flags)
        return
    subprocess.Popen(args)


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


def _no_window_flags() -> int:
    if os.name == "nt":
        return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    return 0


def say(text: str) -> str:
    """Text-to-speech via Windows SAPI. Text is passed through a temp file so
    it is data, never part of the PowerShell command (no injection)."""
    text = text or "halo"
    import tempfile

    fh = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
    fh.write(text)
    fh.close()
    safe = fh.name.replace("'", "''")
    ps = (
        "Add-Type -AssemblyName System.Speech;"
        f"$t=[IO.File]::ReadAllText('{safe}');"
        "(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak($t)"
    )
    subprocess.Popen(
        ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
        creationflags=_no_window_flags(),
    )
    return f"mengucapkan: {text[:40]}"


def notify(text: str, title: str = "MADRATIF") -> str:
    text = text or ""

    def _show():
        try:
            import ctypes

            # MB_ICONWARNING | MB_SYSTEMMODAL | MB_SETFOREGROUND | MB_TOPMOST
            flags = 0x30 | 0x1000 | 0x10000 | 0x40000
            ctypes.windll.user32.MessageBoxW(0, text, title, flags)
        except Exception:
            pass

    threading.Thread(target=_show, daemon=True).start()
    return f"notifikasi tampil: {text[:40]}"


def beep() -> str:
    def _play():
        try:
            import winsound

            for freq, dur in [(523, 150), (659, 150), (784, 150), (1047, 300), (784, 150), (1047, 400)]:
                winsound.Beep(freq, dur)
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()
    return "beep!"


def _wallpaper_backup_path():
    from . import config as cfgmod

    return cfgmod.CONFIG_DIR / "wallpaper_backup.txt"


def set_wallpaper(url: str) -> str:
    if str(url).strip().lower() == "reset":
        return reset_wallpaper()
    try:
        import ctypes

        SPI_SETDESKWALLPAPER = 20
        SPI_GETDESKWALLPAPER = 0x0073
        # backup current wallpaper so `reset` can restore it
        try:
            buf = ctypes.create_unicode_buffer(600)
            ctypes.windll.user32.SystemParametersInfoW(SPI_GETDESKWALLPAPER, 600, buf, 0)
            bp = _wallpaper_backup_path()
            bp.parent.mkdir(parents=True, exist_ok=True)
            bp.write_text(buf.value or "", encoding="utf-8")
        except Exception:
            pass
        # download the image
        import tempfile
        import urllib.request

        target = _normalize_url(url)
        ext = os.path.splitext(target.split("?")[0])[1] or ".jpg"
        path = os.path.join(tempfile.gettempdir(), "madratif_wallpaper" + ext)
        req = urllib.request.Request(target, headers={"User-Agent": "madratif"})
        with urllib.request.urlopen(req, timeout=25) as resp, open(path, "wb") as out:
            out.write(resp.read())
        ok = ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, path, 3)
        return "wallpaper diganti" if ok else "gagal set wallpaper"
    except Exception as exc:  # noqa: BLE001
        return f"error wallpaper: {exc}"


def reset_wallpaper() -> str:
    try:
        import ctypes

        try:
            cur = _wallpaper_backup_path().read_text(encoding="utf-8").strip()
        except Exception:
            cur = ""
        if not cur:
            return "tidak ada wallpaper cadangan"
        ctypes.windll.user32.SystemParametersInfoW(20, 0, cur, 3)
        return "wallpaper dikembalikan"
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


def minimize_all() -> str:
    subprocess.Popen(
        ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command",
         "(New-Object -ComObject Shell.Application).MinimizeAll()"],
        creationflags=_no_window_flags(),
    )
    return "semua jendela di-minimize"


def set_volume(level) -> str:
    def _run():
        try:
            import ctypes

            user32 = ctypes.windll.user32
            VK_VOLUME_DOWN = 0xAE
            VK_VOLUME_UP = 0xAF

            def tap(vk):
                user32.keybd_event(vk, 0, 0, 0)
                user32.keybd_event(vk, 0, 2, 0)

            for _ in range(52):  # turun ke 0 dulu
                tap(VK_VOLUME_DOWN)
            if str(level).lower() in ("max", "100"):
                steps = 52
            else:
                try:
                    steps = round(max(0, min(100, int(level))) / 2)
                except (ValueError, TypeError):
                    steps = 25
            for _ in range(steps):
                tap(VK_VOLUME_UP)
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()
    return f"volume -> {level}"


def rotate_screen(orientation: int) -> str:
    """orientation: 0 = normal, 2 = 180 derajat (terbalik)."""
    try:
        import ctypes
        from ctypes import wintypes

        class POINTL(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        class DEVMODE(ctypes.Structure):
            _fields_ = [
                ("dmDeviceName", ctypes.c_wchar * 32),
                ("dmSpecVersion", wintypes.WORD),
                ("dmDriverVersion", wintypes.WORD),
                ("dmSize", wintypes.WORD),
                ("dmDriverExtra", wintypes.WORD),
                ("dmFields", wintypes.DWORD),
                ("dmPosition", POINTL),
                ("dmDisplayOrientation", wintypes.DWORD),
                ("dmDisplayFixedOutput", wintypes.DWORD),
                ("dmColor", ctypes.c_short),
                ("dmDuplex", ctypes.c_short),
                ("dmYResolution", ctypes.c_short),
                ("dmTTOption", ctypes.c_short),
                ("dmCollate", ctypes.c_short),
                ("dmFormName", ctypes.c_wchar * 32),
                ("dmLogPixels", wintypes.WORD),
                ("dmBitsPerPel", wintypes.DWORD),
                ("dmPelsWidth", wintypes.DWORD),
                ("dmPelsHeight", wintypes.DWORD),
                ("dmDisplayFlags", wintypes.DWORD),
                ("dmDisplayFrequency", wintypes.DWORD),
                ("dmICMMethod", wintypes.DWORD),
                ("dmICMIntent", wintypes.DWORD),
                ("dmMediaType", wintypes.DWORD),
                ("dmDitherType", wintypes.DWORD),
                ("dmReserved1", wintypes.DWORD),
                ("dmReserved2", wintypes.DWORD),
                ("dmPanningWidth", wintypes.DWORD),
                ("dmPanningHeight", wintypes.DWORD),
            ]

        ENUM_CURRENT_SETTINGS = -1
        DM_DISPLAYORIENTATION = 0x00000080
        dm = DEVMODE()
        dm.dmSize = ctypes.sizeof(DEVMODE)
        if not ctypes.windll.user32.EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(dm)):
            return "gagal baca pengaturan layar"
        dm.dmFields = DM_DISPLAYORIENTATION
        dm.dmDisplayOrientation = orientation
        res = ctypes.windll.user32.ChangeDisplaySettingsExW(None, ctypes.byref(dm), None, 0, None)
        if res == 0:
            return "layar diputar" if orientation else "layar dinormalkan"
        return f"gagal memutar layar (kode {res})"
    except Exception as exc:  # noqa: BLE001
        return f"error putar layar: {exc}"


def open_matrix() -> str:
    _spawn_new_console([_console_python(), "-m", "madratif", "_matrix"])
    return "matrix dibuka"


def open_fakeupdate() -> str:
    _spawn_new_console([_console_python(), "-m", "madratif", "_fakeupdate"])
    return "layar fake-update dibuka"


def open_bsod() -> str:
    _spawn_new_console([_console_python(), "-m", "madratif", "_bsod"])
    return "layar biru (palsu) dibuka"


def open_disco() -> str:
    _spawn_new_console([_console_python(), "-m", "madratif", "_disco"])
    return "disco dimulai"


def open_countdown(seconds: int) -> str:
    _spawn_new_console([_console_python(), "-m", "madratif", "_countdown", str(seconds)])
    return f"hitung mundur {seconds} detik dimulai"
