from django.core.management.base import BaseCommand
from django.db import connection
from rag_pipeline.services.embedding_service import EmbeddingService


class Command(BaseCommand):
    help = 'Populate embeddings for existing chunks (if not already generated)'

    def handle(self, *args, **options):
        self.stdout.write('Populating embeddings for existing chunks...')

        embedding_service = EmbeddingService()

        try:
            with connection.cursor() as cursor:
                # Find chunks without embeddings
                cursor.execute("""
                    SELECT c.id, c.chunk_text
                    FROM chunks c
                    LEFT JOIN embeddings e ON c.id = e.chunk_id
                    WHERE e.chunk_id IS NULL
                """)

                chunks_to_process = cursor.fetchall()

                if not chunks_to_process:
                    self.stdout.write('No chunks need embedding generation.')
                    return

                self.stdout.write(f'Found {len(chunks_to_process)} chunks to process...')

                processed_count = 0

                for chunk_id, chunk_text in chunks_to_process:
                    try:
                        # Generate embedding
                        embedding = embedding_service.generate_embedding(chunk_text)
                        embedding_str = '[' + ','.join(map(str, embedding)) + ']'

                        # Store embedding
                        cursor.execute("""
                            INSERT INTO embeddings (chunk_id, embedding, model_version)
                            VALUES (%s, %s::vector, %s)
                        """, [chunk_id, embedding_str, 'text-embedding-3-small'])

                        processed_count += 1

                        if processed_count % 10 == 0:
                            self.stdout.write(f'  Processed {processed_count} chunks...')

                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'  Failed to process chunk {chunk_id}: {str(e)}')
                        )

                self.stdout.write(
                    self.style.SUCCESS(f'✓ Embedding population completed! {processed_count} embeddings generated.')
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Embedding population failed: {str(e)}'))
            raise
