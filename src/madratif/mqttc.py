"""Factory that builds a configured MiniMQTT client (no third-party deps)."""

from __future__ import annotations

from .mqtt_mini import MiniMQTT


def make_client(cfg: dict, client_id: str, keepalive: int = 45) -> MiniMQTT:
    client = MiniMQTT(client_id, keepalive=keepalive)
    client.tls = bool(cfg.get("tls"))
    if cfg.get("username"):
        client.set_auth(cfg["username"], cfg.get("password"))
    return client
