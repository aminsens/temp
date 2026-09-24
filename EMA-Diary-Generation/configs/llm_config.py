"""
LLM configuration for local llama.cpp server.
Qwen3.5-27B on 2x RTX 5090.
"""

import json
from urllib.request import Request, urlopen
from typing import Optional


# ──────────────────────────────────────────────────────────────────────
# Server Configuration
# ──────────────────────────────────────────────────────────────────────

BASE_URL = "http://127.0.0.1:8022"
MAX_TOKENS = 8192  # enough for diary generation

# Qwen3.5 sampling presets
PRESETS = {
    "thinking_general": {
        "temperature": 1.0,
        "top_p": 0.95,
        "top_k": 20,
        "min_p": 0.0,
        "presence_penalty": 1.5,
        "repetition_penalty": 1.0,
    },
    "thinking_coding": {
        "temperature": 0.6,
        "top_p": 0.95,
        "top_k": 20,
        "min_p": 0.0,
        "presence_penalty": 0.0,
        "repetition_penalty": 1.0,
    },
    "json_output": {
        "temperature": 0.3,  # low temp for deterministic JSON
        "top_p": 0.8,
        "top_k": 20,
        "min_p": 0.0,
        "presence_penalty": 1.5,
        "repetition_penalty": 1.0,
    },
}


# ──────────────────────────────────────────────────────────────────────
# LLM Client
# ──────────────────────────────────────────────────────────────────────

class LlamaClient:
    """Client for local llama.cpp server."""

    def __init__(self, base_url: str = BASE_URL, max_tokens: int = MAX_TOKENS):
        self.base_url = base_url
        self.max_tokens = max_tokens
        self.model = self._discover_model()

    def _discover_model(self) -> str:
        """Get model ID from running server."""
        req = Request(f"{self.base_url}/v1/models", method="GET")
        with urlopen(req, timeout=10) as resp:
            models = json.loads(resp.read().decode())
        model_id = models["data"][0]["id"]
        print(f"Connected to: {model_id}")
        return model_id

    def chat(
        self,
        messages: list[dict],
        preset: str = "json_output",
        max_tokens: Optional[int] = None,
        timeout: int = 600,
        disable_thinking: bool = True,
    ) -> str:
        """Send chat completion request."""
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            **PRESETS.get(preset, PRESETS["json_output"]),
        }

        # Disable thinking for structured output
        if disable_thinking:
            payload["chat_template_kwargs"] = {"enable_thinking": False}

        req = Request(
            f"{self.base_url}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=timeout) as resp:
            out = json.loads(resp.read().decode())

        msg = out["choices"][0]["message"]

        # If thinking mode leaked through, content might be in reasoning_content
        content = msg.get("content", "")
        if not content and "reasoning_content" in msg:
            content = msg["reasoning_content"]

        # Strip any leftover <analysis>...</analysis> tags
        if "<analysis>" in content:
            import re
            content = re.sub(r'<analysis>.*?</analysis>', '', content, flags=re.DOTALL).strip()
        if "<thinking>" in content:
            import re
            content = re.sub(r'<thinking>.*?</thinking>', '', content, flags=re.DOTALL).strip()

        return content

    def generate(
        self,
        system: str,
        user: str,
        preset: str = "json_output",
        max_tokens: Optional[int] = None,
        timeout: int = 600,
    ) -> str:
        """Simplified generation with system + user messages."""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        return self.chat(messages, preset, max_tokens, timeout)


# ──────────────────────────────────────────────────────────────────────
# Convenience functions
# ──────────────────────────────────────────────────────────────────────

_client = None

def get_client() -> LlamaClient:
    """Get or create singleton client."""
    global _client
    if _client is None:
        _client = LlamaClient()
    return _client


def ask(system: str, user: str, preset: str = "json_output", max_tokens: int = 8192) -> str:
    """Quick generation function."""
    client = get_client()
    return client.generate(system, user, preset, max_tokens)
