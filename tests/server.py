"""A local HTTP server for testing the client over a real connection.

These tests run the real client (nothing stubbed) against this server, so we
see exactly what goes over the wire.

`handler` receives the recorded request and its index, and returns a dict
describing the response:
    {"status": 200, "headers": {}, "json": ..., "body": b"...", "delay": 0.0}
"""

from __future__ import annotations

import json as json_lib
import threading
import time
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


RATE_LIMIT_HEADERS = {
    "x-ratelimit-limit": "10",
    "x-ratelimit-interval-ms": "1000",
}


@dataclass
class RecordedRequest:
    method: str
    path: str
    headers: Mapping[str, str]
    body: bytes
    received_at: float
    responded_at: float | None = None

    @property
    def json(self) -> Any:
        return json_lib.loads(self.body)

    def multipart_parts(self) -> dict[str, MultipartPart]:
        """The parts of a multipart body, by field name."""
        content_type = self.headers["content-type"]
        assert content_type.startswith("multipart/form-data; boundary="), content_type
        boundary = content_type.split("boundary=", 1)[1].encode()
        parts: dict[str, MultipartPart] = {}
        for raw in self.body.split(b"--" + boundary):
            # Each part is "\r\n<headers>\r\n\r\n<body>\r\n"; the last is "--\r\n"
            if raw in (b"", b"--\r\n", b"--"):
                continue
            raw = raw.removeprefix(b"\r\n").removesuffix(b"\r\n")
            head, _, body = raw.partition(b"\r\n\r\n")
            headers: dict[str, str] = {}
            for line in head.decode("latin1").split("\r\n"):
                name, _, value = line.partition(":")
                headers[name.strip().lower()] = value.strip()
            disposition = headers.get("content-disposition", "")
            name = _disposition_param(disposition, "name")
            parts[name] = MultipartPart(
                name=name,
                filename=_disposition_param(disposition, "filename"),
                content_type=headers.get("content-type"),
                body=body,
            )
        return parts


@dataclass
class MultipartPart:
    name: str
    filename: str | None
    content_type: str | None
    body: bytes

    @property
    def json(self) -> Any:
        return json_lib.loads(self.body)


@dataclass
class Server:
    base_url: str
    requests: list[RecordedRequest] = field(default_factory=list)


Handler = Callable[[RecordedRequest, int], Mapping[str, Any] | None]


@contextmanager
def start_server(handler: Handler | None = None):
    """Start a server on a free port, yielding a `Server` with its base URL and the requests it got."""
    server = Server(base_url="")
    respond = handler or (lambda request, index: {"json": {"data": {}}})

    class RequestHandler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args: Any) -> None:
            pass

        def handle_one(self) -> None:
            length = int(self.headers.get("content-length") or 0)
            body = self.rfile.read(length) if length else b""
            recorded = RecordedRequest(
                method=self.command,
                path=self.path,
                headers={k.lower(): v for k, v in self.headers.items()},
                body=body,
                received_at=time.monotonic(),
            )
            server.requests.append(recorded)

            response = respond(recorded, len(server.requests) - 1) or {}
            status = response.get("status", 200)
            headers = {**RATE_LIMIT_HEADERS, **response.get("headers", {})}
            if response.get("delay"):
                time.sleep(response["delay"])

            if "json" in response:
                payload = json_lib.dumps(response["json"]).encode()
                headers.setdefault("content-type", "application/json")
            else:
                payload = response.get("body", b"")
                if isinstance(payload, str):
                    payload = payload.encode()

            self.send_response(status)
            for name, value in headers.items():
                self.send_header(name, value)
            self.send_header("content-length", str(len(payload)))
            self.end_headers()
            recorded.responded_at = time.monotonic()
            self.wfile.write(payload)

        do_GET = do_POST = do_PUT = do_DELETE = handle_one

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), RequestHandler)
    httpd.daemon_threads = True
    server.base_url = f"http://127.0.0.1:{httpd.server_port}"
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        httpd.shutdown()
        httpd.server_close()


def _disposition_param(disposition: str, param: str) -> str:
    marker = f'{param}="'
    if marker not in disposition:
        return ""
    return disposition.split(marker, 1)[1].split('"', 1)[0]
