"""Small factory that builds a configured paho-mqtt (v2) client."""

from __future__ import annotations

import ssl

import paho.mqtt.client as mqtt


def make_client(cfg: dict, client_id: str, clean_session: bool = True):
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=client_id,
        clean_session=clean_session,
    )
    if cfg.get("username"):
        client.username_pw_set(cfg["username"], cfg.get("password") or None)
    if cfg.get("tls"):
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    return client
