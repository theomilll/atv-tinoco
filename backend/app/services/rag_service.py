"""RAG service with local embeddings and pluggable LLM providers."""
import base64
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
from flask import current_app

from ..models import DocumentChunk, Embedding
from .embedding_service import EmbeddingService
from .bm25_service import BM25Service, reciprocal_rank_fusion
from .llm_providers import get_llm_provider


class RAGService:
    """Service for Retrieval-Augmented Generation."""

    def __init__(self, use_hybrid_search: bool = True):
        self.embedding_service = EmbeddingService()
        self._llm = None
        self._bm25_service = None
        self.use_hybrid_search = use_hybrid_search

    @property
    def llm(self):
        if self._llm is None:
            self._llm = get_llm_provider()
        return self._llm

    @property
    def bm25_service(self):
        if self._bm25_service is None:
            self._bm25_service = BM25Service()
        return self._bm25_service

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        v1, v2 = np.array(vec1), np.array(vec2)
        norm = np.linalg.norm(v1) * np.linalg.norm(v2)
        return float(np.dot(v1, v2) / norm) if norm > 0 else 0.0

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding using local model."""
        return self.embedding_service.get_embedding(text)

    def semantic_search(
        self,
        query: str,
        user_id: int,
        top_k: int = 10
    ) -> List[Tuple[DocumentChunk, float]]:
        """Retrieve chunks using semantic (embedding) similarity."""
        query_embedding = self.get_embedding(query)

        embeddings = Embedding.query.join(Embedding.chunk).join(
            DocumentChunk.document
        ).filter(
            DocumentChunk.document.has(user_id=user_id, status='completed')
        ).all()

        if not embeddings:
            return []

        chunk_scores = []
        for embedding in embeddings:
            if len(embedding.vector) == len(query_embedding):
                similarity = self.cosine_similarity(query_embedding, embedding.vector)
                chunk_scores.append((embedding.chunk, similarity))

        chunk_scores.sort(key=lambda x: x[1], reverse=True)
        return chunk_scores[:top_k]

    def keyword_search(
        self,
        query: str,
        user_id: int,
        top_k: int = 10
    ) -> List[Tuple[DocumentChunk, float]]:
        """Retrieve chunks using BM25 keyword search."""
        return self.bm25_service.search(query, user_id, top_k)

    def retrieve_relevant_chunks(
        self,
        query: str,
        user_id: int,
        top_k: int = 5
    ) -> List[Tuple[DocumentChunk, float]]:
        """Retrieve most relevant document chunks using hybrid search."""
        if not self.use_hybrid_search:
            return self.semantic_search(query, user_id, top_k)

        semantic_results = self.semantic_search(query, user_id, top_k=10)
        keyword_results = self.keyword_search(query, user_id, top_k=10)

        if not semantic_results:
            return keyword_results[:top_k]
        if not keyword_results:
            return semantic_results[:top_k]

        fused = reciprocal_rank_fusion([semantic_results, keyword_results])
        return fused[:top_k]

    def build_context_from_chunks(self, chunks: List[Tuple[DocumentChunk, float]]) -> str:
        """Build context string from retrieved chunks."""
        if not chunks:
            return "No relevant documents found."

        context_parts = []
        for i, (chunk, score) in enumerate(chunks, 1):
            context_parts.append(
                f"[Document {i}: {chunk.document.title}]\n{chunk.content}"
            )

        return "\n\n".join(context_parts)

    def generate_response(
        self,
        user_message: str,
        context: str,
        conversation_history: Optional[List[dict]] = None,
        images: Optional[List[str]] = None
    ) -> str:
        """Generate AI response using LLM with RAG context and optional images."""
        system_prompt = """You are ChatGepeto, a friendly and knowledgeable teacher assistant that helps students with their study questions.

Instructions:
- Help students understand concepts clearly
- Provide explanations that are easy to follow
- Use examples when helpful
- Encourage learning and critical thinking
- Be patient and supportive"""

        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            for msg in conversation_history[-10:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        messages.append({"role": "user", "content": user_message})

        return self.llm.chat(messages, temperature=0.7, max_tokens=500, images=images)

    def generate_conversation_title(self, first_message: str) -> str:
        """Generate a short title for a conversation."""
        messages = [{
            "role": "user",
            "content": f'Generate a short, concise title (max 50 characters) for a conversation that starts with: "{first_message}". Return only the title, nothing else.'
        }]

        title = self.llm.chat(messages, temperature=0.5, max_tokens=20)
        title = title.strip().strip('"').strip("'")
        return title[:50]


# File type mapping
ALLOWED_TYPES = {
    'image/png': 'image',
    'image/jpeg': 'image',
    'image/gif': 'image',
    'image/webp': 'image',
    'application/pdf': 'document',
    'text/plain': 'document',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'document',
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def process_attachment(file, user_id: int) -> dict:
    """Save uploaded file and return attachment dict."""
    content_type = file.content_type
    if content_type not in ALLOWED_TYPES:
        raise ValueError(f"Unsupported file type: {content_type}")

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)

    if size > MAX_FILE_SIZE:
        raise ValueError("File too large (max 10MB)")

    save_dir = Path(current_app.config['UPLOAD_FOLDER']) / 'attachments' / str(user_id)
    save_dir.mkdir(parents=True, exist_ok=True)
    file_path = save_dir / file.filename

    counter = 1
    while file_path.exists():
        stem = Path(file.filename).stem
        suffix = Path(file.filename).suffix
        file_path = save_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    file.save(str(file_path))

    return {
        'filename': file.filename,
        'file_type': content_type,
        'file_path': str(file_path.relative_to(current_app.config['UPLOAD_FOLDER'])),
        'category': ALLOWED_TYPES[content_type],
    }


def get_base64_for_image(file_path: str) -> str:
    """Read image file and return base64 encoded string."""
    full_path = Path(current_app.config['UPLOAD_FOLDER']) / file_path
    with open(full_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def extract_text_from_doc(file_path: str, file_type: str) -> str:
    """Extract text content from document files."""
    full_path = Path(current_app.config['UPLOAD_FOLDER']) / file_path

    if file_type == 'text/plain':
        return full_path.read_text(errors='ignore')

    if file_type == 'application/pdf':
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(full_path))
            return '\n'.join(page.extract_text() or '' for page in reader.pages)
        except Exception:
            return "[Could not extract PDF text]"

    if 'wordprocessingml' in file_type:
        try:
            import docx
            doc = docx.Document(str(full_path))
            return '\n'.join(p.text for p in doc.paragraphs)
        except Exception:
            return "[Could not extract DOCX text]"

    return ""
