"""Create the right API client for the chosen provider.

All three providers (Azure OpenAI, GitHub Models, OpenAI) expose the SAME
`client.chat.completions.create(...)` method, so the rest of the app doesn't
have to care which one you picked.
"""

from __future__ import annotations

from .config import Settings


def build_client(settings: Settings):
    """Return a tuple of (client, model_name) for the configured provider."""
    if settings.provider == "azure":
        from openai import AzureOpenAI

        # --- API key auth (simplest; this is what the Microsoft Learn labs use) ---
        client = AzureOpenAI(
            azure_endpoint=settings.azure_endpoint,
            api_key=settings.azure_api_key,
            api_version=settings.azure_api_version,
        )

        # --- OPTIONAL: keyless Microsoft Entra ID auth (more secure, no key in .env) ---
        # To use it: `pip install azure-identity`, then delete the block above and
        # uncomment the block below.
        #
        # from azure.identity import DefaultAzureCredential, get_bearer_token_provider
        # token_provider = get_bearer_token_provider(
        #     DefaultAzureCredential(),
        #     "https://cognitiveservices.azure.com/.default",
        # )
        # client = AzureOpenAI(
        #     azure_endpoint=settings.azure_endpoint,
        #     azure_ad_token_provider=token_provider,
        #     api_version=settings.azure_api_version,
        # )

        return client, settings.model

    # GitHub Models and OpenAI both use the plain OpenAI client.
    from openai import OpenAI

    if settings.provider == "github":
        client = OpenAI(base_url=settings.base_url, api_key=settings.api_key)
        return client, settings.model

    # provider == "openai"
    client = OpenAI(api_key=settings.api_key)
    return client, settings.model
