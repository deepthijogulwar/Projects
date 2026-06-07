"""The core chat logic: a small, easy-to-read ChatSession class.

This class is provider-agnostic — it only needs a `client` that has
`client.chat.completions.create(...)`. That makes it simple to unit-test with a
fake client (see tests/test_chat.py) without any network calls or API keys.
"""

from __future__ import annotations

from collections.abc import Iterator


class ChatSession:
    """Holds one conversation and talks to the model."""

    def __init__(
        self,
        client,
        model: str,
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 800,
    ) -> None:
        self.client = client
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        # The "system" message defines the assistant's persona and always stays first.
        self.messages: list[dict] = [{"role": "system", "content": system_prompt}]

    def stream(self, user_message: str) -> Iterator[str]:
        """Send a message and yield the reply piece-by-piece (streaming)."""
        self.messages.append({"role": "user", "content": user_message})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=True,
        )

        collected: list[str] = []
        for chunk in response:
            # Some streamed chunks carry no text (e.g. role markers) — skip those safely.
            if not getattr(chunk, "choices", None):
                continue
            delta = chunk.choices[0].delta
            token = getattr(delta, "content", None)
            if token:
                collected.append(token)
                yield token

        # Save the full assistant reply so the model "remembers" it on the next turn.
        self.messages.append({"role": "assistant", "content": "".join(collected)})

    def send(self, user_message: str) -> str:
        """Send a message and return the whole reply as a single string."""
        return "".join(self.stream(user_message))

    def reset(self) -> None:
        """Forget the conversation but keep the current persona."""
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def set_system(self, system_prompt: str) -> None:
        """Change the assistant's persona and start a fresh conversation."""
        self.system_prompt = system_prompt
        self.reset()
