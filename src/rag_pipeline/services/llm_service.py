import logging
import requests
from typing import List, Dict
from django.conf import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM integration (Ollama with OpenAI fallback)."""

    def __init__(self):
        self.ollama_base_url = settings.OLLAMA_BASE_URL
        self.ollama_model = settings.OLLAMA_MODEL
        self.openai_client = None

        # Initialize OpenAI client as fallback
        if settings.OPENAI_API_KEY:
            import openai
            self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_answer(self, query: str, chunks: List[Dict]) -> str:
        """
        Generate answer using LLM based on query and relevant chunks.

        Args:
            query: User query
            chunks: List of relevant document chunks

        Returns:
            Generated answer string
        """
        try:
            # Try Ollama first
            answer = self._generate_with_ollama(query, chunks)
            if answer:
                return answer

            # Fallback to OpenAI if Ollama fails
            if self.openai_client:
                return self._generate_with_openai(query, chunks)

            # If both fail, return a basic response
            return self._generate_basic_response(query, chunks)

        except Exception as e:
            logger.error(f"LLM answer generation failed: {str(e)}")
            return self._generate_basic_response(query, chunks)

    def _generate_with_ollama(self, query: str, chunks: List[Dict]) -> str:
        """Generate answer using Ollama."""
        try:
            # Prepare context from chunks
            context = self._prepare_context(chunks)

            # Create prompt
            prompt = f"""You are a financial analyst assistant. Answer the following question based on the provided context from Apple's 10-K filings.

Context:
{context}

Question: {query}

Please provide a clear, accurate answer based on the context. If the information is not available in the context, say so clearly.

Answer:"""

            # Make request to Ollama
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()

            return ""

        except Exception as e:
            logger.warning(f"Ollama generation failed: {str(e)}")
            return ""

    def _generate_with_openai(self, query: str, chunks: List[Dict]) -> str:
        """Generate answer using OpenAI as fallback."""
        try:
            context = self._prepare_context(chunks)

            prompt = f"""You are a financial analyst assistant. Answer the following question based on the provided context from Apple's 10-K filings.

Context:
{context}

Question: {query}

Please provide a clear, accurate answer based on the context. If the information is not available in the context, say so clearly.

Answer:"""

            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful financial analyst assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"OpenAI generation failed: {str(e)}")
            return ""

    def _generate_basic_response(self, query: str, chunks: List[Dict]) -> str:
        """Generate a basic response when LLM services fail."""
        if not chunks:
            return "I couldn't find relevant information to answer your question."

        # Return a simple response based on the most relevant chunk
        best_chunk = max(chunks, key=lambda x: x['similarity_score'])
        return f"Based on the available information: {best_chunk['chunk_text'][:300]}..."

    def _prepare_context(self, chunks: List[Dict]) -> str:
        """Prepare context string from chunks."""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"Source {i} (Section: {chunk.get('section', 'Unknown')}):\n"
                f"{chunk['chunk_text']}\n"
            )

        return "\n".join(context_parts)
