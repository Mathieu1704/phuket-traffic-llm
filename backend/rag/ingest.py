"""
One-time indexing pipeline: textualize all data sources → embed → store in ChromaDB.
Run from TFE_Phuket root:
    source venv/bin/activate
    python backend/rag/ingest.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from rag.textualizers import (
    traffic, flights, weather, events,
    social, poi, intersections, turning, segments, transport,
)

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
BATCH_SIZE = 100

SOURCES = [
    ("traffic_monthly",   traffic.textualize),
    ("flights",           flights.textualize),
    ("weather",           weather.textualize),
    ("events",            events.textualize),
    ("social_trends",     social.textualize),
    ("poi",               poi.textualize),
    ("intersections",     intersections.textualize),
    ("turning_movements", turning.textualize),
    ("traffic_segments",  segments.textualize),
    ("transport",         transport.textualize),
]


def _safe_meta(meta: dict) -> dict:
    """ChromaDB only accepts str/int/float/bool metadata values."""
    clean = {}
    for k, v in meta.items():
        if isinstance(v, (str, int, float, bool)):
            clean[k] = v
        else:
            clean[k] = str(v)
    return clean


def ingest_collection(client, embed_fn, name: str, chunks: list[dict]):
    # Delete existing collection to allow clean re-ingest
    try:
        client.delete_collection(name)
    except Exception:
        pass

    coll = client.create_collection(name=name, embedding_function=embed_fn)

    total = len(chunks)
    ingested = 0
    for i in range(0, total, BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        coll.add(
            documents=[c["text"] for c in batch],
            metadatas=[_safe_meta(c["metadata"]) for c in batch],
            ids=[f"{name}_{i + j}" for j, _ in enumerate(batch)],
        )
        ingested += len(batch)
        print(f"  {name}: {ingested}/{total} chunks", end="\r")

    print(f"  ✓ {name}: {total} chunks indexed" + " " * 20)
    return total


def main():
    print(f"ChromaDB path: {os.path.abspath(CHROMA_PATH)}")
    print(f"Embedding model: {EMBED_MODEL}")
    print("Loading embedding model (first run downloads ~90 MB)...")

    embed_fn = SentenceTransformerEmbeddingFunction(model_name=EMBED_MODEL)
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    total_chunks = 0
    t0 = time.time()

    for coll_name, textualize_fn in SOURCES:
        print(f"\n[{coll_name}] Textualizing...", end=" ")
        try:
            chunks = textualize_fn()
            print(f"{len(chunks)} chunks")
            if chunks:
                total_chunks += ingest_collection(client, embed_fn, coll_name, chunks)
        except Exception as e:
            print(f"ERROR: {e}")

    elapsed = time.time() - t0
    print(f"\n{'='*50}")
    print(f"✓ Indexed {total_chunks} total chunks in {elapsed:.1f}s")
    print(f"✓ ChromaDB stored at: {os.path.abspath(CHROMA_PATH)}")
    print(f"\nCollections created:")
    for coll in client.list_collections():
        n = client.get_collection(coll.name, embedding_function=embed_fn).count()
        print(f"  {coll.name:25s} {n} chunks")


if __name__ == "__main__":
    main()
