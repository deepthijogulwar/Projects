"""Optional web UI:  streamlit run app.py

A simple box to ask questions over the inbox, with expandable source emails.
Requires: pip install streamlit
"""
import streamlit as st

from rag.pipeline import EmailRAG

st.set_page_config(page_title="Ask My Inbox (RAG)", page_icon="📧")
st.title("📧 Ask My Inbox")
st.caption("Retrieval-augmented Q&A over an email inbox — grounded answers with citations.")


@st.cache_resource
def load_rag():
    return EmailRAG()  # bundled sample data, TF-IDF backend


rag = load_rag()
st.write(f"Loaded **{len(rag.emails)}** emails · retrieval backend: `{rag.backend}`")

question = st.text_input("Ask a question about the inbox:",
                         placeholder="e.g. When is Project Aurora launching?")

if question:
    result = rag.ask(question)
    st.subheader("Answer")
    st.write(result["answer"])
    st.caption(f"answer mode: {result['mode']}")

    st.subheader("Sources")
    for i, s in enumerate(result["sources"], 1):
        with st.expander(f"[{i}] {s['subject']} — {s['from']} ({s['date']}) · score={s['score']}"):
            match = next((e for e in rag.emails if e["id"] == s["id"]), None)
            if match:
                st.text(match["body"])
