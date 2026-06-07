# 📧 RAG over Email — Ask Your Inbox

> Point it at an inbox, ask a question in plain English, and get a **grounded
> answer with citations to the actual emails**. A Retrieval-Augmented Generation
> (RAG) system built for messy, real-world email — not a clean single-PDF demo.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![retrieval](https://img.shields.io/badge/retrieval-TF--IDF%20%7C%20embeddings-success)
![LLM](https://img.shields.io/badge/LLM-optional-orange)
![retrieval hit@4](https://img.shields.io/badge/retrieval%20hit@4-100%25-brightgreen)

## What it does
Ask things like *"When is Project Aurora launching?"* or *"What's the approved Q3
budget?"* and get an answer **plus the source emails it came from**, so you can
trust and verify it.

```
$ python ask.py "What is the approved Q3 marketing budget?"
A: I have approved a Q3 marketing budget of $280,000. [1]
   sources:
     [1] RE: Q3 marketing budget proposal - Maria Lopez <cfo@northwind.example> (2026-03-05)
```

## Why this one stands out
Most RAG portfolio projects are "chat with one PDF." Email is harder and more
realistic — and this project leans into that:

| Typical RAG demo | This project |
|---|---|
| One clean PDF | A real **inbox**: threads, senders, dates, reply chains |
| No sources | Every answer **cites the emails** it used |
| "Looks like it works" | A **retrieval evaluation** (hit@k) on a labelled question set |
| One hard-wired stack | **Pluggable** retrieval (TF-IDF → semantic embeddings) + optional LLM |
| Needs a paid API to run | Runs **offline & free** out of the box (extractive fallback) |

## How it works
```
emails (.json / .mbox / .eml)
        |  ingest.py     -> normalise to {id, from, date, subject, body}
        v
   retriever.py          -> TF-IDF (default) or sentence-transformers (optional)
        |  top-k emails
        v
   generator.py          -> LLM answer with citations  (or extractive fallback)
        v
   answer + cited sources
```

## Quickstart
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

python ask.py --demo                       # run sample questions
python ask.py "When is the office move?"   # ask your own
python evaluate.py                         # retrieval hit@k on the labelled set
```
Optional upgrades:
```powershell
pip install sentence-transformers   # then: python ask.py "..." --backend embeddings
pip install openai                  # set OPENAI_API_KEY (or GITHUB_TOKEN) for real LLM answers
pip install streamlit               # then: streamlit run app.py   (web UI)
```

## Use your own emails
The bundled `data/sample_emails.json` is a small **synthetic** inbox so the demo
runs instantly, offline, and with zero privacy risk. To use real data, point
`--data` at:
- a **.mbox** export (Gmail: *Takeout → Mail*; Thunderbird; etc.),
- a **folder of .eml** files, or
- the public **Enron email dataset** (the classic email corpus).

```powershell
python ask.py "your question" --data path\to\inbox.mbox
```
> ⚠️ **Privacy:** never commit a real inbox to a public repo — it exposes your and
> other people's private mail. `.gitignore` already excludes `*.mbox`, `*.eml`,
> and `data/enron/`. Demo publicly on synthetic/Enron data; run on your own inbox
> locally.

## Evaluation
`evaluate.py` checks, for a labelled question set, whether the answer-bearing
email is retrieved in the top-k:
```
Retrieval hit@4: 8/8 = 100%
Answer facts present in retrieved emails: 8/8 = 100%
```
This is deliberately the honest, measurable part: writing the final sentence is
the LLM's job, but **retrieving the right email is what makes or breaks a RAG
system** — so that's what we measure.

## ⚠️ Limitations (read honestly)
- **Demo data is synthetic** (a small fictional company) so the repo runs
  instantly and privately. Swap in Enron or your own inbox for real scale.
- **Default retrieval is TF-IDF** (keyword-based) — fast and dependency-free, but
  it misses pure paraphrases. Switch on `--backend embeddings` for semantic search.
- **Answers are extractive without an LLM.** With no API key, the answer is the
  best-matching *sentence* (a rough preview). Add a key for fluent, synthesised
  answers with citations.
- **No thread-merging or chunking yet** — emails are handled whole. Fine for short
  mail; long threads would benefit from chunking.
- **Small corpus, no PII scrubbing** — a production system would add access
  control and redaction.

## Tech stack
Python · scikit-learn (TF-IDF) · NumPy · *(optional)* sentence-transformers ·
OpenAI-compatible LLMs (OpenAI / Azure / free GitHub Models) · Streamlit

## Roadmap
- Thread-aware chunking + metadata filters (sender / date)
- Hybrid retrieval (TF-IDF + embeddings) with re-ranking
- Answer-faithfulness evaluation (not just retrieval)
- Dockerfile + a hosted demo
