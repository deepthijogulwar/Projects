"""Retrieval evaluation: does the answer-bearing email show up in the top-k?

Most RAG demos skip evaluation. This measures retrieval quality on a small
labelled question set (data/eval_questions.json): hit@k, plus whether the
answer's key fact is present in the retrieved emails.
"""
import argparse
import json
import os

from rag.pipeline import EmailRAG
from rag.ingest import searchable_text

_EVAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "eval_questions.json")


def main():
    parser = argparse.ArgumentParser(description="Evaluate retrieval on a labelled question set.")
    parser.add_argument("--backend", default="tfidf", choices=["tfidf", "embeddings"])
    parser.add_argument("--k", type=int, default=4)
    args = parser.parse_args()

    with open(_EVAL, encoding="utf-8") as f:
        questions = json.load(f)

    rag = EmailRAG(backend=args.backend)
    print(f"Evaluating {len(questions)} questions | backend={rag.backend} | k={args.k}\n")

    hits = facts = 0
    for item in questions:
        found = rag.retriever.search(item["question"], k=args.k)
        ids = [rag.emails[i]["id"] for i, _ in found]
        text = " ".join(searchable_text(rag.emails[i]) for i, _ in found).lower()
        hit = bool(set(item["expected_ids"]) & set(ids))
        fact_ok = all(kw.lower() in text for kw in item.get("keywords", []))
        hits += hit
        facts += fact_ok
        print(f"[{'OK  ' if hit else 'MISS'}] {item['question']}")
        print(f"        expect one of {item['expected_ids']}  |  got {ids}  |  facts_present={fact_ok}")

    n = len(questions)
    print(f"\nRetrieval hit@{args.k}: {hits}/{n} = {hits / n:.0%}")
    print(f"Answer facts present in retrieved emails: {facts}/{n} = {facts / n:.0%}")


if __name__ == "__main__":
    main()
