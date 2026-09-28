"""Command line entry point and dispatcher for MADRATIF."""

from __future__ import annotations

import json
import os
import sys

from . import __version__
from . import config as cfgmod

USAGE = """MADRATIF - kontrol PC pribadi dari jarak jauh lewat MQTT

Perintah controller (ketik ini di HP / Termux atau terminal pengontrol):
  madratif clients                    tampilkan daftar client yang online
  madratif google <url> <client>      buka Chrome ke <url> di client
  madratif screensaver <client>       buka screensaver "MADRATIF" di client
  madratif status <client>            buka panel status di client
  madratif ping <client>              cek koneksi ke client

Perintah client (di PC yang mau dikontrol):
  madratif client start [--id NAMA]   jalankan agent (menunggu perintah)
  madratif client id                  tampilkan client id mesin ini

Konfigurasi:
  madratif setup                      buat / ubah konfigurasi
  madratif config                     tampilkan konfigurasi saat ini
  madratif version

Tips: pakai 'all' sebagai <client> untuk broadcast ke semua client.
Contoh:
  madratif google https://roblox.com client-1
  madratif screensaver client-1
"""


def _init_console():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass
    if os.name == "nt":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass


def cmd_setup() -> int:
    cfg = cfgmod.load()
    print("=== MADRATIF setup ===")
    broker = input(f"Broker MQTT [{cfg['broker']}]: ").strip() or cfg["broker"]
    port_raw = input(f"Port [{cfg['port']}]: ").strip() or str(cfg["port"])
    try:
        port = int(port_raw)
    except ValueError:
        port = cfg["port"]

    current_key = cfg.get("network_key") or ""
    key_hint = current_key or "(kosong = dibuat acak)"
    key = input(f"Network key (rahasia, samakan di semua device) [{key_hint}]: ").strip()
    if not key:
        key = current_key or cfgmod.generate_key()

    default_cid = cfg.get("client_id") or cfgmod.default_client_id()
    cid = input(f"Client ID mesin ini [{default_cid}]: ").strip() or default_cid

    cfg.update({"broker": broker, "port": port, "network_key": key, "client_id": cid})
    cfgmod.save(cfg)
    print("\nTersimpan di", cfgmod.CONFIG_PATH)
    print("Network key :", key)
    print("Client ID   :", cid)
    print("\nPENTING: samakan Broker + Network key di HP (controller) dan semua PC (client).")
    return 0


def cmd_config() -> int:
    cfg = cfgmod.load()
    safe = dict(cfg)
    if safe.get("password"):
        safe["password"] = "***"
    print(json.dumps(safe, indent=2))
    print("\nFile:", cfgmod.CONFIG_PATH)
    return 0


def main(argv=None) -> int:
    _init_console()
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0

    cmd = argv[0]
    rest = argv[1:]

    if cmd in ("version", "-v", "--version"):
        print("madratif", __version__)
        return 0
    if cmd == "setup":
        return cmd_setup()
    if cmd == "config":
        return cmd_config()

    # Internal commands used by the agent to open a fresh window locally.
    if cmd == "_screensaver":
        from . import screensaver

        return screensaver.run()
    if cmd == "_statuspanel":
        from . import statuspanel

        return statuspanel.run()

    # Client agent.
    if cmd == "client":
        sub = rest[0] if rest else "start"
        if sub == "start":
            cid = None
            if "--id" in rest:
                idx = rest.index("--id")
                if idx + 1 < len(rest):
                    cid = rest[idx + 1]
            from . import agent

            return agent.run(cid)
        if sub == "id":
            print(cfgmod.load().get("client_id") or cfgmod.default_client_id())
            return 0
        print("Sub-perintah tidak dikenal. Coba: madratif client start")
        return 2

    # Controller commands.
    from . import controller

    if cmd == "clients":
        return controller.list_clients()
    if cmd == "google":
        if len(rest) < 1:
            print("Pakai: madratif google <url> <client>")
            return 2
        url = rest[0]
        target = rest[1] if len(rest) > 1 else "all"
        return controller.send_command(target, "google", {"url": url})
    if cmd == "screensaver":
        if len(rest) < 1:
            print("Pakai: madratif screensaver <client>")
            return 2
        return controller.send_command(rest[0], "screensaver")
    if cmd == "status":
        if len(rest) < 1:
            print("Pakai: madratif status <client>")
            return 2
        return controller.send_command(rest[0], "status")
    if cmd == "ping":
        if len(rest) < 1:
            print("Pakai: madratif ping <client>")
            return 2
        return controller.send_command(rest[0], "ping")

    print(f"Perintah tidak dikenal: {cmd}\n")
    print(USAGE)
    return 2
