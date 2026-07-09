from __future__ import annotations

from collections.abc import Callable

# A provider takes rendered messages + model params and returns the model's reply text.
Provider = Callable[[list[dict[str, str]], dict[str, object]], str]


def _mock_provider(messages: list[dict[str, str]], params: dict[str, object]) -> str:
    """Deterministic provider for tests/CI: echoes the last user message."""
    for m in reversed(messages):
        if m["role"] == "user":
            return m["content"]
    return messages[-1]["content"] if messages else ""


def _openai_provider(messages: list[dict[str, str]], params: dict[str, object]) -> str:
    from openai import OpenAI  # lazy import; only needed when actually used

    client = OpenAI()
    model = str(params.get("model") or "gpt-4o-mini")
    kwargs = {k: params[k] for k in ("temperature", "top_p", "max_tokens") if params.get(k) is not None}
    resp = client.chat.completions.create(model=model, messages=messages, **kwargs)
    return resp.choices[0].message.content or ""


def _ollama_provider(messages: list[dict[str, str]], params: dict[str, object]) -> str:
    from ollama import Client  # lazy import; only needed when actually used

    # Client() defaults host to http://127.0.0.1:11434 and honors OLLAMA_HOST for overrides.
    client = Client()
    model = str(params.get("model") or "llama3.2")
    option_keys = {"temperature": "temperature", "top_p": "top_p", "max_tokens": "num_predict"}
    options = {option_keys[k]: params[k] for k in option_keys if params.get(k) is not None}
    resp = client.chat(model=model, messages=messages, options=options or None)
    return resp.message.content or ""


_PROVIDERS: dict[str, Provider] = {"mock": _mock_provider, "openai": _openai_provider, "ollama": _ollama_provider}


def get_provider(name: str | None) -> Provider | None:
    if not name:
        return None
    if name not in _PROVIDERS:
        raise ValueError(f"Unknown provider '{name}'. Available: {', '.join(sorted(_PROVIDERS))}")
    return _PROVIDERS[name]
