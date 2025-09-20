import time
from datetime import datetime
from django.db import connection
from django.db.models import Avg
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Document, QueryHistory
from .serializers import (
    QueryRequestSerializer,
    QueryResponseSerializer,
    HealthResponseSerializer,
    StatsResponseSerializer,
)
from .services.query_processor import QueryProcessor


class QueryView(APIView):
    """Main RAG query endpoint for financial questions."""

    def post(self, request):
        start_time = time.time()

        # Validate request
        serializer = QueryRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        query_data = serializer.validated_data
        query = query_data['query']
        year = query_data['year']
        top_k = query_data['top_k']

        try:
            # Process query using RAG pipeline
            query_processor = QueryProcessor()
            result = query_processor.process_query(query, year, top_k)

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Save query history
            QueryHistory.objects.create(
                query=query,
                year=year,
                response_time_ms=processing_time_ms,
                confidence_score=result.get('confidence', 0.0),
                sources_count=len(result.get('sources', []))
            )

            # Prepare response
            response_data = {
                'query': query,
                'answer': result.get('answer', 'No answer found'),
                'sources': result.get('sources', []),
                'confidence': result.get('confidence', 0.0),
                'processing_time_ms': processing_time_ms,
                'year': year,
            }

            response_serializer = QueryResponseSerializer(data=response_data)
            if response_serializer.is_valid():
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(response_serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response(
                {'error': f'Query processing failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HealthView(APIView):
    """Health check endpoint."""

    def get(self, request):
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            database_status = "connected"
        except Exception:
            database_status = "disconnected"

        # Check Ollama connection (simplified for now)
        ollama_status = "connected"  # TODO: Implement actual Ollama health check

        response_data = {
            'status': 'healthy' if database_status == 'connected' else 'unhealthy',
            'database': database_status,
            'ollama': ollama_status,
            'timestamp': timezone.now(),
        }

        serializer = HealthResponseSerializer(data=response_data)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StatsView(APIView):
    """System statistics and performance metrics."""

    def get(self, request):
        # Get document statistics
        documents_processed = Document.objects.filter(status='completed').count()

        # Get total chunks from PostgreSQL (using raw SQL for pgvector tables)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM chunks")
                total_chunks = cursor.fetchone()[0]
        except Exception:
            total_chunks = 0

        # Get query statistics
        total_queries = QueryHistory.objects.count()
        avg_response_time = QueryHistory.objects.aggregate(
            avg_time=Avg('response_time_ms')
        )['avg_time'] or 0

        response_data = {
            'documents_processed': documents_processed,
            'total_chunks': total_chunks,
            'total_queries': total_queries,
            'avg_response_time_ms': round(avg_response_time, 2),
            'last_updated': timezone.now(),
        }

        serializer = StatsResponseSerializer(data=response_data)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
