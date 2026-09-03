"""Lifecycle and lightweight HTTP/WebSocket proxy for the Streamlit child."""

import asyncio
import contextlib
import os
import subprocess
import sys
from collections.abc import Awaitable, Callable
from contextlib import suppress
from typing import Any

import httpx
import websockets
from websockets.exceptions import ConnectionClosed

_HOP_BY_HOP_HEADERS = {
    b"connection",
    b"host",
    b"sec-websocket-accept",
    b"sec-websocket-extensions",
    b"sec-websocket-key",
    b"sec-websocket-protocol",
    b"sec-websocket-version",
    b"upgrade",
}


class StreamlitHost:
    def __init__(self, port: int) -> None:
        self.port = port
        self.process: subprocess.Popen[bytes] | None = None

    def start(self) -> None:
        if self.process and self.process.poll() is None:
            return
        ui_path = os.path.join(os.path.dirname(__file__), "ui.py")
        self.process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", ui_path, "--server.address", "127.0.0.1",
             "--server.port", str(self.port), "--server.headless", "true", "--server.baseUrlPath", "ui",
             "--server.enableCORS", "false", "--server.enableXsrfProtection", "false"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            with contextlib.suppress(subprocess.TimeoutExpired):
                self.process.wait(timeout=5)
        self.process = None


class StreamlitProxy:
    def __init__(self, port: int) -> None:
        self.port = port
        self.target = f"http://127.0.0.1:{port}"

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Awaitable[Any]],
        send: Callable[..., Awaitable[Any]],
    ) -> None:
        if scope["type"] == "websocket":
            await self._proxy_websocket(scope, receive, send)
            return
        if scope["type"] != "http":
            await self._not_supported(send)
            return
        body = b""
        while True:
            message = await receive()
            body += message.get("body", b"")
            if not message.get("more_body"):
                break
        path = scope.get("path") or "/"
        query = scope.get("query_string", b"").decode()
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    scope["method"], f"{self.target}{path}" + (f"?{query}" if query else ""),
                    headers={key.decode(): value.decode() for key, value in scope.get("headers", [])},
                    content=body,
                )
            except httpx.HTTPError:
                await self._not_supported(send, 503)
                return
        excluded_headers = {"content-length", "connection", "transfer-encoding"}
        headers = [
            (key.encode(), value.encode())
            for key, value in response.headers.items()
            if key.lower() not in excluded_headers
        ]
        await send({"type": "http.response.start", "status": response.status_code, "headers": headers})
        await send({"type": "http.response.body", "body": response.content})

    async def _proxy_websocket(
        self,
        scope: dict[str, Any],
        receive: Callable[..., Awaitable[Any]],
        send: Callable[..., Awaitable[Any]],
    ) -> None:
        first_message = await receive()
        if first_message["type"] == "websocket.disconnect":
            return
        path = scope.get("path") or "/"
        query = scope.get("query_string", b"").decode("latin-1")
        upstream_url = f"ws://127.0.0.1:{self.port}{path}"
        if query:
            upstream_url = f"{upstream_url}?{query}"
        headers = [
            (key.decode(), value.decode())
            for key, value in scope.get("headers", [])
            if key.lower() not in _HOP_BY_HOP_HEADERS
        ]
        subprotocols = [
            protocol.strip()
            for key, value in scope.get("headers", [])
            if key.lower() == b"sec-websocket-protocol"
            for protocol in value.decode("latin-1").split(",")
            if protocol.strip()
        ]
        try:
            async with websockets.connect(
                upstream_url,
                additional_headers=headers,
                subprotocols=subprotocols or None,
            ) as upstream:
                accept_message = {"type": "websocket.accept"}
                if upstream.subprotocol:
                    accept_message["subprotocol"] = upstream.subprotocol
                await send(accept_message)

                async def forward_to_upstream() -> None:
                    while True:
                        message = await receive()
                        if message["type"] == "websocket.disconnect":
                            await upstream.close(code=message.get("code", 1000))
                            return
                        if message.get("text") is not None:
                            await upstream.send(message["text"])
                        elif message.get("bytes") is not None:
                            await upstream.send(message["bytes"])

                async def forward_to_client() -> None:
                    async for message in upstream:
                        if isinstance(message, bytes):
                            await send({"type": "websocket.send", "bytes": message})
                        else:
                            await send({"type": "websocket.send", "text": message})

                tasks = [
                    asyncio.create_task(forward_to_upstream()),
                    asyncio.create_task(forward_to_client()),
                ]
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                for task in done:
                    with suppress(Exception):
                        task.result()
        except ConnectionClosed as exc:
            with suppress(Exception):
                await send({"type": "websocket.close", "code": exc.code, "reason": exc.reason})
        except Exception:
            with suppress(Exception):
                await send({"type": "websocket.close", "code": 1011})

    async def _not_supported(self, send: Callable[..., Awaitable[Any]], status: int = 501) -> None:
        await send(
            {"type": "http.response.start", "status": status, "headers": [(b"content-type", b"text/plain")]}
        )
        await send({"type": "http.response.body", "body": b"Streamlit proxy unavailable"})
