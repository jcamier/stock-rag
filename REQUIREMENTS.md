# 10-K RAG Pipeline - Requirements Document

## Project Overview

### Purpose
This project is a **Proof of Concept (POC)** RAG pipeline built with Django for financial services. The system processes and vectorizes two Apple 10-K SEC filings to enable AI-powered querying of financial data.

### Primary Objectives
- **RAG Pipeline**: Building end-to-end RAG systems using Django, PostgreSQL with pgvector, and OpenAI embeddings
- **Financial Services Relevance**: Handle typical financial queries (revenue, profit margins, risk factors, etc.) from SEC 10-K documents
- **Agent Integration Ready**: Provide structured API responses with metadata suitable for LLM agent consumption


### Project Scope
- **Documents**: Two Apple 10-K filings (2023 and 2024) from SEC EDGAR database
- **Interface**: Single API endpoint (`/query`) for demonstration via Postman
- **Query Format**: Users specify year in queries (e.g., "Apple revenue 2023", "Apple profit margins 2024")
- **Response Structure**: Structured JSON with answer, sources, confidence scores, and metadata
- **Timeline**: Weekend POC completion (2 days)

### Success Criteria
- Accurate answers to financial queries from both years
- Response times under a few seconds on local laptop
- Clean, maintainable code architecture
- Professional API design suitable for agent integration
- Complete RAG pipeline demo

### Future Scalability
- Architecture designed to handle multiple companies' 10-K documents
- Currently limited to Apple documents for POC scope
- Foundation ready for production scaling

## Technical Architecture & Stack

### Backend Framework
- **Django 5.0+** with **Django REST Framework** for API endpoints
- **Single Django app** (`rag_pipeline`) for focused functionality
- **Django models** for document metadata, query history, and system tracking
- **Separation of concerns**: Django models for metadata, PostgreSQL+pgvector for RAG data

### Database Architecture
- **PostgreSQL 16** with **pgvector extension** for vector storage
  - Single database connection to allow for shared connection pooling
- **Django models** for:
  - Document metadata (company, year, filing_date, url, status)
  - Query history and performance tracking
  - System configuration and settings
- **PostgreSQL tables** for:
  - Document chunks (id, document_id, chunk_text, chunk_index)
  - Vector embeddings (chunk_id, embedding_vector, created_at)
  - Document content (parsed text, HTML content for future use)

### Document Processing Pipeline
- **Beautiful Soup** for HTML parsing and content extraction
- **Target sections** for POC:
  - Management Discussion & Analysis (MD&A)
  - Consolidated Financial Statements
  - Risk Factors (basic extraction)
- **Future enhancements**: Table extraction, footnote processing, cross-references

### Chunking Strategy
- **Fixed token count**: 500-800 tokens per chunk
- **Overlap**: 10-15% between chunks to preserve context
- **Chunking method**: Sentence-aware splitting to maintain readability
- **Metadata**: Track chunk position, source section, and document year

### Embedding & Vector Storage
- **OpenAI text-embedding-3-small** (cost-effective, high quality)
- **Vector dimensions**: 1536 (text-embedding-3-small)
- **Storage**: PostgreSQL with pgvector extension
- **Indexing**: HNSW index for fast similarity search
- **Caching**: Embedding caching for identical chunks (future enhancement)

### LLM Integration
- **Ollama** with **Llama 3.2** (latest) for local inference
- **Fallback**: OpenAI API for production reliability
- **Model management**: Local Ollama instance on local laptop
- **Context window**: 8K tokens for comprehensive responses

### Container Architecture
- **Django app**: Separate container with uv package management
- **PostgreSQL + pgvector**: Separate container with persistent volumes
- **Ollama**: Local installation (not containerized for performance)
- **Redis**: Separate container (future enhancement for caching)

### API Design
- **Endpoint**: `POST /api/query/` with JSON body
- **Request format**:
  ```json
  {
    "query": "What was Apple's revenue in 2023?",
    "year": "2023",
    "top_k": 5
  }
  ```
- **Response format**:
  ```json
  {
    "query": "What was Apple's revenue in 2023?",
    "answer": "Apple's revenue in 2023 was $383.3 billion...",
    "sources": [
      {
        "chunk_id": "chunk_123",
        "document": "aapl-20230930",
        "section": "Consolidated Statements of Operations",
        "relevance_score": 0.95,
        "snippet": "Net sales were $383.3 billion in fiscal 2023..."
      }
    ],
    "confidence": 0.92,
    "processing_time_ms": 1250,
    "year": "2023"
  }
  ```

