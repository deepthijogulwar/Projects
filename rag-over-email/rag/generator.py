"""Answer generation (the 'G' in RAG).

If an LLM is configured (env var OPENAI_API_KEY or GITHUB_TOKEN, plus the
`openai` package), we ask it to answer using ONLY the retrieved emails and to
cite them. Otherwise we fall back to an **extractive** answer (the single most
relevant sentence from the top emails) so the demo always works offline and
free. Either way the cited source emails are returned for transparency.
"""
import os
import re
import importlib.util

SYSTEM_PROMPT = (
    "You answer questions using ONLY the provided emails. "
    "Cite the emails you use by their number in square brackets, e.g. [1]. "
    "If the answer is not in the emails, say you could not find it. Be concise."
)


def llm_available():
    has_key = bool(os.getenv("OPENAI_API_KEY") or os.getenv("GITHUB_TOKEN"))
    has_pkg = importlib.util.find_spec("openai") is not None
    return has_key and has_pkg


def build_context(retrieved):
    """Number the retrieved emails so they can be cited [1], [2], ..."""
    blocks = []
    for i, em in enumerate(retrieved, 1):
        blocks.append(
            f"[{i}] From: {em.get('from', '')} | Subject: {em.get('subject', '')} "
            f"| Date: {em.get('date', '')}\n{em.get('body', '')}"
        )
    return "\n\n".join(blocks)


def generate(question, retrieved):
    """Return {'answer': str, 'mode': 'llm' | 'extractive'}."""
    if llm_available():
        try:
            return {"answer": _llm_answer(question, retrieved), "mode": "llm"}
        except Exception as exc:  # bad key / network / quota -> graceful fallback
            fallback = _extractive_answer(question, retrieved)
            return {"answer": f"{fallback}  (note: LLM call failed: {exc})",
                    "mode": "extractive"}
    return {"answer": _extractive_answer(question, retrieved), "mode": "extractive"}


# --- extractive fallback (no API key needed) ---
def _sentences(text):
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def _stem(word):
    """Very light suffix stripping so 'launching' matches 'launch'."""
    for suffix in ("ing", "ed", "es", "s"):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def _tokens(text):
    return {_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower())}


def _overlap(question, sentence):
    return len(_tokens(question) & _tokens(sentence))


def _extractive_answer(question, retrieved):
    # Look in the top couple of retrieved emails (where the answer is most
    # likely) and return the single best-matching sentence as the offline answer.
    best_score, best_sentence, best_rank = 0, "", None
    for rank, em in enumerate(retrieved[:2], 1):
        for sentence in _sentences(em.get("body", "")):
            score = _overlap(question, sentence)
            if score > best_score:
                best_score, best_sentence, best_rank = score, sentence, rank
    if not best_sentence:
        return "I could not find an answer to that in the emails."
    return f"{best_sentence} [{best_rank}]"


# --- LLM answer (used when an API key + openai are present) ---
def _llm_answer(question, retrieved):
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("GITHUB_TOKEN")
    base_url = os.getenv("OPENAI_BASE_URL")
    # GitHub Models is a free OpenAI-compatible endpoint (uses your GITHUB_TOKEN)
    if not os.getenv("OPENAI_API_KEY") and os.getenv("GITHUB_TOKEN"):
        base_url = base_url or "https://models.inference.ai.azure.com"

    client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
    model = os.getenv("RAG_MODEL", "gpt-4o-mini")
    user = f"Emails:\n\n{build_context(retrieved)}\n\nQuestion: {question}"
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": user}],
        temperature=0,
    )
    return resp.choices[0].message.content.strip()
