"""RenderResult — rich output from InstructVault.render().

Subclasses ``list`` so it is a drop-in replacement for the previous
``List[PromptMessage]`` return type: every list operation (iteration,
indexing, ``len()``, ``isinstance(x, list)``, ``.append``, slicing, unpacking)
keeps working, while the model metadata and provider adapter methods are
available as attributes/methods on the same object.
"""
from __future__ import annotations

from typing import Any

from .spec import PromptMessage


class RenderResult(list[PromptMessage]):
    """Returned by ``InstructVault.render()``.

    A ``list`` of :class:`PromptMessage` that additionally carries the model
    identity declared in the prompt spec, so applications always know what
    model a prompt was designed for.

    Attributes:
        model:        Model name declared in the prompt spec (e.g. ``"gpt-4o"``).
        provider:     Provider declared in the prompt spec (e.g. ``"openai"``).
        temperature:  Sampling temperature from the prompt spec.
        top_p:        Top-p from the prompt spec.
        max_tokens:   Max tokens from the prompt spec.
        prompt_name:  ``name`` field of the PromptSpec.
        prompt_path:  File path / bundle key used to load the prompt.
        ref:          Git ref used at render time (``None`` = worktree).
        messages:     Alias for the list itself (kept for explicitness).
    """

    def __init__(
        self,
        messages: list[PromptMessage],
        *,
        model: str | None = None,
        provider: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
        prompt_name: str = "",
        prompt_path: str = "",
        ref: str | None = None,
    ) -> None:
        super().__init__(messages)
        self.model = model
        self.provider = provider
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.prompt_name = prompt_name
        self.prompt_path = prompt_path
        self.ref = ref

    @property
    def messages(self) -> list[PromptMessage]:
        """The rendered messages (alias for ``list(self)``)."""
        return list(self)

    def __repr__(self) -> str:
        model_str = f"model={self.model!r}, " if self.model else ""
        return (
            f"RenderResult({model_str}prompt={self.prompt_name!r}, "
            f"messages={len(self)})"
        )

    # ------------------------------------------------------------------
    # Provider adapters
    # ------------------------------------------------------------------

    def to_openai(self) -> dict[str, Any]:
        """Return kwargs ready for ``openai.chat.completions.create(**result.to_openai())``.

        Only includes keys that are set in the prompt spec, so callers can
        override anything by unpacking and adding their own values::

            client.chat.completions.create(**{**result.to_openai(), "stream": True})
        """
        kwargs: dict[str, Any] = {
            "messages": [{"role": m.role, "content": m.content} for m in self],
        }
        if self.model:
            kwargs["model"] = self.model
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        if self.top_p is not None:
            kwargs["top_p"] = self.top_p
        if self.max_tokens is not None:
            kwargs["max_tokens"] = self.max_tokens
        return kwargs

    def to_anthropic(self) -> dict[str, Any]:
        """Return kwargs ready for ``anthropic.messages.create(**result.to_anthropic())``.

        System messages are merged into the ``system`` key; all other roles go
        into ``messages`` as Anthropic expects.
        """
        system_parts = [m.content for m in self if m.role == "system"]
        chat_msgs = [
            {"role": m.role, "content": m.content}
            for m in self
            if m.role != "system"
        ]
        kwargs: dict[str, Any] = {"messages": chat_msgs}
        if system_parts:
            kwargs["system"] = "\n\n".join(system_parts)
        if self.model:
            kwargs["model"] = self.model
        if self.max_tokens is not None:
            kwargs["max_tokens"] = self.max_tokens
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        return kwargs

    def to_litellm(self) -> dict[str, Any]:
        """Return kwargs for LiteLLM's ``completion()`` — works with 100+ models.

        LiteLLM uses the OpenAI message format but prefixes the model with the
        provider when routing (e.g. ``"anthropic/claude-3-5-sonnet-20241022"``).
        If ``provider`` is set in the spec and ``model`` does not already contain
        a slash, the two are joined automatically.
        """
        kwargs = self.to_openai()
        if self.model and self.provider and "/" not in self.model:
            kwargs["model"] = f"{self.provider}/{self.model}"
        return kwargs

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict for logging, tracing, or observability pipelines."""
        return {
            "prompt_name": self.prompt_name,
            "prompt_path": self.prompt_path,
            "ref": self.ref,
            "model": self.model,
            "provider": self.provider,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "messages": [{"role": m.role, "content": m.content} for m in self],
        }
