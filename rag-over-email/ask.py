"""Command-line interface: ask questions over the email inbox.

Examples:
    python ask.py --demo
    python ask.py "When is Project Aurora launching?"
    python ask.py "What is the PTO policy?" --backend embeddings --k 5
    python ask.py "..." --data path/to/inbox.mbox
"""
import argparse

from rag.pipeline import EmailRAG

DEMO_QUESTIONS = [
    "What is the approved Q3 marketing budget?",
    "Who is the lead for Project Aurora?",
    "When is the office moving and to which building?",
    "What is the deadline to reset our passwords?",
]


def print_result(result):
    print("\n" + "=" * 72)
    print(f"Q: {result['question']}")
    print(f"A: {result['answer']}")
    print(f"   (answer mode: {result['mode']})")
    print("   sources:")
    for i, s in enumerate(result["sources"], 1):
        print(f"     [{i}] {s['subject']}  -  {s['from']}  ({s['date']})  score={s['score']}")


def main():
    parser = argparse.ArgumentParser(description="Ask questions over an email inbox (RAG).")
    parser.add_argument("question", nargs="*", help="your question (omit to run --demo)")
    parser.add_argument("--data", default=None,
                        help="path to a .json / .mbox file or a folder of .eml (default: sample data)")
    parser.add_argument("--backend", default="tfidf", choices=["tfidf", "embeddings"])
    parser.add_argument("--k", type=int, default=4, help="number of emails to retrieve")
    parser.add_argument("--demo", action="store_true", help="run a set of demo questions")
    args = parser.parse_args()

    rag = EmailRAG(args.data, backend=args.backend)
    print(f"Loaded {len(rag.emails)} emails | retrieval backend: {rag.backend}")

    if args.demo or not args.question:
        for q in DEMO_QUESTIONS:
            print_result(rag.ask(q, k=args.k))
    else:
        print_result(rag.ask(" ".join(args.question), k=args.k))


if __name__ == "__main__":
    main()
