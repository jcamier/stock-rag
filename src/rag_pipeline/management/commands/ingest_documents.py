from django.core.management.base import BaseCommand
from django.conf import settings
from rag_pipeline.services.document_processor import DocumentProcessor
from rag_pipeline.models import Document


class Command(BaseCommand):
    help = 'Ingest Apple 10-K documents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            help='Specific year to ingest (2023 or 2024)',
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting document ingestion...')

        processor = DocumentProcessor()

        # Define documents to ingest
        documents = [
            {
                'url': settings.AAPL_2023_10K_URL,
                'company': 'Apple Inc.',
                'year': 2023
            },
            {
                'url': settings.AAPL_2024_10K_URL,
                'company': 'Apple Inc.',
                'year': 2024
            }
        ]

        # Filter by year if specified
        if options['year']:
            documents = [doc for doc in documents if doc['year'] == options['year']]

        success_count = 0

        for doc_info in documents:
            self.stdout.write(f'Processing {doc_info["company"]} {doc_info["year"]} 10-K...')

            # Create Django document record
            django_doc, created = Document.objects.get_or_create(
                company=doc_info['company'],
                year=doc_info['year'],
                defaults={
                    'filing_date': '2023-09-30' if doc_info['year'] == 2023 else '2024-09-28',
                    'url': doc_info['url'],
                    'status': 'processing'
                }
            )

            if not created:
                self.stdout.write(f'  Document already exists, skipping...')
                continue

            # Process document
            result = processor.process_document(
                doc_info['url'],
                doc_info['company'],
                doc_info['year']
            )

            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Successfully processed {result["chunk_count"]} chunks'
                    )
                )
                success_count += 1
            else:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Failed: {result["error"]}')
                )
                django_doc.status = 'failed'
                django_doc.save()

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Document ingestion completed! {success_count} documents processed.')
        )