### Development Tools
- **Package management**: uv for fast, reliable dependency management
- **Testing**: pytest for unit and integration tests
- **Code formatting**: ruff + black for consistent code style
- **Containerization**: Docker Compose for local development
- **Environment**: Python 3.11+ with type hints

### Telemetry & Monitoring
- **Langfuse 3.0+** for comprehensive tracking:
  - Query processing pipeline (embedding → retrieval → LLM)
  - Document ingestion (parsing → chunking → embedding)
  - System performance (response times, token usage, error rates)
  - LLM interactions and response quality
- **Logging**: Structured logging for debugging and monitoring
- **Metrics**: Custom metrics for RAG pipeline performance

### Security & Performance
- **Input validation**: Query sanitization and validation
- **Error handling**: Graceful error responses with meaningful messages
- **Rate limiting**: Basic rate limiting for API protection
- **Response optimization**: Efficient vector search and LLM inference

## Data Models & Database Schema

### Django Models

#### Document Model
```python
class Document(models.Model):
    company = models.CharField(max_length=100)
    year = models.IntegerField()
    filing_date = models.DateField()
    url = models.URLField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ])
    chunk_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### QueryHistory Model
```python
class QueryHistory(models.Model):
    query = models.TextField()
    year = models.IntegerField()
    response_time_ms = models.IntegerField()
    confidence_score = models.FloatField()
    sources_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
```

### PostgreSQL Tables (RAG Data)

#### Documents Table
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL,
    filing_date DATE NOT NULL,
    url TEXT NOT NULL,
    html_content TEXT,
    parsed_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Chunks Table
```sql
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id),
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    section VARCHAR(100),
    subsection VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Embeddings Table
```sql
CREATE TABLE embeddings (
    chunk_id UUID PRIMARY KEY REFERENCES chunks(id),
    embedding VECTOR(1536) NOT NULL,
    model_version VARCHAR(50) DEFAULT 'text-embedding-3-small',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create HNSW index for fast similarity search
CREATE INDEX ON embeddings USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 200);
```

## API Endpoints

### POST /api/query/
**Purpose**: Main RAG query endpoint for financial questions

**Request Body**:
```json
{
  "query": "What was Apple's revenue in 2023?",
  "year": "2023",
  "top_k": 5
}
```

**Response**:
```json
{
  "query": "What was Apple's revenue in 2023?",
  "answer": "Apple's revenue in 2023 was $383.3 billion...",
  "sources": [...],
  "confidence": 0.92,
  "processing_time_ms": 1250,
  "year": "2023"
}
```

### GET /api/health/
**Purpose**: Health check endpoint

**Response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "ollama": "connected",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### GET /api/stats/
**Purpose**: System statistics and performance metrics

