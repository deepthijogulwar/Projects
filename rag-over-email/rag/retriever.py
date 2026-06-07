"""Retrieval layer.

Default backend is **TF-IDF** (scikit-learn) — no heavy dependencies, runs
anywhere instantly. An optional **embeddings** backend uses sentence-transformers
for semantic search (better with paraphrases/synonyms); turn it on with
backend="embeddings" after `pip install sentence-transformers`.

Shipping a lightweight default that always runs, with a semantic upgrade you can
flip on, is a deliberate design choice — not every environment can run a GPU model.
"""
import numpy as np


class Retriever:
    def __init__(self, backend="tfidf"):
        if backend not in ("tfidf", "embeddings"):
            raise ValueError("backend must be 'tfidf' or 'embeddings'")
        self.backend = backend
        self._matrix = None

    def fit(self, docs):
        """Index a list of document strings."""
        self._docs = list(docs)
        if self.backend == "embeddings":
            self._fit_embeddings()
        else:
            self._fit_tfidf()
        return self

    def search(self, query, k=4):
        """Return the top-k (index, score) pairs, best match first."""
        scores = self._search_embeddings(query) if self.backend == "embeddings" else self._search_tfidf(query)
        order = np.argsort(scores)[::-1][:k]
        return [(int(i), float(scores[i])) for i in order]

    # --- TF-IDF backend (default) ---
    def _fit_tfidf(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = self._vectorizer.fit_transform(self._docs)

    def _search_tfidf(self, query):
        from sklearn.metrics.pairwise import cosine_similarity
        qv = self._vectorizer.transform([query])
        return cosine_similarity(qv, self._matrix)[0]

    # --- Embeddings backend (optional) ---
    def _fit_embeddings(self):
        self._model = _load_sentence_model()
        self._matrix = self._model.encode(self._docs, normalize_embeddings=True)

    def _search_embeddings(self, query):
        qv = self._model.encode([query], normalize_embeddings=True)[0]
        return self._matrix @ qv  # cosine similarity (vectors are normalized)


def _load_sentence_model(name="all-MiniLM-L6-v2"):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise ImportError(
            "The 'embeddings' backend needs sentence-transformers. "
            "Install it with:  pip install sentence-transformers"
        ) from exc
    return SentenceTransformer(name)
