"""The client agent: runs on each PC, connects to the broker, waits for the
fixed set of commands, and reports its presence."""

from __future__ import annotations

import platform
import secrets
import socket
import threading
import time

from . import actions
from . import config as cfgmod
from . import protocol as P
from .mqttc import make_client

HEARTBEAT = 30  # seconds between presence refreshes


def _presence_payload(cid: str, status: str) -> bytes:
    return P.encode(
        {
            "status": status,
            "client_id": cid,
            "host": socket.gethostname(),
            "os": f"{platform.system()} {platform.release()}",
            "ts": P.now(),
        }
    )


def _handle(action: str, args: dict):
    try:
        if action == "google":
            return True, actions.open_chrome(args.get("url", ""))
        if action == "screensaver":
            return True, actions.open_screensaver()
        if action == "status":
            return True, actions.open_status_panel()
        if action == "ping":
            info = actions.system_summary()
            return True, f"pong dari {info['host']} ({info['os']})"
        return False, f"aksi tidak dikenal: {action}"
    except Exception as exc:  # noqa: BLE001 - report any failure back to controller
        return False, f"error: {exc}"


def run(client_id_override: str | None = None) -> int:
    cfg = cfgmod.load()
    if not cfg.get("network_key"):
        print("[madratif] Belum dikonfigurasi. Jalankan:  madratif setup")
        return 2

    cid = client_id_override or cfg.get("client_id") or cfgmod.default_client_id()
    nk = cfg["network_key"]
    presence = P.presence_topic(nk, cid)
    cmd_t = P.cmd_topic(nk, cid)
    ack_t = P.ack_topic(nk, cid)

    mqtt_id = f"madratif-agent-{cid}-{secrets.token_hex(3)}"
    client = make_client(cfg, mqtt_id, clean_session=True)
    client.will_set(presence, _presence_payload(cid, "offline"), qos=1, retain=True)

    def on_connect(c, _userdata, _flags, reason_code, _properties=None):
        if getattr(reason_code, "is_failure", False):
            print(f"[madratif] Gagal connect: {reason_code}")
            return
        c.publish(presence, _presence_payload(cid, "online"), qos=1, retain=True)
        c.subscribe(cmd_t, qos=1)
        print(f"[madratif] Client '{cid}' ONLINE - menunggu perintah ...")
        print(f"[madratif] Broker {cfg['broker']}:{cfg['port']}  network={nk}")

    def on_message(c, _userdata, msg):
        data = P.decode(msg.payload) or {}
        action = data.get("action")
        args = data.get("args") or {}
        reqid = data.get("reqid")
        print(f"[madratif] perintah diterima: {action} {args}")
        ok, detail = _handle(action, args)
        c.publish(
            ack_t,
            P.encode(
                {
                    "reqid": reqid,
                    "client_id": cid,
                    "action": action,
                    "ok": ok,
                    "detail": detail,
                    "ts": P.now(),
                }
            ),
            qos=1,
        )
        print(f"[madratif]  -> {'OK' if ok else 'GAGAL'}: {detail}")

    client.on_connect = on_connect
    client.on_message = on_message

    def heartbeat_loop():
        while True:
            time.sleep(HEARTBEAT)
            try:
                client.publish(presence, _presence_payload(cid, "online"), qos=0, retain=True)
            except Exception:
                pass

    try:
        client.connect(cfg["broker"], int(cfg["port"]), keepalive=45)
    except Exception as exc:  # noqa: BLE001
        print(f"[madratif] Tidak bisa connect ke broker: {exc}")
        return 1

    threading.Thread(target=heartbeat_loop, daemon=True).start()

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[madratif] Menutup - mengirim status offline.")
        try:
            client.publish(presence, _presence_payload(cid, "offline"), qos=1, retain=True)
            client.disconnect()
        except Exception:
            pass
    return 0
