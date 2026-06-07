# 🤖 Multi-Provider GenAI Chat App

A clean, beginner-friendly **command-line chat app** that talks to large language models — with **one codebase that works across Azure OpenAI, GitHub Models (free), and OpenAI**. Built around the Microsoft Applied Skills "Azure OpenAI" course.

## ✨ Features
- **Streaming replies** — tokens print as they're generated.
- **Provider-agnostic** — switch between Azure OpenAI / GitHub Models / OpenAI with a single `.env` setting; the chat logic never changes.
- **Conversation memory** — remembers context within a session (`reset` to clear).
- **Clean architecture** — config / client / chat session cleanly separated.
- **Unit-tested** — the core `ChatSession` is tested with a *fake client* (no API key or network needed).
- **Friendly errors** — clear messages tell you exactly which setting is missing.

## 🏗️ Structure
```
chatapp/
  config.py     # loads & validates settings from .env (provider, keys, model)
  client.py     # builds the right API client for the chosen provider
  chat.py       # ChatSession: streaming, memory, persona
  __main__.py   # the interactive CLI
tests/
  test_chat.py  # unit tests using a fake client (no network)
```

## ▶️ Run it
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

copy .env.example .env      # then add a key — GitHub Models is free & easiest
python -m chatapp
```
Type a message to chat; `reset` clears history, `exit` quits.

## 🔑 Providers (set `PROVIDER` in `.env`)
| Provider | Best for | Needs |
|---|---|---|
| `github` | Free, quickest start | a free GitHub token (no scopes) |
| `azure` | Microsoft Applied Skills | an Azure OpenAI resource |
| `openai` | OpenAI's public API | an OpenAI API key |

## 🧪 Tests
```powershell
pip install pytest
pytest
```

## 🛠️ Tech
Python · OpenAI SDK · Azure OpenAI · python-dotenv · streaming chat completions
