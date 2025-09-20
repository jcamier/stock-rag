# 10-K RAG Pipeline POC

A Proof of Concept RAG (Retrieval-Augmented Generation) pipeline built with Django for financial services. This system processes and vectorizes Apple 10-K SEC filings to enable AI-powered querying of financial data.

## Features

- **RAG Pipeline**: End-to-end RAG system using Django, PostgreSQL with pgvector, and OpenAI embeddings
- **Financial Document Processing**: Handles Apple 10-K filings with Beautiful Soup parsing
- **Vector Search**: Fast similarity search using pgvector HNSW indexing
- **LLM Integration**: Local Ollama with OpenAI fallback for response generation
- **REST API**: Clean API design suitable for agent integration
- **Docker Support**: Containerized deployment with Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- OpenAI API key
- (Optional) Ollama for local LLM inference

### Setup

1. **Clone and navigate to the project:**
   ```bash
   cd /Users/jacquescamier/PythonProjects/stock-rag
   ```

2. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your OpenAI API key and other settings
   ```

3. **Start the services:**
   ```bash
   make up
   ```

4. **Set up the database and ingest documents:**
   ```bash
   make setup
   make ingest
   ```

5. **Test the API:**
   ```bash
   make test-api
   ```

### Available Commands

```bash
# Service management
make up          # Start all services
make down        # Stop all services
make build       # Build Docker images
make logs        # View logs

# Database setup
make setup       # Complete setup (migrations + pgvector + superuser)
make migrations  # Run Django migrations
make setup-pgvector  # Setup pgvector extension

# Document processing
make ingest      # Ingest Apple 10-K documents
make populate    # Populate embeddings for documents

# Testing
make test        # Run tests
make test-api    # Test API endpoints

# Development
make shell       # Shell into backend container
make install     # Install Python dependencies
```

## API Endpoints

### POST /api/query/
Query the RAG system with financial questions.

**Request:**
```json
{
  "query": "What was Apple's revenue in 2023?",
  "year": 2023,
  "top_k": 5
}
```

**Response:**
```json
{
  "query": "What was Apple's revenue in 2023?",
  "answer": "Apple's revenue in 2023 was $383.3 billion...",
  "sources": [...],
  "confidence": 0.92,
  "processing_time_ms": 1250,
  "year": 2023
}
```

### GET /api/health/
Health check endpoint.

### GET /api/stats/
System statistics and performance metrics.

## Architecture

- **Backend**: Django 5.0+ with Django REST Framework
- **Database**: PostgreSQL 16 with pgvector extension
- **Vector Storage**: 1536-dimensional embeddings using OpenAI text-embedding-3-small
- **LLM**: Ollama (local) with OpenAI fallback
- **Document Processing**: Beautiful Soup for HTML parsing
- **Containerization**: Docker Compose for local development

## Project Structure

```
stock-rag/
├── docker-compose.yml          # Docker services configuration
├── Dockerfile                  # Django app container
├── pyproject.toml             # Python dependencies and project config
├── Makefile                   # Development commands
├── src/                       # Django application
│   ├── manage.py              # Django management script
│   ├── settings.py            # Django settings
│   ├── urls.py                # URL routing
│   └── rag_pipeline/          # Main Django app
│       ├── models.py          # Django models
│       ├── views.py           # API views
│       ├── serializers.py     # API serializers
│       ├── services/          # Business logic services
│       ├── utils/             # Utility functions
│       └── management/        # Django management commands
├── scripts/                   # Database initialization scripts
└── tests/                     # Test suite
```

## Development

### Local Development Setup

1. **Install dependencies:**
   ```bash
   make install
   ```

2. **Run locally:**
   ```bash
   make run-local
   ```

### Testing

```bash
make test              # Run all tests
make test-api          # Test API endpoints
```

## Configuration

Key environment variables in `.env`:

- `DB_NAME`: Database name (default: stock_rag)
- `DB_USER`: Database user (default: postgres)
- `DB_PASS`: Database password (default: postgres)
- `DB_HOST`: Database host (default: db)
- `OPENAI_API_KEY`: Your OpenAI API key
- `LANGFUSE_PUBLIC_KEY`: Langfuse public key (optional)
- `LANGFUSE_SECRET_KEY`: Langfuse secret key (optional)
- `OLLAMA_BASE_URL`: Ollama server URL (default: http://localhost:11434)

## Troubleshooting

### Common Issues

1. **Database connection errors**: Ensure PostgreSQL container is running and healthy
2. **OpenAI API errors**: Check your API key and rate limits
3. **Ollama connection issues**: Ensure Ollama is running locally or disable it

### Logs

```bash
make logs              # All services
make logs-backend      # Backend only
```

## License

This is a proof of concept project for demonstration purposes.
