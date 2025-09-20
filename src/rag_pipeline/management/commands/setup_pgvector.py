from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Setup pgvector extension and create necessary tables'

    def handle(self, *args, **options):
        self.stdout.write('Setting up pgvector extension...')

        try:
            with connection.cursor() as cursor:
                # Enable pgvector extension
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                self.stdout.write(self.style.SUCCESS('✓ pgvector extension enabled'))

                # Create documents table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        company VARCHAR(100) NOT NULL,
                        year INTEGER NOT NULL,
                        filing_date DATE NOT NULL,
                        url TEXT NOT NULL,
                        html_content TEXT,
                        parsed_text TEXT,
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                self.stdout.write(self.style.SUCCESS('✓ documents table created'))

                # Create chunks table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chunks (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
                        chunk_index INTEGER NOT NULL,
                        chunk_text TEXT NOT NULL,
                        section VARCHAR(100),
                        subsection VARCHAR(100),
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                self.stdout.write(self.style.SUCCESS('✓ chunks table created'))

                # Create embeddings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS embeddings (
                        chunk_id UUID PRIMARY KEY REFERENCES chunks(id) ON DELETE CASCADE,
                        embedding VECTOR(1536) NOT NULL,
                        model_version VARCHAR(50) DEFAULT 'text-embedding-3-small',
                        created_at TIMESTAMP DEFAULT NOW()
                    );
                """)
                self.stdout.write(self.style.SUCCESS('✓ embeddings table created'))

                # Create HNSW index
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS embeddings_embedding_idx ON embeddings USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 200);
                """)
                self.stdout.write(self.style.SUCCESS('✓ HNSW index created'))

                # Create additional indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS documents_company_year_idx ON documents (company, year);")
                cursor.execute("CREATE INDEX IF NOT EXISTS chunks_document_id_idx ON chunks (document_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS chunks_section_idx ON chunks (section);")
                self.stdout.write(self.style.SUCCESS('✓ Additional indexes created'))

            self.stdout.write(self.style.SUCCESS('\n✓ pgvector setup completed successfully!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Setup failed: {str(e)}'))
            raise
