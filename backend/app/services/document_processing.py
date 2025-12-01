"""Document processing - chunk and create embeddings."""
from ..extensions import db
from ..models import Document, Embedding
from .embedding_service import EmbeddingService
from .chunking_service import ChunkingService


def process_document(document: Document) -> None:
    """Process a document: chunk and create embeddings."""
    document.status = 'processing'
    db.session.commit()

    try:
        chunking_service = ChunkingService()
        chunks = chunking_service.chunk_document(document)

        if not chunks:
            document.status = 'failed'
            db.session.commit()
            return

        embedding_service = EmbeddingService()
        texts = [chunk.content for chunk in chunks]
        vectors = embedding_service.get_embeddings_batch(texts)

        for chunk, vector in zip(chunks, vectors):
            embedding = Embedding(
                chunk=chunk,
                vector=vector,
                model_name=embedding_service.MODEL_NAME
            )
            db.session.add(embedding)

        document.status = 'completed'
        db.session.commit()

    except Exception:
        document.status = 'failed'
        db.session.commit()
        raise
