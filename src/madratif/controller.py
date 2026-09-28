"""The controller side: list clients and send commands (used from Termux/phone)."""

from __future__ import annotations

import secrets
import threading
import time

from . import config as cfgmod
from . import protocol as P
from .mqttc import make_client


def _need_key(cfg: dict) -> bool:
    if not cfg.get("network_key"):
        print("Belum dikonfigurasi. Jalankan:  madratif setup")
        return False
    return True


def _connect(cfg, client_id, on_message):
    client = make_client(cfg, client_id, keepalive=30)
    client.on_message = on_message
    client.connect(cfg["broker"], int(cfg["port"]), keepalive=30)
    return client


def _discover(cfg: dict, nk: str, timeout: float = 1.5):
    found: dict = {}

    def on_message(topic, payload):
        cid = P.client_from_presence(topic)
        data = P.decode(payload) or {}
        if cid and data.get("status") == "online":
            found[cid] = data

    try:
        client = _connect(cfg, f"madratif-disc-{secrets.token_hex(3)}", on_message)
    except Exception:
        return []
    client.subscribe(P.presence_wildcard(nk), qos=1)
    client.loop_start()
    time.sleep(timeout)
    client.disconnect()
    return sorted(found)


def list_clients(timeout: float = 2.0) -> int:
    cfg = cfgmod.load()
    if not _need_key(cfg):
        return 2
    nk = cfg["network_key"]
    found: dict = {}

    def on_message(topic, payload):
        cid = P.client_from_presence(topic)
        data = P.decode(payload) or {}
        if cid:
            found[cid] = data

    try:
        client = _connect(cfg, f"madratif-ctl-{secrets.token_hex(3)}", on_message)
    except Exception as exc:  # noqa: BLE001
        print(f"Tidak bisa connect ke broker: {exc}")
        return 1
    client.subscribe(P.presence_wildcard(nk), qos=1)
    client.loop_start()
    time.sleep(timeout)
    client.disconnect()

    if not found:
        print("Tidak ada client terdeteksi.")
        print("Pastikan client sudah menjalankan agent dan network key sama.")
        return 0

    print(f"\n  CLIENTS  (network: {nk})")
    print("  " + "-" * 50)
    print(f"  {'CLIENT':<16}{'STATUS':<12}{'HOST':<20}")
    print("  " + "-" * 50)
    for cid in sorted(found):
        data = found[cid]
        status = data.get("status", "?")
        dot = "●" if status == "online" else "○"
        print(f"  {cid:<16}{dot + ' ' + status:<12}{str(data.get('host', '')):<20}")
    print()
    return 0


def send_command(client_id: str, action: str, args: dict | None = None, wait: float = 6.0) -> int:
    cfg = cfgmod.load()
    if not _need_key(cfg):
        return 2
    nk = cfg["network_key"]
    args = args or {}

    if client_id == "all":
        targets = _discover(cfg, nk)
        if not targets:
            print("Tidak ada client untuk broadcast.")
            return 0
    else:
        targets = [client_id]

    reqid = secrets.token_hex(4)
    acks: dict = {}
    done = threading.Event()

    def on_message(topic, payload):
        data = P.decode(payload) or {}
        if data.get("reqid") == reqid:
            acks[data.get("client_id")] = data
            if len(acks) >= len(targets):
                done.set()

    try:
        client = _connect(cfg, f"madratif-ctl-{secrets.token_hex(3)}", on_message)
    except Exception as exc:  # noqa: BLE001
        print(f"Tidak bisa connect ke broker: {exc}")
        return 1

    # Subscribe to the ack topics BEFORE publishing the command. Both go out on
    # the same TCP connection in order, so the subscription is registered at the
    # broker before the command is delivered -> no missed acks.
    for t in targets:
        client.subscribe(P.ack_topic(nk, t), qos=1)
    client.loop_start()

    payload = P.encode({"action": action, "args": args, "reqid": reqid, "ts": P.now()})
    for t in targets:
        client.publish(P.cmd_topic(nk, t), payload, qos=1)
        print(f"-> kirim '{action}' ke {t} ...")

    done.wait(timeout=wait)
    client.disconnect()

    if not acks:
        print("Tidak ada balasan (client offline / network key berbeda?).")
        return 1
    for cid, data in acks.items():
        mark = "OK   " if data.get("ok") else "GAGAL"
        print(f"  [{mark}] {cid}: {data.get('detail')}")
    return 0