**Response**:
```json
{
  "documents_processed": 2,
  "total_chunks": 1250,
  "total_queries": 45,
  "avg_response_time_ms": 1200,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

## Document Processing Pipeline

### 1. Document Ingestion
- Fetch HTML content from SEC EDGAR URLs
- Parse with Beautiful Soup
- Extract relevant sections (MD&A, Financial Statements, Risk Factors)
- Store raw HTML and parsed text in PostgreSQL

### 2. Chunking Process
- Split parsed text into 500-800 token chunks
- Maintain 10-15% overlap between chunks
- Preserve sentence boundaries
- Track section and subsection metadata

### 3. Embedding Generation
- Generate embeddings using OpenAI text-embedding-3-small
- Store 1536-dimensional vectors in PostgreSQL
- Create HNSW index for fast similarity search
- Cache embeddings to avoid re-processing

### 4. Query Processing
- Accept user query with year specification
- Generate query embedding using same model
- Perform vector similarity search with pgvector
- Retrieve top-k most relevant chunks
- Generate response using Ollama LLM
- Return structured response with sources

## Development Workflow

### Phase 1: Foundation Setup
1. **Docker Environment**: Set up Django + PostgreSQL containers
2. **Database Schema**: Create Django models and PostgreSQL tables
3. **Basic API**: Implement health check and stats endpoints
4. **Document Ingestion**: Build HTML parsing and storage pipeline

### Phase 2: RAG Implementation
1. **Chunking**: Implement text chunking with overlap
2. **Embeddings**: Integrate OpenAI embeddings and pgvector storage
3. **Query Processing**: Build vector search and retrieval
4. **LLM Integration**: Connect Ollama for response generation

### Phase 3: Integration & Testing
1. **End-to-End Pipeline**: Complete RAG workflow
2. **Error Handling**: Implement robust error handling
3. **Testing**: Unit and integration tests
4. **Performance**: Optimize response times

### Phase 4: Monitoring & Polish
1. **Langfuse Integration**: Add comprehensive telemetry
2. **API Documentation**: Complete endpoint documentation
3. **Demo Preparation**: Test with sample queries
4. **Code Quality**: Format and lint code

## File Structure

```
stock-rag/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .env
├── src/
│   ├── manage.py
│   ├── settings.py
│   ├── rag_pipeline/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── document_processor.py
│   │   │   ├── embedding_service.py
│   │   │   ├── query_processor.py
│   │   │   └── llm_service.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── chunking.py
│   │       └── html_parser.py
│   └── requirements/
│       ├── __init__.py
│       ├── base.py
│       ├── development.py
│       └── production.py
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   └── test_services.py
```

## Dependencies

### Core Dependencies
- **Django**: 5.0+
- **Django REST Framework**: 3.14+
- **PostgreSQL**: 16 with pgvector
- **OpenAI**: 1.0+ (for embeddings)
- **Ollama**: Latest (for LLM)
- **Langfuse**: 3.0+ (for telemetry)

### Python Packages
- **uv**: Fast package management
- **beautifulsoup4**: HTML parsing
- **psycopg2**: PostgreSQL adapter
- **pgvector**: Vector operations
- **pydantic**: Data validation
- **pytest**: Testing framework
- **ruff**: Code formatting
- **black**: Code formatting

## Environment Configuration

The project uses a `.env` file for environment variables. Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

See `.env.example` for all required environment variables.

## Success Metrics

### Technical Metrics
- **Response Time**: < 3 seconds for typical queries
- **Accuracy**: > 90% correct answers for financial questions
- **Uptime**: 99%+ availability during demo
- **Error Rate**: < 5% failed queries

### Business Metrics
- **Query Coverage**: Handle 80%+ of common financial questions
- **Source Quality**: Provide relevant citations for all answers
- **User Experience**: Intuitive API design for agent integration
- **Scalability**: Architecture ready for multiple companies

## Future Enhancements

### Short-term (Post-POC)
- **Redis Caching**: Implement embedding and response caching
- **Query Expansion**: Add synonym and related term expansion
- **Response Streaming**: Stream LLM responses for better UX
- **Batch Processing**: Process multiple queries simultaneously

### Medium-term
- **Multi-Company Support**: Extend to other companies' 10-Ks
- **Advanced Parsing**: Extract tables, footnotes, and cross-references
- **Semantic Search**: Implement hybrid text + vector search
- **API Authentication**: Add proper authentication and authorization

### Long-term
- **Production Deployment**: AWS/Azure deployment with scaling
- **Real-time Updates**: Automatic ingestion of new filings
- **Advanced Analytics**: Query analytics and insights dashboard
- **Multi-Modal RAG**: Support for charts, images, and tables

## Risk Mitigation

### Technical Risks
- **Ollama Performance**: Fallback to OpenAI API if local LLM fails
- **Vector Search Quality**: Implement query preprocessing and expansion
- **Memory Usage**: Monitor and optimize chunk sizes and batch processing
- **Database Performance**: Implement proper indexing and query optimization

### Business Risks
- **API Reliability**: Implement circuit breakers and retry logic
- **Data Quality**: Validate document parsing and chunking quality
- **Response Accuracy**: Implement confidence scoring and validation
- **Demo Preparation**: Thorough testing with sample queries

## Conclusion

This RAG pipeline POC demonstrates proficiency in:
- **End-to-end RAG architecture** with Django and PostgreSQL
- **Vector database integration** with pgvector
- **LLM orchestration** with Ollama and OpenAI
- **Financial document processing** with Beautiful Soup
- **Professional API design** suitable for agent integration
- **Comprehensive telemetry** with Langfuse
- **Containerized deployment** with Docker

The project provides a solid foundation for production RAG systems while maintaining simplicity appropriate for a weekend POC demonstration.
