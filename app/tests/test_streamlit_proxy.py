import asyncio

import pytest

from student_attrition_risk.streamlit_host import StreamlitProxy


class FakeUpstream:
    def __init__(self) -> None:
        self.sent: list[str | bytes] = []
        self.closed = asyncio.Event()
        self.subprotocol = "streamlit"

    async def send(self, message: str | bytes) -> None:
        self.sent.append(message)

    async def close(self, code: int = 1000) -> None:
        self.close_code = code
        self.closed.set()

    def __aiter__(self):
        return self._messages()

    async def _messages(self):
        yield b"upstream-bytes"
        await self.closed.wait()


class FakeConnect:
    def __init__(self, upstream: FakeUpstream) -> None:
        self.upstream = upstream
        self.url = None
        self.headers = None
        self.subprotocols = None

    async def __aenter__(self) -> FakeUpstream:
        return self.upstream

    async def __aexit__(self, *_args: object) -> None:
        return None


@pytest.mark.anyio
async def test_websocket_proxy_forwards_frames_headers_query_and_disconnect(monkeypatch):
    upstream = FakeUpstream()
    connector = FakeConnect(upstream)

    def connect(url, *, additional_headers, subprotocols):
        connector.url = url
        connector.headers = additional_headers
        connector.subprotocols = subprotocols
        return connector

    monkeypatch.setattr("student_attrition_risk.streamlit_host.websockets.connect", connect)
    incoming = iter(
        [
            {"type": "websocket.connect"},
            {"type": "websocket.receive", "text": "client-text"},
            {"type": "websocket.disconnect", "code": 1001},
        ]
    )
    sent: list[dict[str, object]] = []

    async def receive():
        return next(incoming)

    async def send(message):
        sent.append(message)

    await StreamlitProxy(8501)(
        {
            "type": "websocket",
            "path": "/ui/_stcore/stream",
            "query_string": b"session=abc",
            "headers": [
                (b"cookie", b"session=abc"),
                (b"origin", b"http://localhost"),
                (b"sec-websocket-protocol", b"streamlit, other"),
            ],
        },
        receive,
        send,
    )

    assert connector.url == "ws://127.0.0.1:8501/ui/_stcore/stream?session=abc"
    assert ("cookie", "session=abc") in connector.headers
    assert connector.subprotocols == ["streamlit", "other"]
    assert upstream.sent == ["client-text"]
    assert upstream.close_code == 1001
    assert {message.get("bytes") for message in sent if message["type"] == "websocket.send"} == {
        b"upstream-bytes"
    }
    assert sent[0] == {"type": "websocket.accept", "subprotocol": "streamlit"}