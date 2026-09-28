"""A tiny, dependency-free MQTT 3.1.1 client.

Only what MADRATIF needs: CONNECT (with optional will / auth / TLS), SUBSCRIBE,
PUBLISH (QoS 0/1, retain), receiving PUBLISH, keepalive pings, and automatic
reconnect. Pure standard library so the app runs on a portable Python with no
pip install at all.
"""

from __future__ import annotations

import socket
import ssl
import struct
import threading
import time

# packet types
_CONNECT = 0x10
_CONNACK = 2
_PUBLISH = 3
_PUBACK = 0x40
_SUBSCRIBE = 0x82
_SUBACK = 9
_PINGREQ = b"\xc0\x00"
_PINGRESP = 13
_DISCONNECT = b"\xe0\x00"


def _mbstr(text: str) -> bytes:
    raw = text.encode("utf-8")
    return struct.pack("!H", len(raw)) + raw


def _encode_len(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n % 128
        n //= 128
        if n > 0:
            b |= 0x80
        out.append(b)
        if n == 0:
            break
    return bytes(out)


class MiniMQTT:
    def __init__(self, client_id: str, keepalive: int = 45):
        self.client_id = client_id
        self.keepalive = keepalive
        self.host = None
        self.port = 1883
        self.tls = False
        self.username = None
        self.password = None
        self.will = None  # (topic, payload_bytes, qos, retain)

        self.on_connect = None  # called as on_connect(self) after CONNACK
        self.on_message = None  # called as on_message(topic:str, payload:bytes)

        self._sock = None
        self._lock = threading.Lock()
        self._pid = 0
        self._stop = False
        self._connected = False

    # ---- configuration -------------------------------------------------
    def set_auth(self, username, password):
        self.username = username or None
        self.password = (password or None) if username else None

    def set_will(self, topic, payload, qos=0, retain=False):
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        self.will = (topic, payload, qos, retain)

    # ---- low level -----------------------------------------------------
    def _next_pid(self) -> int:
        self._pid = (self._pid % 65535) + 1
        return self._pid

    def _send(self, data: bytes):
        with self._lock:
            if self._sock is None:
                raise ConnectionError("not connected")
            self._sock.sendall(data)

    def _packet(self, first_byte: int, body: bytes) -> bytes:
        return bytes([first_byte]) + _encode_len(len(body)) + body

    def _read_exact(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = self._sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("socket closed by broker")
            buf += chunk
        return buf

    def _read_packet(self):
        b1 = self._read_exact(1)[0]
        mult = 1
        remaining = 0
        while True:
            b = self._read_exact(1)[0]
            remaining += (b & 0x7F) * mult
            if not (b & 0x80):
                break
            mult *= 128
        payload = self._read_exact(remaining) if remaining else b""
        return b1, payload

    def _build_connect(self) -> bytes:
        flags = 0x02  # clean session
        if self.username:
            flags |= 0x80
            if self.password:
                flags |= 0x40
        payload = _mbstr(self.client_id)
        if self.will:
            wt, wp, wq, wr = self.will
            flags |= 0x04 | ((wq & 0x03) << 3) | (0x20 if wr else 0)
            payload += _mbstr(wt)
            payload += struct.pack("!H", len(wp)) + wp
        if self.username:
            payload += _mbstr(self.username)
            if self.password:
                pw = self.password.encode("utf-8")
                payload += struct.pack("!H", len(pw)) + pw
        vh = _mbstr("MQTT") + bytes([0x04]) + bytes([flags]) + struct.pack("!H", self.keepalive)
        return self._packet(_CONNECT, vh + payload)

    def _open(self):
        raw = socket.create_connection((self.host, self.port), timeout=20)
        if self.tls:
            ctx = ssl.create_default_context()
            raw = ctx.wrap_socket(raw, server_hostname=self.host)
        self._sock = raw
        self._sock.settimeout(20)
        self._send(self._build_connect())
        b1, payload = self._read_packet()
        if (b1 >> 4) != _CONNACK or len(payload) < 2 or payload[1] != 0:
            code = payload[1] if len(payload) > 1 else "?"
            raise ConnectionError(f"CONNECT ditolak broker (code {code})")
        self._sock.settimeout(None)
        self._connected = True

    # ---- public API ----------------------------------------------------
    def connect(self, host, port, keepalive=None):
        self.host = host
        self.port = int(port)
        if keepalive:
            self.keepalive = keepalive
        self._open()

    def subscribe(self, topic, qos=1):
        pid = self._next_pid()
        body = struct.pack("!H", pid) + _mbstr(topic) + bytes([qos])
        self._send(self._packet(_SUBSCRIBE, body))

    def publish(self, topic, payload, qos=0, retain=False):
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        first = 0x30 | (qos << 1) | (1 if retain else 0)
        vh = _mbstr(topic)
        if qos > 0:
            vh += struct.pack("!H", self._next_pid())
        self._send(self._packet(first, vh + payload))

    def _ping_loop(self):
        interval = max(5, int(self.keepalive * 0.6))
        while not self._stop and self._connected:
            for _ in range(interval * 2):
                if self._stop or not self._connected:
                    return
                time.sleep(0.5)
            try:
                self._send(_PINGREQ)
            except Exception:
                return

    def _read_loop(self):
        while not self._stop:
            b1, payload = self._read_packet()
            ptype = b1 >> 4
            if ptype == _PUBLISH:
                self._dispatch_publish(b1, payload)
            # CONNACK / SUBACK / PUBACK / PINGRESP -> nothing to do

    def _dispatch_publish(self, b1, payload):
        qos = (b1 >> 1) & 0x03
        tlen = struct.unpack("!H", payload[:2])[0]
        topic = payload[2:2 + tlen].decode("utf-8", "replace")
        idx = 2 + tlen
        if qos > 0:
            pid = struct.unpack("!H", payload[idx:idx + 2])[0]
            idx += 2
            try:
                self._send(bytes([_PUBACK]) + _encode_len(2) + struct.pack("!H", pid))
            except Exception:
                pass
        msg = payload[idx:]
        if self.on_message:
            try:
                self.on_message(topic, msg)
            except Exception:
                pass

    def loop_forever(self):
        while not self._stop:
            try:
                if not self._connected:
                    self._open()
                if self.on_connect:
                    self.on_connect(self)
                threading.Thread(target=self._ping_loop, daemon=True).start()
                self._read_loop()
            except Exception:
                self._connected = False
                try:
                    if self._sock:
                        self._sock.close()
                except Exception:
                    pass
                self._sock = None
                if self._stop:
                    break
                time.sleep(3)  # backoff before reconnect

    def loop_start(self):
        threading.Thread(target=self.loop_forever, daemon=True).start()

    def loop_stop(self):
        self._stop = True

    def disconnect(self):
        self._stop = True
        try:
            self._send(_DISCONNECT)
        except Exception:
            pass
        try:
            if self._sock:
                self._sock.close()
        except Exception:
            pass
        self._connected = False
        self._sock = None
