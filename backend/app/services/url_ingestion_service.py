"""URL ingestion service for web pages."""
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup
from flask import current_app

from ..extensions import db
from ..models import Document
from .chunking_service import ChunkingService


class URLIngestionService:
    """Service for ingesting web pages as documents."""

    USER_AGENT = 'ChatGepeto/1.0 (RAG Knowledge Base)'
    TIMEOUT = 30
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB

    def __init__(self):
        self.chunking_service = ChunkingService()

    def fetch_url(self, url: str) -> tuple:
        """Fetch URL content. Returns (html_content, title)."""
        headers = {'User-Agent': self.USER_AGENT}

        response = requests.get(
            url,
            headers=headers,
            timeout=self.TIMEOUT,
            stream=True
        )
        response.raise_for_status()

        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > self.MAX_CONTENT_LENGTH:
            raise ValueError(f"Content too large: {content_length} bytes")

        content = response.text

        soup = BeautifulSoup(content, 'lxml')
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else url

        return content, title

    def extract_content(self, html: str) -> str:
        """Extract main content from HTML."""
        return self.chunking_service._html_to_text(html)

    def create_document_from_url(
        self,
        url: str,
        user_id: int,
        title: Optional[str] = None
    ) -> Document:
        """Fetch URL and create document with chunks."""
        html_content, fetched_title = self.fetch_url(url)
        text_content = self.extract_content(html_content)

        if not text_content.strip():
            raise ValueError("No text content found at URL")

        document = Document(
            user_id=user_id,
            title=title or fetched_title[:255],
            file='',
            file_type='text/html',
            file_size=len(text_content.encode('utf-8')),
            status='processing'
        )
        db.session.add(document)
        db.session.commit()

        # Save extracted text to file
        document.file = f"urls/{document.id}.txt"
        file_path = Path(current_app.config['UPLOAD_FOLDER']) / document.file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(text_content)
        db.session.commit()

        # Create chunks
        try:
            self.chunking_service.chunk_document(document)
            document.status = 'completed'
            db.session.commit()
        except Exception:
            document.status = 'failed'
            db.session.commit()
            raise

        return document
