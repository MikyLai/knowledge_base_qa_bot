import os

from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from . import indexer


SYSTEM_PROMPT = """You are a helpful customer support assistant.
Answer ONLY using the information in the CONTEXT below.
For each fact you state, cite the source ID exactly as shown in [Source: ...].
Source IDs use the format filename#heading.
If the context does not contain enough information to answer, reply:
"I cannot confirm that from the knowledge base."
Do NOT guess, infer, or use any knowledge outside the provided context."""

_llm = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            request_timeout=20,
            max_retries=1,
        )
    return _llm


def build_prompt(query: str, ranked_sections: list) -> str:
    # TODO: Build the prompt from top-ranked Markdown sections.
    #
    # Design decision: Put raw Markdown sections into CONTEXT with citations.
    #
    # Hints:
    # 1. Include [Source: filename#heading] before each section.
    # 2. Include heading_path so the model sees the document structure.
    # 3. Include only top sections passed into this function.
    # 4. Place CONTEXT before QUESTION.
    context_parts = []
    for section, _score in ranked_sections:
        breadcrumb = " > ".join(section.heading_path)
        context_parts.append(
            f"[Source: {section.id}]\n({breadcrumb})\n{section.content}"
        )
    context = "\n\n".join(context_parts)
    return f"CONTEXT:\n{context}\n\nQUESTION:\n{query}"


SCORE_THRESHOLD = 1.0


def query(question: str) -> dict:
    if not indexer.sections:
        return {
            "answer": "The knowledge base has not been indexed yet. Call POST /index first.",
            "sources": [],
        }

    ranked_sections = indexer.search(question, k=3)
    ranked_sections = [(s, score) for s, score in ranked_sections if score >= SCORE_THRESHOLD]
    if not ranked_sections:
        return {
            "answer": "I cannot confirm that from the knowledge base.",
            "sources": [],
        }

    response = get_llm().invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=build_prompt(question, ranked_sections)),
    ])

    sources = [
        {
            "source": section.id,
            "heading": " > ".join(section.heading_path),
            "score": round(score, 3),
            "content": section.content[:240],
        }
        for section, score in ranked_sections
    ]

    return {
        "answer": response.content,
        "sources": sources,
    }
