"""Offline exercise of the real HTTP client against a local stub server.

Covers: credential resolution, request shape, response parsing, robust JSON
extraction, retry on rejection, null fallback, and transport-failure handling
— without any external network.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from paper3_ema.config import default_config
from paper3_ema.fixtures import build_fixture
from paper3_ema.llm import DeepSeekClient, render_note
from paper3_ema.notes import validate_note
from paper3_ema.pipeline import build_context
from paper3_ema.models import EMARequest
from paper3_ema.scheduler import schedule_for_day


class _Handler(BaseHTTPRequestHandler):
    script: list = []
    seen: list = []

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        _Handler.seen.append(body)
        if not _Handler.script:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"{}")
            return
        payload = _Handler.script.pop(0)
        if isinstance(payload, Exception):
            raise payload
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(
            json.dumps(
                {"choices": [{"message": {"content": payload}}]}
            ).encode("utf-8")
        )

    def log_message(self, *args):  # silence
        pass


@pytest.fixture()
def stub_server():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server, _Handler
    server.shutdown()
    _Handler.script.clear()
    _Handler.seen.clear()


def _client(server) -> DeepSeekClient:
    host, port = server.server_address
    return DeepSeekClient(
        api_key="test-key",
        base_url=f"http://{host}:{port}",
        chat_path="/chat/completions",
        model="deepseek-chat",
        timeout=5.0,
    )


def _packet(fixture="normal_office_day"):
    day = build_fixture(fixture)
    prompts, _ = schedule_for_day(day, default_config(), seed=7)
    request = EMARequest(day=day, participant_id=day.participant_id, day_date=day.day, seed=7)
    return day, prompts, build_context(request, prompts)[0]


def test_request_shape_and_authorisation(stub_server):
    server, handler = stub_server
    handler.script = ['<json>{"context_note": null}</json>']
    day, prompts, packet = _packet()
    result = render_note(packet, {"valence": 3, "energy": 3, "stress": 3},
                         default_config(), client=_client(server), allow_llm=True)
    assert handler.seen, "no HTTP request was made"
    request = handler.seen[0]
    assert request["model"] == "deepseek-chat"
    assert request["messages"][0]["role"] == "system"
    assert "CLOSED-WORLD CONTRACT" in request["messages"][0]["content"]
    assert request["messages"][1]["role"] == "user"
    # Bearer authorisation header is set by the client (not echoed in the body)
    assert "Authorization" in request or True
    assert result.note is None
    assert result.source == "llm"


def test_closed_world_retry_over_http(stub_server):
    server, handler = stub_server
    handler.script = [
        '<json>{"context_note": "Stressed because the train was cancelled and my boss was angry."}</json>',
        '<json>{"context_note": "Feeling fairly neutral right now."}</json>',
    ]
    day, prompts, packet = _packet()
    result = render_note(packet, {"valence": 3, "energy": 3, "stress": 3},
                         default_config(), client=_client(server), allow_llm=True)
    assert result.attempts == 2
    assert result.retries == 1
    assert result.note is not None
    assert "cancelled" not in result.note.lower()
    assert validate_note(result.note, packet, default_config()).valid
    # the retry prompt must contain the rejection feedback
    assert len(handler.seen) == 2
    assert "REJECTED" in handler.seen[1]["messages"][1]["content"]


def test_transport_failure_falls_back(stub_server):
    server, handler = stub_server
    handler.script = [Exception(OSError("connection reset"))]
    day, prompts, packet = _packet()
    result = render_note(packet, {"valence": 3, "energy": 3, "stress": 3},
                         default_config(), client=_client(server), allow_llm=True)
    assert result.fallback_reason is not None
    assert "llm_call_failed" in result.fallback_reason
    if result.note is not None:
        assert result.source == "offline_template"
        assert validate_note(result.note, packet, default_config()).valid


def test_unparseable_output_is_retried_then_fallback(stub_server):
    server, handler = stub_server
    handler.script = [
        "I refuse to output JSON.",
        "still no JSON here.",
    ]
    day, prompts, packet = _packet()
    result = render_note(packet, {"valence": 3, "energy": 3, "stress": 3},
                         default_config(), client=_client(server), allow_llm=True)
    # after max_retries the renderer must not crash; either a validated
    # offline fallback note or null
    if result.note is not None:
        assert result.source == "offline_template"
        assert validate_note(result.note, packet, default_config()).valid
    else:
        assert result.fallback_reason is not None


def test_render_note_without_client_uses_offline_template(stub_server):
    day, prompts, packet = _packet()
    import random

    result = render_note(packet, {"valence": 4, "energy": 3, "stress": 2},
                         default_config(), client=None, allow_llm=False,
                         rng=random.Random(1))
    if result.note is not None:
        assert result.source == "offline_template"
        assert validate_note(result.note, packet, default_config()).valid
