"""End-to-end pipeline: load emails -> index -> ask a question."""
import os
from .ingest import load_emails, searchable_text
from .retriever import Retriever
from . import generator

# Default to the bundled sample data, resolved relative to this file so it works
# no matter which folder you run from.
_DEFAULT_DATA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sample_emails.json"
)


class EmailRAG:
    """Retrieval-augmented question answering over a collection of emails."""

    def __init__(self, emails_path=None, backend="tfidf"):
        self.emails = load_emails(emails_path or _DEFAULT_DATA)
        self._texts = [searchable_text(e) for e in self.emails]
        try:
            self.retriever = Retriever(backend=backend).fit(self._texts)
            self.backend = backend
        except Exception as exc:
            if backend != "tfidf":
                print(f"[warn] '{backend}' backend unavailable ({exc}); using tfidf instead.")
                self.retriever = Retriever(backend="tfidf").fit(self._texts)
                self.backend = "tfidf"
            else:
                raise

    def ask(self, question, k=4):
        """Retrieve the k most relevant emails and answer, with sources."""
        hits = self.retriever.search(question, k=k)
        retrieved = [self.emails[i] for i, _ in hits]
        result = generator.generate(question, retrieved)
        sources = [
            {
                "id": em.get("id", ""),
                "subject": em.get("subject", ""),
                "from": em.get("from", ""),
                "date": em.get("date", ""),
                "score": round(score, 3),
            }
            for (idx, score), em in zip(hits, retrieved)
        ]
        return {"question": question, "answer": result["answer"],
                "mode": result["mode"], "sources": sources}
