"""Load, save, and default the MADRATIF configuration (~/.madratif/config.json)."""

from __future__ import annotations

import json
import os
import re
import secrets
import socket
from pathlib import Path

CONFIG_DIR = Path.home() / ".madratif"
CONFIG_PATH = CONFIG_DIR / "config.json"

DEFAULTS = {
    "broker": "broker.emqx.io",
    "port": 1883,
    "network_key": "",
    "client_id": "",
    "username": "",
    "password": "",
    "tls": False,
}


def default_client_id() -> str:
    """A friendly client id derived from the machine hostname."""
    name = socket.gethostname() or "client"
    name = re.sub(r"[^A-Za-z0-9_-]", "-", name).strip("-").lower()
    return name or "client"


def generate_key() -> str:
    """A random, unguessable namespace used to isolate your devices on the broker."""
    return secrets.token_urlsafe(9)


def load() -> dict:
    cfg = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                cfg.update({k: data[k] for k in data if k in DEFAULTS})
        except Exception:
            pass

    env = os.environ
    if env.get("MADRATIF_BROKER"):
        cfg["broker"] = env["MADRATIF_BROKER"]
    if env.get("MADRATIF_PORT"):
        try:
            cfg["port"] = int(env["MADRATIF_PORT"])
        except ValueError:
            pass
    if env.get("MADRATIF_KEY"):
        cfg["network_key"] = env["MADRATIF_KEY"]
    if env.get("MADRATIF_CLIENT_ID"):
        cfg["client_id"] = env["MADRATIF_CLIENT_ID"]
    if env.get("MADRATIF_USERNAME"):
        cfg["username"] = env["MADRATIF_USERNAME"]
    if env.get("MADRATIF_PASSWORD"):
        cfg["password"] = env["MADRATIF_PASSWORD"]
    if env.get("MADRATIF_TLS"):
        cfg["tls"] = env["MADRATIF_TLS"].lower() in ("1", "true", "yes", "on")
    return cfg


def save(cfg: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    clean = {k: cfg.get(k, DEFAULTS[k]) for k in DEFAULTS}
    CONFIG_PATH.write_text(json.dumps(clean, indent=2), encoding="utf-8")
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except Exception:
        pass
