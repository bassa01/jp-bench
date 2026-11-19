import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from jpbench.adapters import (
    AnthropicMessagesAdapter,
    HTTPAdapter,
    OpenAICompatibleAdapter,
)

SECRET = "sk-test-FAKE-SECRET-42"


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        return

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
        if self.path == "/chat/completions":
            ok = self.headers.get("Authorization") == f"Bearer {SECRET}"
            payload = {"choices": [{"message": {"content": body["messages"][0]["content"][:5] if ok else "denied"}}]}
            self._send(200 if ok else 401, payload)
        elif self.path == "/v1/messages":
            ok = self.headers.get("x-api-key") == SECRET
            self._send(200, {"content": [{"type": "text", "text": "anthropic-ok" if ok else "denied"}]})
        elif self.path == "/boom":
            self._send(500, {"error": SECRET})
        else:
            self._send(404, {})

    def _send(self, status, payload):
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


@pytest.fixture(scope="module")
def base_url():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def test_openai_compatible_adapter_round_trip(base_url):
    adapter = OpenAICompatibleAdapter(base_url, "m", SECRET)
    assert adapter.complete("hello world") == "hello"


def test_anthropic_adapter_round_trip(base_url):
    adapter = AnthropicMessagesAdapter(base_url, "m", SECRET)
    assert adapter.complete("x") == "anthropic-ok"


def test_errors_never_contain_the_key(base_url):
    adapter = OpenAICompatibleAdapter(base_url + "/boom", "m", SECRET)
    with pytest.raises(RuntimeError) as exc:
        adapter.complete("x")
    assert SECRET not in str(exc.value)


def test_plain_http_to_remote_host_is_refused():
    with pytest.raises(ValueError, match="must be https"):
        HTTPAdapter("http://example.com", "m", SECRET)


def test_missing_key_gives_a_clear_message(monkeypatch):
    monkeypatch.delenv("JPBENCH_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="set JPBENCH_API_KEY"):
        OpenAICompatibleAdapter.from_env()


def test_from_env_reads_base_url_model_and_key(monkeypatch, base_url):
    monkeypatch.setenv("JPBENCH_API_KEY", SECRET)
    monkeypatch.setenv("JPBENCH_BASE_URL", base_url)
    monkeypatch.setenv("JPBENCH_MODEL", "m")
    adapter = OpenAICompatibleAdapter.from_env()
    assert adapter.complete("abc") == "abc"
