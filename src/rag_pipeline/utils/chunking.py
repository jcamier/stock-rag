import tiktoken
import logging
from typing import List, Dict
import re

logger = logging.getLogger(__name__)


class TextChunker:
    """Service for chunking text into manageable pieces."""

    def __init__(self, chunk_size: int = 600, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def chunk_text(self, text: str) -> List[Dict]:
        """
        Chunk text into overlapping pieces.

        Args:
            text: Input text to chunk

        Returns:
            List of chunk dictionaries with text and metadata
        """
        try:
            # Split text into sentences
            sentences = self._split_into_sentences(text)

            chunks = []
            current_chunk = []
            current_tokens = 0

            for sentence in sentences:
                sentence_tokens = len(self.encoding.encode(sentence))

                # If adding this sentence would exceed chunk size, finalize current chunk
                if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                    chunk_text = ' '.join(current_chunk)
                    chunks.append({
                        'text': chunk_text,
                        'token_count': current_tokens,
                        'section': self._detect_section(chunk_text)
                    })

                    # Start new chunk with overlap
                    current_chunk = self._get_overlap_chunk(current_chunk)
                    current_tokens = sum(len(self.encoding.encode(s)) for s in current_chunk)

                current_chunk.append(sentence)
                current_tokens += sentence_tokens

            # Add final chunk if it has content
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'token_count': current_tokens,
                    'section': self._detect_section(chunk_text)
                })

            return chunks

        except Exception as e:
            logger.error(f"Text chunking failed: {str(e)}")
            return [{'text': text, 'token_count': 0, 'section': 'Unknown'}]

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting - can be improved with more sophisticated NLP
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _get_overlap_chunk(self, previous_chunk: List[str]) -> List[str]:
        """Get overlap portion from previous chunk."""
        if len(previous_chunk) <= 2:
            return []

        # Take last 2-3 sentences for overlap
        overlap_sentences = previous_chunk[-2:]
        return overlap_sentences

    def _detect_section(self, text: str) -> str:
        """Detect which section of the 10-K this chunk belongs to."""
        text_lower = text.lower()

        # Management Discussion & Analysis
        if any(keyword in text_lower for keyword in ['management discussion', 'md&a', 'operating results']):
            return 'MD&A'

        # Financial Statements
        if any(keyword in text_lower for keyword in ['consolidated statements', 'balance sheet', 'income statement', 'cash flow']):
            return 'Financial Statements'

        # Risk Factors
        if any(keyword in text_lower for keyword in ['risk factors', 'risks and uncertainties']):
            return 'Risk Factors'

        # Business Overview
        if any(keyword in text_lower for keyword in ['business overview', 'products and services', 'market']):
            return 'Business Overview'

        return 'Other'
