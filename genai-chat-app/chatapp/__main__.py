"""Interactive command-line chat.  Run with:  python -m chatapp

Reads your settings from .env, builds the right client for your chosen provider,
and starts a streaming chat loop.
"""
from __future__ import annotations

from chatapp.config import load_settings, ConfigError
from chatapp.client import build_client
from chatapp.chat import ChatSession


def main() -> None:
    try:
        settings = load_settings()
    except ConfigError as exc:
        print("Configuration problem:\n" + str(exc))
        return

    client, model = build_client(settings)
    session = ChatSession(
        client,
        model,
        settings.system_prompt,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
    )

    print(f"Chatting via {settings.provider} ({model}).  Commands: 'reset' clears history, 'exit' quits.\n")
    while True:
        try:
            user = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user:
            continue
        if user.lower() in {"exit", "quit"}:
            break
        if user.lower() == "reset":
            session.reset()
            print("(history cleared)\n")
            continue
        print("AI: ", end="", flush=True)
        for token in session.stream(user):
            print(token, end="", flush=True)
        print("\n")


if __name__ == "__main__":
    main()
