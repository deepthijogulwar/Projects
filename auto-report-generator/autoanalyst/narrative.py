"""Turn the computed numbers into a plain-English executive summary.

Uses an LLM if one is configured (OPENAI_API_KEY / GITHUB_TOKEN + the `openai`
package); otherwise a clear template. Either way the *numbers come from the data*,
not invented by the model — the LLM only rephrases the verified facts.
"""
import os
import importlib.util


def _llm_available():
    has_key = bool(os.getenv("OPENAI_API_KEY") or os.getenv("GITHUB_TOKEN"))
    return has_key and importlib.util.find_spec("openai") is not None


def write_summary(facts):
    if _llm_available():
        try:
            return _llm_summary(facts)
        except Exception:
            pass  # any API problem -> fall back to the template
    return _template_summary(facts)


def _template_summary(f):
    parts = [
        f"Across {f['months']} months ({f['start']:%b %Y}-{f['end']:%b %Y}), total sales were "
        f"${f['total_sales']:,.0f} at a {f['margin']:.1%} profit margin "
        f"(${f['total_profit']:,.0f} profit)."
    ]
    if f.get("change"):
        c = f["change"]
        direction = "up" if c["pct"] >= 0 else "down"
        parts.append(
            f"In the latest month ({c['last_period']:%b %Y}) sales were ${c['last']:,.0f}, "
            f"{direction} {abs(c['pct']):.1%} versus the prior month."
        )
    parts.append(
        f"{f['top_region']} was the top region and {f['top_category']} the top category by sales."
    )
    if f.get("loss_makers"):
        lm = ", ".join(f"{k} (${v:,.0f})" for k, v in f["loss_makers"].items())
        parts.append(f"Loss-making categories to investigate: {lm}.")
    if f.get("anomaly"):
        a = f["anomaly"]
        parts.append(
            f"{a['month']:%b %Y} stands out as an outlier (${a['value']:,.0f}, z={a['z']:.1f}) "
            f"and is worth a closer look."
        )
    return " ".join(parts)


def _llm_summary(f):
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GITHUB_TOKEN")
    base_url = os.getenv("OPENAI_BASE_URL")
    if not os.getenv("OPENAI_API_KEY") and os.getenv("GITHUB_TOKEN"):
        base_url = base_url or "https://models.inference.ai.azure.com"  # free GitHub Models

    client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
    model = os.getenv("REPORT_MODEL", "gpt-4o-mini")
    prompt = (
        "Write a concise 4-5 sentence executive summary for a sales report, using ONLY the "
        "facts below. Keep every number exactly as given. Be business-like.\n\n"
        + _template_summary(f)
    )
    resp = client.chat.completions.create(
        model=model,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()
