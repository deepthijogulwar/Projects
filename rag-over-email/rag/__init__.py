"""RAG over email — ask natural-language questions over an email inbox and get
grounded, cited answers.

Public entry point:
    from rag.pipeline import EmailRAG
"""
from .pipeline import EmailRAG

__all__ = ["EmailRAG"]
