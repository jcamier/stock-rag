from django.db import models
from django.utils import timezone
from pgvector.django import VectorField


class Document(models.Model):
    """Model for tracking 10-K documents."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    company = models.CharField(max_length=100)
    year = models.IntegerField()
    filing_date = models.DateField()
    url = models.URLField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    chunk_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['company', 'year']
        ordering = ['-year', 'company']

    def __str__(self):
        return f"{self.company} {self.year} 10-K"


class Chunk(models.Model):
    """Model for storing document chunks."""

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField()
    chunk_text = models.TextField()
    section = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['document', 'chunk_index']
        ordering = ['document', 'chunk_index']

    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document}"


class Embedding(models.Model):
    """Model for storing vector embeddings of chunks."""

    chunk = models.OneToOneField(Chunk, on_delete=models.CASCADE, related_name='embedding')
    embedding = VectorField(dimensions=1536)  # OpenAI text-embedding-3-small dimensions
    model_name = models.CharField(max_length=100, default='text-embedding-3-small')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Embedding for {self.chunk}"


class QueryHistory(models.Model):
    """Model for tracking query history and performance."""

    query = models.TextField()
    year = models.IntegerField()
    response_time_ms = models.IntegerField()
    confidence_score = models.FloatField()
    sources_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Query {self.id}: {self.query[:50]}..."


class SystemConfig(models.Model):
    """Model for system configuration and settings."""

    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key}: {self.value}"
