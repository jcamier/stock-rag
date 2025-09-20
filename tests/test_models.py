from django.test import TestCase
from django.utils import timezone
from rag_pipeline.models import Document, QueryHistory, SystemConfig


class DocumentModelTest(TestCase):
    def test_document_creation(self):
        """Test creating a document instance."""
        document = Document.objects.create(
            company='Apple Inc.',
            year=2023,
            filing_date='2023-09-30',
            url='https://example.com/aapl-2023.htm',
            status='pending'
        )

        self.assertEqual(document.company, 'Apple Inc.')
        self.assertEqual(document.year, 2023)
        self.assertEqual(document.status, 'pending')
        self.assertEqual(str(document), 'Apple Inc. 2023 10-K')

    def test_document_unique_constraint(self):
        """Test that company-year combination is unique."""
        Document.objects.create(
            company='Apple Inc.',
            year=2023,
            filing_date='2023-09-30',
            url='https://example.com/aapl-2023.htm'
        )

        with self.assertRaises(Exception):
            Document.objects.create(
                company='Apple Inc.',
                year=2023,
                filing_date='2023-09-30',
                url='https://example.com/aapl-2023-duplicate.htm'
            )


class QueryHistoryModelTest(TestCase):
    def test_query_history_creation(self):
        """Test creating a query history instance."""
        query_history = QueryHistory.objects.create(
            query='What was Apple revenue in 2023?',
            year=2023,
            response_time_ms=1500,
            confidence_score=0.85,
            sources_count=3
        )

        self.assertEqual(query_history.query, 'What was Apple revenue in 2023?')
        self.assertEqual(query_history.year, 2023)
        self.assertEqual(query_history.confidence_score, 0.85)
        self.assertIn('Query 1:', str(query_history))


class SystemConfigModelTest(TestCase):
    def test_system_config_creation(self):
        """Test creating a system config instance."""
        config = SystemConfig.objects.create(
            key='embedding_model',
            value='text-embedding-3-small',
            description='OpenAI embedding model used'
        )

        self.assertEqual(config.key, 'embedding_model')
        self.assertEqual(config.value, 'text-embedding-3-small')
        self.assertEqual(str(config), 'embedding_model: text-embedding-3-small')
