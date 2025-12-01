"""BM25 keyword search service for hybrid retrieval."""
import re
from typing import List, Tuple, Optional
from rank_bm25 import BM25Okapi

from ..models import DocumentChunk


class BM25Service:
    """Service for BM25 keyword-based search."""

    def __init__(self):
        self._index = None
        self._chunks = None
        self._user_id = None

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase, remove punctuation, split."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        return [t for t in tokens if len(t) > 2]

    def _build_index(self, user_id: int) -> None:
        """Build BM25 index for user's documents."""
        if self._user_id == user_id and self._index is not None:
            return

        self._chunks = list(
            DocumentChunk.query.join(DocumentChunk.document).filter(
                DocumentChunk.document.has(user_id=user_id, status='completed')
            ).all()
        )

        if not self._chunks:
            self._index = None
            self._user_id = user_id
            return

        tokenized_corpus = [self._tokenize(chunk.content) for chunk in self._chunks]
        self._index = BM25Okapi(tokenized_corpus)
        self._user_id = user_id

    def search(
        self,
        query: str,
        user_id: int,
        top_k: int = 10
    ) -> List[Tuple[DocumentChunk, float]]:
        """Search for chunks using BM25."""
        self._build_index(user_id)

        if not self._index or not self._chunks:
            return []

        tokenized_query = self._tokenize(query)
        if not tokenized_query:
            return []

        scores = self._index.get_scores(tokenized_query)

        chunk_scores = list(zip(self._chunks, scores))
        chunk_scores.sort(key=lambda x: x[1], reverse=True)

        results = [(chunk, score) for chunk, score in chunk_scores if score > 0]
        return results[:top_k]

    def invalidate_cache(self, user_id: Optional[int] = None) -> None:
        """Invalidate the BM25 index cache."""
        if user_id is None or self._user_id == user_id:
            self._index = None
            self._chunks = None
            self._user_id = None


def reciprocal_rank_fusion(
    results_list: List[List[Tuple[DocumentChunk, float]]],
    k: int = 60
) -> List[Tuple[DocumentChunk, float]]:
    """Combine multiple ranked lists using Reciprocal Rank Fusion."""
    chunk_scores = {}

    for results in results_list:
        for rank, (chunk, _) in enumerate(results, 1):
            chunk_id = chunk.id
            rrf_score = 1.0 / (k + rank)

            if chunk_id in chunk_scores:
                existing_chunk, existing_score = chunk_scores[chunk_id]
                chunk_scores[chunk_id] = (existing_chunk, existing_score + rrf_score)
            else:
                chunk_scores[chunk_id] = (chunk, rrf_score)

    fused = list(chunk_scores.values())
    fused.sort(key=lambda x: x[1], reverse=True)

    return fused
