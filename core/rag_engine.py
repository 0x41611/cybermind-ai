"""
CyberMind AI - RAG Engine
Retrieval-Augmented Generation using ChromaDB + sentence-transformers
"""
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Any
from config import config
from utils.logger import get_logger
from utils.helpers import hash_text, chunk_text

logger = get_logger("rag_engine")


class RAGEngine:
    """
    Manages the knowledge base using ChromaDB.
    Stores CTF writeups and retrieves relevant context for AI responses.
    """

    COLLECTION_NAME = "cybermind_writeups"

    def __init__(self):
        self._client = None
        self._collection = None
        self._embedder = None
        self._initialized = False
        self._stats = {"total_docs": 0, "categories": {}}

    def initialize(self, on_progress: Optional[callable] = None) -> bool:
        """Initialize ChromaDB and embedding model"""
        try:
            if on_progress:
                on_progress("Loading ChromaDB...")

            import chromadb
            self._client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)
            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )

            if on_progress:
                on_progress("Loading embedding model (first time may take a while)...")

            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer(config.EMBEDDING_MODEL)

            self._initialized = True
            self._update_stats()

            logger.info(f"RAG engine initialized. Total docs: {self._stats['total_docs']}")
            return True

        except ImportError as e:
            logger.error(f"Missing dependency: {e}. Run: pip install chromadb sentence-transformers")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {e}")
            return False

    def is_ready(self) -> bool:
        return self._initialized

    def add_writeup(self, writeup: Dict[str, Any]) -> int:
        """
        Add a CTF writeup to the knowledge base.
        Returns number of chunks added.
        """
        if not self._initialized:
            return 0

        title = writeup.get("title", "Untitled")
        content = writeup.get("content", "")
        category = writeup.get("category", "Misc")
        source = writeup.get("source", "unknown")
        tags = writeup.get("tags", [])

        if not content.strip():
            return 0

        # Split into chunks
        chunks = chunk_text(content, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        added = 0

        for i, chunk in enumerate(chunks):
            doc_id = hash_text(f"{title}_{i}_{chunk[:100]}")

            # Skip duplicates
            try:
                existing = self._collection.get(ids=[doc_id])
                if existing["ids"]:
                    continue
            except Exception:
                pass

            try:
                embedding = self._embedder.encode(chunk).tolist()
                self._collection.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{
                        "title": title,
                        "category": category,
                        "source": source,
                        "chunk_index": i,
                        "tags": json.dumps(tags),
                    }]
                )
                added += 1
            except Exception as e:
                logger.warning(f"Failed to add chunk {i} of '{title}': {e}")

        if added > 0:
            self._update_stats()
            logger.debug(f"Added {added} chunks for: {title}")

        return added

    def add_writeups_batch(self, writeups: List[Dict], on_progress: Optional[callable] = None) -> int:
        """Add multiple writeups"""
        total = 0
        for i, writeup in enumerate(writeups):
            if on_progress:
                on_progress(i + 1, len(writeups), writeup.get("title", "..."))
            total += self.add_writeup(writeup)
        return total

    def search(self, query: str, n_results: int = 5, category: Optional[str] = None) -> List[Dict]:
        """
        Search for relevant writeups/content.
        Returns list of relevant text chunks with metadata.
        """
        if not self._initialized:
            return []

        try:
            query_embedding = self._embedder.encode(query).tolist()

            where = {"category": category} if category else None

            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, max(1, self._stats["total_docs"])),
                where=where,
                include=["documents", "metadatas", "distances"]
            )

            docs = []
            if results["documents"] and results["documents"][0]:
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                ):
                    # Only include if reasonably similar (cosine distance < 0.8)
                    if dist < 0.8:
                        docs.append({
                            "content": doc,
                            "title": meta.get("title", ""),
                            "category": meta.get("category", ""),
                            "source": meta.get("source", ""),
                            "similarity": round(1 - dist, 3),
                            "tags": json.loads(meta.get("tags", "[]"))
                        })

            return docs

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def get_context_for_query(self, query: str, max_tokens: int = 3000) -> str:
        """
        Build context string from relevant writeups for injection into AI prompt.
        """
        results = self.search(query, n_results=config.MAX_CONTEXT_DOCS)
        if not results:
            return ""

        context_parts = ["## Relevant CTF Writeups & Techniques from Knowledge Base:\n"]
        token_count = 0

        for r in results:
            chunk = (
                f"### {r['title']} [{r['category']}] (similarity: {r['similarity']})\n"
                f"{r['content']}\n"
            )
            chunk_tokens = len(chunk) // 4
            if token_count + chunk_tokens > max_tokens:
                break
            context_parts.append(chunk)
            token_count += chunk_tokens

        return "\n".join(context_parts)

    def get_stats(self) -> Dict:
        """Get knowledge base statistics"""
        self._update_stats()
        return self._stats.copy()

    def _update_stats(self):
        """Update statistics"""
        if not self._collection:
            return
        try:
            count = self._collection.count()
            self._stats["total_docs"] = count

            # Get category breakdown + unique writeup count
            if count > 0:
                results = self._collection.get(include=["metadatas"])
                cats = {}
                unique_titles = set()
                for meta in results.get("metadatas", []):
                    cat = meta.get("category", "Unknown")
                    cats[cat] = cats.get(cat, 0) + 1
                    title = meta.get("title", "")
                    if title:
                        unique_titles.add(title)
                self._stats["categories"] = cats
                # Override trainer's cumulative counter with the real count
                self._stats["total_writeups"] = len(unique_titles)
        except Exception:
            pass

    def delete_all(self):
        """Clear the knowledge base"""
        if self._client and self._collection:
            self._client.delete_collection(self.COLLECTION_NAME)
            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            self._update_stats()
