"""Topic names and message (de)serialisation shared by controller and agent."""

from __future__ import annotations

import json
import time

BASE = "madratif"


def _root(nk: str) -> str:
    return f"{BASE}/{nk}"


def presence_topic(nk: str, cid: str) -> str:
    return f"{_root(nk)}/clients/{cid}/presence"


def cmd_topic(nk: str, cid: str) -> str:
    return f"{_root(nk)}/clients/{cid}/cmd"


def ack_topic(nk: str, cid: str) -> str:
    return f"{_root(nk)}/clients/{cid}/ack"


def presence_wildcard(nk: str) -> str:
    return f"{_root(nk)}/clients/+/presence"


def client_from_presence(topic: str):
    parts = topic.split("/")
    if len(parts) >= 5 and parts[-1] == "presence":
        return parts[-2]
    return None


def encode(obj) -> bytes:
    return json.dumps(obj, separators=(",", ":")).encode("utf-8")


def decode(payload: bytes):
    try:
        return json.loads(payload.decode("utf-8"))
    except Exception:
        return None


def now() -> float:
    return round(time.time(), 3)
