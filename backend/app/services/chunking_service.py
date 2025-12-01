"""Document chunking service."""
import re
from typing import List
from pathlib import Path
from flask import current_app

from ..extensions import db
from ..models import Document, DocumentChunk


class ChunkingService:
    """Service for splitting documents into chunks for embedding."""

    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 50
    CHARS_PER_TOKEN = 4

    def __init__(self, chunk_size: int = None, overlap: int = None):
        self.chunk_size = chunk_size or self.CHUNK_SIZE
        self.overlap = overlap or self.CHUNK_OVERLAP
        self.char_limit = self.chunk_size * self.CHARS_PER_TOKEN
        self.overlap_chars = self.overlap * self.CHARS_PER_TOKEN

    def split_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks using sliding window."""
        if not text or not text.strip():
            return []

        text = self._clean_text(text)

        if len(text) <= self.char_limit:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.char_limit

            if end < len(text):
                chunk_text = text[start:end]
                for boundary in ['. ', '.\n', '? ', '!\n', '! ', '?\n']:
                    last_boundary = chunk_text.rfind(boundary, len(chunk_text) - int(self.char_limit * 0.2))
                    if last_boundary != -1:
                        end = start + last_boundary + len(boundary)
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - self.overlap_chars
            if start >= len(text) - self.overlap_chars:
                break

        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean text for chunking."""
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('\x00', '')
        return text.strip()

    def chunk_document(self, document: Document) -> List[DocumentChunk]:
        """Extract text from document and create chunks."""
        file_path = Path(current_app.config['UPLOAD_FOLDER']) / document.file

        text = self._extract_text(file_path, document.file_type)

        if not text:
            return []

        chunk_texts = self.split_text(text)

        chunks = []
        for i, chunk_text in enumerate(chunk_texts):
            chunk = DocumentChunk(
                document=document,
                content=chunk_text,
                chunk_index=i,
                chunk_metadata={
                    'source_file': document.file,
                    'file_type': document.file_type,
                    'chunk_method': 'sliding_window',
                    'chunk_size': self.chunk_size,
                    'overlap': self.overlap,
                }
            )
            db.session.add(chunk)
            chunks.append(chunk)

        db.session.commit()
        return chunks

    def _extract_text(self, file_path: Path, file_type: str) -> str:
        """Extract text from file based on type."""
        if not file_path.exists():
            return ""

        if file_type == 'text/plain':
            return file_path.read_text(errors='ignore')

        if file_type == 'application/pdf':
            return self._extract_pdf(file_path)

        if 'wordprocessingml' in file_type:
            return self._extract_docx(file_path)

        if file_type == 'text/html':
            return self._extract_html(file_path)

        return ""

    def _extract_pdf(self, file_path: Path) -> str:
        """Extract text from PDF with page markers."""
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(file_path))
            pages = []
            for i, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text:
                    pages.append(f"[Page {i}]\n{text}")
            return '\n\n'.join(pages)
        except Exception:
            return ""

    def _extract_docx(self, file_path: Path) -> str:
        """Extract text from DOCX."""
        try:
            import docx
            doc = docx.Document(str(file_path))
            return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception:
            return ""

    def _extract_html(self, file_path: Path) -> str:
        """Extract text from HTML file."""
        try:
            html = file_path.read_text(errors='ignore')
            return self._html_to_text(html)
        except Exception:
            return ""

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to clean text."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')

        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()

        text = soup.get_text(separator='\n')
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return '\n'.join(lines)
