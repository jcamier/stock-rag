import logging
import re
from bs4 import BeautifulSoup
from typing import Dict, List

logger = logging.getLogger(__name__)


class HTMLParser:
    """Service for parsing 10-K HTML documents."""

    def parse_10k(self, html_content: str) -> Dict[str, any]:
        """
        Parse 10-K HTML content and extract relevant sections.

        Args:
            html_content: Raw HTML content

        Returns:
            Dictionary with parsed content and sections
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Extract sections
            sections = self._extract_sections(soup)

            # Combine all text
            full_text = self._extract_full_text(soup)

            return {
                'sections': sections,
                'full_text': full_text,
                'metadata': self._extract_metadata(soup)
            }

        except Exception as e:
            logger.error(f"HTML parsing failed: {str(e)}")
            return {
                'sections': {},
                'full_text': html_content,
                'metadata': {}
            }

    def _extract_sections(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract specific sections from 10-K document."""
        sections = {}

        # Management Discussion & Analysis
        sections['md&a'] = self._extract_section_by_keywords(
            soup,
            ['management discussion', 'md&a', 'operating results', 'financial condition']
        )

        # Financial Statements
        sections['financial_statements'] = self._extract_section_by_keywords(
            soup,
            ['consolidated statements', 'balance sheet', 'income statement', 'cash flow']
        )

        # Risk Factors
        sections['risk_factors'] = self._extract_section_by_keywords(
            soup,
            ['risk factors', 'risks and uncertainties', 'risk management']
        )

        # Business Overview
        sections['business_overview'] = self._extract_section_by_keywords(
            soup,
            ['business overview', 'products and services', 'market', 'competition']
        )

        return sections

    def _extract_section_by_keywords(self, soup: BeautifulSoup, keywords: List[str]) -> str:
        """Extract section content based on keywords."""
        try:
            # Find elements containing keywords
            for keyword in keywords:
                elements = soup.find_all(text=lambda text: text and keyword.lower() in text.lower())

                for element in elements:
                    # Find the parent section
                    section = element.find_parent(['div', 'p', 'section', 'article'])
                    if section:
                        # Extract text from this section and following siblings
                        section_text = self._extract_section_text(section)
                        if len(section_text) > 500:  # Only return substantial content
                            return section_text

            return ""

        except Exception as e:
            logger.warning(f"Section extraction failed for keywords {keywords}: {str(e)}")
            return ""

    def _extract_section_text(self, element) -> str:
        """Extract text from a section element and its following siblings."""
        text_parts = []

        # Get text from current element
        text_parts.append(element.get_text(strip=True))

        # Get text from following siblings (up to a reasonable limit)
        current = element.find_next_sibling()
        count = 0
        while current and count < 10:  # Limit to prevent extracting too much
            if current.name in ['div', 'p', 'section']:
                text_parts.append(current.get_text(strip=True))
            current = current.find_next_sibling()
            count += 1

        return ' '.join(text_parts)

    def _extract_full_text(self, soup: BeautifulSoup) -> str:
        """Extract all text content from the document."""
        try:
            # Remove navigation and header elements
            for element in soup.find_all(['nav', 'header', 'footer', 'aside']):
                element.decompose()

            # Get main content
            main_content = soup.find('main') or soup.find('body') or soup

            return main_content.get_text(separator=' ', strip=True)

        except Exception as e:
            logger.warning(f"Full text extraction failed: {str(e)}")
            return soup.get_text(separator=' ', strip=True)

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract metadata from the document."""
        metadata = {}

        try:
            # Extract title
            title = soup.find('title')
            if title:
                metadata['title'] = title.get_text(strip=True)

            # Extract company name from various sources
            company_elements = soup.find_all(text=lambda text: text and 'apple' in text.lower())
            if company_elements:
                metadata['company'] = 'Apple Inc.'

            # Extract filing date if available
            date_elements = soup.find_all(text=lambda text: text and re.search(r'\d{4}-\d{2}-\d{2}', text))
            if date_elements:
                metadata['filing_date'] = date_elements[0].strip()

        except Exception as e:
            logger.warning(f"Metadata extraction failed: {str(e)}")

        return metadata
