from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rag_pipeline.models import Document, QueryHistory


class HealthViewTest(APITestCase):
    def test_health_endpoint(self):
        """Test health check endpoint."""
        url = reverse('health')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertIn('database', response.data)
        self.assertIn('timestamp', response.data)


class StatsViewTest(APITestCase):
    def test_stats_endpoint(self):
        """Test stats endpoint."""
        url = reverse('stats')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('documents_processed', response.data)
        self.assertIn('total_chunks', response.data)
        self.assertIn('total_queries', response.data)


class QueryViewTest(APITestCase):
    def test_query_endpoint_invalid_data(self):
        """Test query endpoint with invalid data."""
        url = reverse('query')
        data = {'query': 'test query'}  # Missing required fields
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_query_endpoint_valid_data(self):
        """Test query endpoint with valid data."""
        url = reverse('query')
        data = {
            'query': 'What was Apple revenue in 2023?',
            'year': 2023,
            'top_k': 5
        }
        response = self.client.post(url, data, format='json')

        # Should return 200 even if no documents are processed yet
        # (will return "No relevant information found" message)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('answer', response.data)
        self.assertIn('sources', response.data)
        self.assertIn('confidence', response.data)
