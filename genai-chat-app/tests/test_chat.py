"""Unit tests for ChatSession using a FAKE client — no API key or network needed."""
from chatapp.chat import ChatSession


class _FakeDelta:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.delta = _FakeDelta(content)


class _FakeChunk:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def create(self, **kwargs):
        # Stream back two tokens, regardless of the input.
        return [_FakeChunk("Hello"), _FakeChunk(", world")]


class _FakeChat:
    completions = _FakeCompletions()


class _FakeClient:
    chat = _FakeChat()


def test_send_returns_full_reply():
    session = ChatSession(_FakeClient(), "fake-model", "You are a test.")
    assert session.send("hi") == "Hello, world"
    # The assistant reply is remembered for the next turn.
    assert session.messages[-1] == {"role": "assistant", "content": "Hello, world"}


def test_reset_keeps_persona():
    session = ChatSession(_FakeClient(), "fake-model", "Persona X")
    session.send("hi")
    session.reset()
    assert session.messages == [{"role": "system", "content": "Persona X"}]
