from rest_framework import serializers
from .models import Document, QueryHistory, SystemConfig


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'


class QueryHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryHistory
        fields = '__all__'


class QueryRequestSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=1000)
    year = serializers.IntegerField()
    top_k = serializers.IntegerField(default=5, min_value=1, max_value=20)


class QueryResponseSerializer(serializers.Serializer):
    query = serializers.CharField()
    answer = serializers.CharField()
    sources = serializers.ListField()
    confidence = serializers.FloatField()
    processing_time_ms = serializers.IntegerField()
    year = serializers.IntegerField()


class HealthResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    database = serializers.CharField()
    ollama = serializers.CharField()
    timestamp = serializers.DateTimeField()


class StatsResponseSerializer(serializers.Serializer):
    documents_processed = serializers.IntegerField()
    total_chunks = serializers.IntegerField()
    total_queries = serializers.IntegerField()
    avg_response_time_ms = serializers.FloatField()
    last_updated = serializers.DateTimeField()
