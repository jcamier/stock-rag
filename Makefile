# Makefile for 10-K RAG Pipeline POC

.PHONY: help up down build migrations test clean logs setup ingest

# Default target
help:
	@echo "Available commands:"
	@echo "  up        - Start all services with docker-compose"
	@echo "  down      - Stop all services"
	@echo "  build     - Build all Docker images"
	@echo "  setup     - Complete project setup (migrations + pgvector + superuser)"
	@echo "  migrations - Run Django migrations"
	@echo "  superuser - Create superuser (interactive)"
	@echo "  superuser-auto - Create superuser automatically (demo)"
	@echo "  test      - Run tests"
	@echo "  clean     - Clean up containers and volumes"
	@echo "  logs      - Show logs from all services"
	@echo "  ingest    - Ingest Apple 10-K documents"
	@echo "  populate  - Populate embeddings for documents"
	@echo ""
	@echo "Python dependency management (uv):"
	@echo "  install   - Install Python dependencies"
	@echo "  export-req - Export requirements.txt from pyproject.toml"

# Start all services
up: down
	docker-compose up -d

# Stop all services
down:
	docker-compose down

# Build all images
build:
	docker-compose build

# Complete project setup
setup: migrations setup-pgvector superuser-auto
	@echo "Project setup complete!"

# Run migrations
migrations:
	docker-compose exec backend python manage.py makemigrations
	docker-compose exec backend python manage.py migrate

# Create superuser (interactive)
superuser:
	docker-compose exec backend python manage.py createsuperuser

# Create superuser automatically (for demo)
superuser-auto:
	docker-compose exec backend python manage.py createsuperuser --username admin --email admin@example.com --noinput
	docker-compose exec backend python manage.py shell -c "from django.contrib.auth.models import User; u = User.objects.get(username='admin'); u.set_password('admin123'); u.save()"

# Run tests
test:
	docker-compose exec backend python -m pytest

# Clean up
clean:
	docker-compose down -v
	docker system prune -f

# Show logs
logs:
	docker-compose logs -f

# Show backend logs only
logs-backend:
	docker-compose logs -f backend

# Shell into backend container
shell:
	docker-compose exec backend bash

# Install Python dependencies
install:
	uv pip install -e .

# Generate requirements.txt from pyproject.toml (if needed for compatibility)
export-req:
	uv export --format requirements-txt > requirements.txt

# Ingest Apple 10-K documents
ingest:
	docker-compose exec backend python manage.py ingest_documents

# Populate embeddings for documents
populate:
	docker-compose exec backend python manage.py populate_embeddings

# Run Django development server locally
run-local:
	cd src && python manage.py runserver

# Collect static files
collectstatic:
	docker-compose exec backend python manage.py collectstatic --noinput

# Setup pgvector extension
setup-pgvector:
	docker-compose exec backend python manage.py setup_pgvector

# Test API endpoints
test-api:
	@echo "Testing API endpoints..."
	@echo "Health check:"
	@curl -s http://localhost:8000/api/health/ | python3 -m json.tool
	@echo "\nStats:"
	@curl -s http://localhost:8000/api/stats/ | python3 -m json.tool

