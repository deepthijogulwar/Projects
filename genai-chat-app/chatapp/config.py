"""Load and validate configuration from environment variables (a .env file).

Beginner notes:
- We keep ALL settings in one place so the rest of the app never touches os.environ.
- `PROVIDER` lets you choose where the AI model runs:
    azure  -> Azure OpenAI Service (matches the Microsoft Applied Skills course)
    github -> GitHub Models (FREE, easiest if you don't have Azure yet)
    openai -> OpenAI's public API
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Read the .env file (if present) and load its values into environment variables.
load_dotenv()


class ConfigError(Exception):
    """Raised when a required setting is missing, with a helpful message."""


@dataclass
class Settings:
    """Everything the app needs to talk to a model, gathered in one object."""

    provider: str
    model: str  # the model name (or Azure deployment name) to call
    # Azure-only fields:
    azure_endpoint: str = ""
    azure_api_key: str = ""
    azure_api_version: str = "2024-10-21"
    # github / openai fields:
    api_key: str = ""
    base_url: str = ""
    # Chat behavior (all providers):
    system_prompt: str = "You are a helpful, friendly assistant."
    temperature: float = 0.7
    max_tokens: int = 800


def _require(value: str, name: str, hint: str) -> str:
    """Return `value` if set, otherwise raise a friendly ConfigError."""
    if not value:
        raise ConfigError(
            f"Missing required setting '{name}'.\n"
            f"Fix: open your .env file and set {name}=...\n"
            f"Hint: {hint}"
        )
    return value


def load_settings() -> Settings:
    """Build a Settings object from the environment, validating as we go."""
    provider = os.getenv("PROVIDER", "azure").strip().lower()
    system_prompt = os.getenv("SYSTEM_PROMPT", "You are a helpful, friendly assistant.")
    temperature = float(os.getenv("TEMPERATURE", "0.7"))
    max_tokens = int(os.getenv("MAX_TOKENS", "800"))

    if provider == "azure":
        return Settings(
            provider="azure",
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
            azure_endpoint=_require(
                os.getenv("AZURE_OPENAI_ENDPOINT", ""),
                "AZURE_OPENAI_ENDPOINT",
                "It looks like https://<your-resource>.openai.azure.com/",
            ),
            azure_api_key=_require(
                os.getenv("AZURE_OPENAI_API_KEY", ""),
                "AZURE_OPENAI_API_KEY",
                "Find it in the Azure portal under your resource > Keys and Endpoint.",
            ),
            azure_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider == "github":
        return Settings(
            provider="github",
            model=os.getenv("GITHUB_MODEL", "gpt-4o-mini"),
            api_key=_require(
                os.getenv("GITHUB_TOKEN", ""),
                "GITHUB_TOKEN",
                "Create a free token (no scopes needed) at https://github.com/settings/tokens",
            ),
            base_url="https://models.inference.ai.azure.com",
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    if provider == "openai":
        return Settings(
            provider="openai",
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=_require(
                os.getenv("OPENAI_API_KEY", ""),
                "OPENAI_API_KEY",
                "Create one at https://platform.openai.com/api-keys",
            ),
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    raise ConfigError(
        f"Unknown PROVIDER '{provider}'. Use one of: azure, github, openai."
    )
