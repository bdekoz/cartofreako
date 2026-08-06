#!/usr/bin/env python3
"""Serve a WASM smoke page and verify it through Chrome DevTools Protocol."""

from __future__ import annotations

import argparse
import base64
import functools
import http.server
import json
import os
import pathlib
import shutil
import socket
import struct
import subprocess
import tempfile
import threading
import time
import urllib.parse
import urllib.request


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".mjs": "text/javascript",
        ".wasm": "application/wasm",
    }

    def log_message(self, _format: str, *_args: object) -> None:
        pass


def read_exact(stream: socket.socket, size: int) -> bytes:
    result = b""
    while len(result) < size:
        chunk = stream.recv(size - len(result))
        if not chunk:
            raise RuntimeError("Chrome closed the DevTools WebSocket")
        result += chunk
    return result


class DevToolsSocket:
    def __init__(self, url: str) -> None:
        parsed = urllib.parse.urlparse(url)
        self.socket = socket.create_connection((parsed.hostname, parsed.port), timeout=10)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {parsed.path} HTTP/1.1\r\n"
            f"Host: {parsed.hostname}:{parsed.port}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        self.socket.sendall(request.encode("ascii"))
        response = b""
        while b"\r\n\r\n" not in response:
            response += read_exact(self.socket, 1)
        if not response.startswith(b"HTTP/1.1 101"):
            raise RuntimeError(f"DevTools WebSocket handshake failed: {response!r}")
        self.next_id = 1

    def send_json(self, value: dict[str, object]) -> None:
        payload = json.dumps(value, separators=(",", ":")).encode("utf-8")
        mask = os.urandom(4)
        length = len(payload)
        header = bytearray([0x81])
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))
        header.extend(mask)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.socket.sendall(header + masked)

    def receive_json(self) -> dict[str, object]:
        while True:
            first, second = read_exact(self.socket, 2)
            opcode = first & 0x0F
            length = second & 0x7F
            if length == 126:
                length = struct.unpack("!H", read_exact(self.socket, 2))[0]
            elif length == 127:
                length = struct.unpack("!Q", read_exact(self.socket, 8))[0]
            if second & 0x80:
                mask = read_exact(self.socket, 4)
            else:
                mask = None
            payload = read_exact(self.socket, length)
            if mask:
                payload = bytes(
                    byte ^ mask[index % 4] for index, byte in enumerate(payload)
                )
            if opcode == 0x8:
                raise RuntimeError("Chrome closed the DevTools session")
            if opcode == 0x9:
                self.socket.sendall(bytes([0x8A, len(payload)]) + payload)
                continue
            if opcode == 0x1:
                return json.loads(payload)

    def call(self, method: str, params: dict[str, object] | None = None) -> dict[str, object]:
        identifier = self.next_id
        self.next_id += 1
        message: dict[str, object] = {"id": identifier, "method": method}
        if params is not None:
            message["params"] = params
        self.send_json(message)
        while True:
            response = self.receive_json()
            if response.get("id") == identifier:
                if "error" in response:
                    raise RuntimeError(f"DevTools command failed: {response['error']}")
                return response.get("result", {})

    def close(self) -> None:
        self.socket.close()


def page_value(devtools: DevToolsSocket, expression: str) -> object:
    response = devtools.call(
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True},
    )
    remote = response.get("result", {})
    if "exceptionDetails" in response:
        raise RuntimeError(str(response["exceptionDetails"]))
    return remote.get("value")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("html", type=pathlib.Path)
    parser.add_argument("--browser", default="")
    args = parser.parse_args()

    html = args.html.resolve()
    if not html.is_file():
        raise SystemExit(f"missing browser smoke page: {html}")
    browser = args.browser or shutil.which("google-chrome") or shutil.which("chromium")
    if not browser:
        raise SystemExit("no Chrome/Chromium browser found")

    handler = functools.partial(QuietHandler, directory=str(html.parent))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    chrome: subprocess.Popen[str] | None = None
    devtools: DevToolsSocket | None = None
    try:
        url = f"http://127.0.0.1:{server.server_port}/{html.name}"
        with tempfile.TemporaryDirectory(prefix="cartofreako-chrome-") as profile:
            chrome = subprocess.Popen(
                [
                    browser,
                    "--headless=new",
                    "--no-sandbox",
                    "--disable-gpu",
                    "--disable-dev-shm-usage",
                    "--remote-debugging-port=0",
                    f"--user-data-dir={profile}",
                    url,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            port_file = pathlib.Path(profile, "DevToolsActivePort")
            deadline = time.monotonic() + 15
            while not port_file.is_file() and time.monotonic() < deadline:
                if chrome.poll() is not None:
                    raise RuntimeError("Chrome exited before opening DevTools")
                time.sleep(0.05)
            if not port_file.is_file():
                raise RuntimeError("Chrome did not publish a DevTools port")
            port = int(port_file.read_text(encoding="utf-8").splitlines()[0])
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/json/list", timeout=5
            ) as response:
                targets = json.load(response)
            page = next(target for target in targets if target.get("type") == "page")
            devtools = DevToolsSocket(page["webSocketDebuggerUrl"])
            devtools.call("Runtime.enable")

            deadline = time.monotonic() + 30
            status = "running"
            while status == "running" and time.monotonic() < deadline:
                status = page_value(
                    devtools,
                    "document.querySelector('#result')?.dataset.status ?? 'running'",
                )
                if status == "running":
                    time.sleep(0.1)
            text = page_value(
                devtools,
                "document.querySelector('#result')?.textContent ?? 'missing result'",
            )
            if status != "pass":
                raise RuntimeError(f"browser smoke {status}: {text}")
            print(text)
    finally:
        if devtools is not None:
            devtools.close()
        if chrome is not None and chrome.poll() is None:
            chrome.terminate()
            try:
                chrome.wait(timeout=5)
            except subprocess.TimeoutExpired:
                chrome.kill()
                chrome.wait(timeout=5)
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
