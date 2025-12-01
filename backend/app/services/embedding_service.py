"""Local embedding service using sentence-transformers."""
from typing import List
import threading


class EmbeddingService:
    """Singleton service for local embeddings."""

    _instance = None
    _lock = threading.Lock()
    _model = None
    MODEL_NAME = "all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.MODEL_NAME)
        return self._model

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using local model."""
        model = self._load_model()
        text = text.replace("\n", " ")
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embedding for efficiency during document processing."""
        model = self._load_model()
        texts = [t.replace("\n", " ") for t in texts]
        embeddings = model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
