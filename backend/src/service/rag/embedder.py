"""In-process embeddings via fastembed (ONNX). No network calls at query time:
the model is pre-baked into the Docker image, so retrieval works identically
with or without any cloud provider configured."""

import asyncio
from functools import lru_cache

from fastembed import TextEmbedding


@lru_cache
def _model(name: str) -> TextEmbedding:
    return TextEmbedding(name)


def embed_texts(texts: list[str], model_name: str) -> list[list[float]]:
    """Batch-embed for ingestion (synchronous; call from a worker thread)."""
    return [e.tolist() for e in _model(model_name).embed(texts, batch_size=64)]


def embed_query(text: str, model_name: str) -> list[float]:
    # bge models embed queries and passages symmetrically enough for this use.
    return next(iter(_model(model_name).query_embed(text))).tolist()


import re

STOP_WORDS = {
    "about", "after", "again", "also", "been", "before", "being", "between",
    "could", "does", "from", "have", "into", "just", "more", "most", "other",
    "should", "some", "than", "that", "their", "there", "these", "they", "this",
    "through", "what", "when", "where", "which", "while", "with", "would",
    "your", "and", "are", "as", "at", "by", "for", "in", "is", "it", "of", "on",
    "or", "the", "to", "we", "do",
    "give", "explain", "guests", "improving", "lenny", "lessons", "me", "plan",
    "podcast", "practical", "step", "strongest"
}

def sanitize_query(query: str) -> str:
    tokens = re.findall(r"[a-z0-9][a-z0-9'-]{1,}", query, re.I)
    valid_tokens = [t for t in tokens if t.lower() not in STOP_WORDS]
    if not valid_tokens:
        return query
    return " ".join(valid_tokens)

async def embed_query_async(text: str, model_name: str) -> list[float]:
    """ONNX inference is CPU-bound; keep it off the event loop."""
    clean_text = sanitize_query(text)
    return await asyncio.to_thread(embed_query, clean_text, model_name)


def warmup(model_name: str) -> None:
    embed_query("warmup", model_name)
