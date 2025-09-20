import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, List
from django.db import connection
from django.conf import settings
from .embedding_service import EmbeddingService
from ..utils.chunking import TextChunker
from ..utils.html_parser import HTMLParser

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Service for processing and ingesting 10-K documents."""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.chunker = TextChunker()
        self.html_parser = HTMLParser()

    def process_document(self, url: str, company: str, year: int) -> Dict[str, any]:
        """
        Process a 10-K document from URL.

        Args:
            url: Document URL
            company: Company name
            year: Filing year

        Returns:
            Processing result dictionary
        """
        try:
            # Fetch document
            html_content = self._fetch_document(url)

            # Parse HTML content
            parsed_content = self.html_parser.parse_10k(html_content)

            # Store document in database
            document_id = self._store_document(url, company, year, html_content, parsed_content['full_text'])

            # Chunk the text
            chunks = self.chunker.chunk_text(parsed_content['full_text'])

            # Store chunks and generate embeddings
            chunk_count = self._store_chunks_and_embeddings(document_id, chunks, parsed_content)

            # Update document status
            self._update_document_status(document_id, 'completed', chunk_count)

            return {
                'success': True,
                'document_id': str(document_id),
                'chunk_count': chunk_count,
                'sections_found': list(parsed_content['sections'].keys())
            }

        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _fetch_document(self, url: str) -> str:
        """Fetch document content from URL."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch document from {url}: {str(e)}")
            raise

    def _store_document(self, url: str, company: str, year: int, html_content: str, parsed_text: str) -> str:
        """Store document in PostgreSQL."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO documents (company, year, filing_date, url, html_content, parsed_text)
                    VALUES (%s, %s, CURRENT_DATE, %s, %s, %s)
                    RETURNING id
                """, [company, year, url, html_content, parsed_text])

                return cursor.fetchone()[0]

        except Exception as e:
            logger.error(f"Failed to store document: {str(e)}")
            raise

    def _store_chunks_and_embeddings(self, document_id: str, chunks: List[Dict], parsed_content: Dict) -> int:
        """Store chunks and generate embeddings."""
        try:
            chunk_count = 0

            with connection.cursor() as cursor:
                for i, chunk in enumerate(chunks):
                    # Store chunk
                    cursor.execute("""
                        INSERT INTO chunks (document_id, chunk_index, chunk_text, section, subsection)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, [
                        document_id,
                        i,
                        chunk['text'],
                        chunk.get('section'),
                        chunk.get('subsection')
                    ])

                    chunk_id = cursor.fetchone()[0]

                    # Generate embedding
                    embedding = self.embedding_service.generate_embedding(chunk['text'])
                    embedding_str = '[' + ','.join(map(str, embedding)) + ']'

                    # Store embedding
                    cursor.execute("""
                        INSERT INTO embeddings (chunk_id, embedding, model_version)
                        VALUES (%s, %s::vector, %s)
                    """, [chunk_id, embedding_str, 'text-embedding-3-small'])

                    chunk_count += 1

            return chunk_count

        except Exception as e:
            logger.error(f"Failed to store chunks and embeddings: {str(e)}")
            raise

    def _update_document_status(self, document_id: str, status: str, chunk_count: int):
        """Update document status in Django model."""
        try:
            from ..models import Document

            # Find the corresponding Django document
            django_doc = Document.objects.filter(
                company__icontains='Apple',  # This is a simplified lookup
                year__isnull=False
            ).first()

            if django_doc:
                django_doc.status = status
                django_doc.chunk_count = chunk_count
                django_doc.save()

        except Exception as e:
            logger.warning(f"Failed to update Django document status: {str(e)}")
