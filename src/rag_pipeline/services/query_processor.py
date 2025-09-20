import logging
from typing import Dict, List, Any
from django.db import connection
from .embedding_service import EmbeddingService
from .llm_service import LLMService

logger = logging.getLogger(__name__)


class QueryProcessor:
    """Main query processing service for RAG pipeline."""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.llm_service = LLMService()

    def process_query(self, query: str, year: int, top_k: int = 5) -> Dict[str, Any]:
        """
        Process a query through the RAG pipeline.

        Args:
            query: User query string
            year: Year to filter documents
            top_k: Number of top chunks to retrieve

        Returns:
            Dictionary with answer, sources, and metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.generate_embedding(query)

            # Retrieve relevant chunks
            relevant_chunks = self._retrieve_chunks(query_embedding, year, top_k)

            if not relevant_chunks:
                return {
                    'answer': 'No relevant information found for your query.',
                    'sources': [],
                    'confidence': 0.0
                }

            # Generate answer using LLM
            answer = self.llm_service.generate_answer(query, relevant_chunks)

            # Calculate confidence based on relevance scores
            confidence = self._calculate_confidence(relevant_chunks)

            # Format sources
            sources = self._format_sources(relevant_chunks)

            return {
                'answer': answer,
                'sources': sources,
                'confidence': confidence
            }

        except Exception as e:
            logger.error(f"Query processing failed: {str(e)}")
            raise

    def _retrieve_chunks(self, query_embedding: List[float], year: int, top_k: int) -> List[Dict]:
        """Retrieve most relevant chunks using vector similarity search."""
        try:
            with connection.cursor() as cursor:
                # Convert embedding to PostgreSQL array format
                embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'

                # Query for similar chunks using cosine similarity
                query = """
                SELECT
                    c.id,
                    c.chunk_text,
                    c.section,
                    c.subsection,
                    d.company,
                    d.year,
                    d.filing_date,
                    1 - (e.embedding <=> %s::vector) as similarity_score
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                JOIN embeddings e ON c.id = e.chunk_id
                WHERE d.year = %s
                ORDER BY e.embedding <=> %s::vector
                LIMIT %s
                """

                cursor.execute(query, [embedding_str, year, embedding_str, top_k])
                results = cursor.fetchall()

                chunks = []
                for row in results:
                    chunks.append({
                        'chunk_id': str(row[0]),
                        'chunk_text': row[1],
                        'section': row[2],
                        'subsection': row[3],
                        'company': row[4],
                        'year': row[5],
                        'filing_date': row[6],
                        'similarity_score': float(row[7])
                    })

                return chunks

        except Exception as e:
            logger.error(f"Chunk retrieval failed: {str(e)}")
            raise

    def _calculate_confidence(self, chunks: List[Dict]) -> float:
        """Calculate confidence score based on similarity scores."""
        if not chunks:
            return 0.0

        # Use the highest similarity score as base confidence
        max_similarity = max(chunk['similarity_score'] for chunk in chunks)

        # Adjust based on number of relevant chunks
        chunk_factor = min(len(chunks) / 3.0, 1.0)  # Cap at 1.0 for 3+ chunks

        confidence = max_similarity * chunk_factor
        return min(confidence, 1.0)  # Cap at 1.0

    def _format_sources(self, chunks: List[Dict]) -> List[Dict]:
        """Format chunks as source citations."""
        sources = []
        for chunk in chunks:
            sources.append({
                'chunk_id': chunk['chunk_id'],
                'document': f"{chunk['company']}-{chunk['year']}",
                'section': chunk['section'] or 'Unknown',
                'relevance_score': chunk['similarity_score'],
                'snippet': chunk['chunk_text'][:200] + '...' if len(chunk['chunk_text']) > 200 else chunk['chunk_text']
            })

        return sources
