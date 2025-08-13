import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional, List
import xml.etree.ElementTree as ET
import tempfile
import os
from pathlib import Path

from .config import paper_scraper_settings

class GrobidClient:
    """
    Client for interacting with Grobid service for PDF processing
    """

    def __init__(self, grobid_url: str = None):
        self.logger = logging.getLogger(__name__)
        self.grobid_url = grobid_url or paper_scraper_settings.grobid_url
        self.timeout = aiohttp.ClientTimeout(total=paper_scraper_settings.grobid_timeout)
        self.max_retries = paper_scraper_settings.grobid_max_retries

    async def extract_pdf_content(
        self,
        pdf_file_path: str,
        filename: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extract full text and metadata from PDF using Grobid

        Args:
            pdf_file_path: Path to the PDF file
            filename: Optional filename for the PDF

        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            if not os.path.exists(pdf_file_path):
                self.logger.error(f"PDF file not found: {pdf_file_path}")
                return None

            filename = filename or os.path.basename(pdf_file_path)

            # Prepare form data
            data = aiohttp.FormData()
            with open(pdf_file_path, 'rb') as f:
                data.add_field('input', f, filename=filename)

            # Make request to Grobid
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                for attempt in range(self.max_retries):
                    try:
                        async with session.post(
                            f"{self.grobid_url}/api/processFulltextDocument",
                            data=data
                        ) as response:
                            if response.status == 200:
                                xml_content = await response.text()
                                return await self._parse_grobid_xml(xml_content)
                            else:
                                self.logger.error(f"Grobid request failed with status {response.status}")

                    except asyncio.TimeoutError:
                        self.logger.warning(f"Grobid request timed out (attempt {attempt + 1})")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    except Exception as e:
                        self.logger.error(f"Error in Grobid request (attempt {attempt + 1}): {e}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                        continue

            return None

        except Exception as e:
            self.logger.error(f"Error extracting PDF content: {e}")
            return None

    async def extract_header_only(
        self,
        pdf_file_path: str,
        filename: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extract only header metadata from PDF using Grobid

        Args:
            pdf_file_path: Path to the PDF file
            filename: Optional filename for the PDF

        Returns:
            Dictionary containing extracted header metadata
        """
        try:
            if not os.path.exists(pdf_file_path):
                self.logger.error(f"PDF file not found: {pdf_file_path}")
                return None

            filename = filename or os.path.basename(pdf_file_path)

            # Prepare form data
            data = aiohttp.FormData()
            with open(pdf_file_path, 'rb') as f:
                data.add_field('input', f, filename=filename)

            # Make request to Grobid
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                for attempt in range(self.max_retries):
                    try:
                        async with session.post(
                            f"{self.grobid_url}/api/processHeaderDocument",
                            data=data
                        ) as response:
                            if response.status == 200:
                                xml_content = await response.text()
                                return await self._parse_grobid_xml(xml_content)
                            else:
                                self.logger.error(f"Grobid header request failed with status {response.status}")

                    except asyncio.TimeoutError:
                        self.logger.warning(f"Grobid header request timed out (attempt {attempt + 1})")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                        continue
                    except Exception as e:
                        self.logger.error(f"Error in Grobid header request (attempt {attempt + 1}): {e}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                        continue

            return None

        except Exception as e:
            self.logger.error(f"Error extracting PDF header: {e}")
            return None

    async def _parse_grobid_xml(self, xml_content: str) -> Dict[str, Any]:
        """
        Parse Grobid XML response into structured data

        Args:
            xml_content: XML content from Grobid

        Returns:
            Dictionary containing parsed data
        """
        try:
            root = ET.fromstring(xml_content)

            # Extract header information
            header = root.find('.//{http://www.tei-c.org/ns/1.0}teiHeader')
            header_data = {}

            if header is not None:
                # Title
                title_elem = header.find('.//{http://www.tei-c.org/ns/1.0}title')
                if title_elem is not None:
                    header_data['title'] = title_elem.text.strip()

                # Authors
                authors = []
                for author_elem in header.findall('.//{http://www.tei-c.org/ns/1.0}author'):
                    author = {}
                    forename = author_elem.find('.//{http://www.tei-c.org/ns/1.0}forename')
                    surname = author_elem.find('.//{http://www.tei-c.org/ns/1.0}surname')
                    if forename is not None and surname is not None:
                        author['name'] = f"{forename.text} {surname.text}".strip()
                    elif forename is not None:
                        author['name'] = forename.text.strip()
                    elif surname is not None:
                        author['name'] = surname.text.strip()

                    if author:
                        authors.append(author)

                header_data['authors'] = authors

                # Abstract
                abstract_elem = header.find('.//{http://www.tei-c.org/ns/1.0}abstract')
                if abstract_elem is not None:
                    header_data['abstract'] = abstract_elem.text.strip()

                # Keywords
                keywords = []
                for kw_elem in header.findall('.//{http://www.tei-c.org/ns/1.0}keywords//{http://www.tei-c.org/ns/1.0}term'):
                    if kw_elem.text:
                        keywords.append(kw_elem.text.strip())
                header_data['keywords'] = keywords

                # Publication date
                date_elem = header.find('.//{http://www.tei-c.org/ns/1.0}date')
                if date_elem is not None:
                    header_data['publication_date'] = date_elem.text.strip()

            # Extract body text
            body = root.find('.//{http://www.tei-c.org/ns/1.0}body')
            body_text = ""

            if body is not None:
                # Extract text from all paragraphs
                paragraphs = []
                for p_elem in body.findall('.//{http://www.tei-c.org/ns/1.0}p'):
                    if p_elem.text:
                        paragraphs.append(p_elem.text.strip())

                body_text = "\n\n".join(paragraphs)

            # Extract citations
            citations = []
            for bibl_elem in root.findall('.//{http://www.tei-c.org/ns/1.0}biblStruct'):
                citation = {}

                # Title
                title_elem = bibl_elem.find('.//{http://www.tei-c.org/ns/1.0}title')
                if title_elem is not None:
                    citation['title'] = title_elem.text.strip()

                # Authors
                cit_authors = []
                for author_elem in bibl_elem.findall('.//{http://www.tei-c.org/ns/1.0}author'):
                    author = {}
                    forename = author_elem.find('.//{http://www.tei-c.org/ns/1.0}forename')
                    surname = author_elem.find('.//{http://www.tei-c.org/ns/1.0}surname')
                    if forename is not None and surname is not None:
                        author['name'] = f"{forename.text} {surname.text}".strip()
                    elif forename is not None:
                        author['name'] = forename.text.strip()
                    elif surname is not None:
                        author['name'] = surname.text.strip()

                    if author:
                        cit_authors.append(author)

                citation['authors'] = cit_authors

                # Date
                date_elem = bibl_elem.find('.//{http://www.tei-c.org/ns/1.0}date')
                if date_elem is not None:
                    citation['date'] = date_elem.text.strip()

                if citation:
                    citations.append(citation)

            return {
                'header': header_data,
                'body_text': body_text,
                'citations': citations,
                'raw_xml': xml_content
            }

        except Exception as e:
            self.logger.error(f"Error parsing Grobid XML: {e}")
            return {
                'header': {},
                'body_text': "",
                'citations': [],
                'raw_xml': xml_content,
                'parse_error': str(e)
            }

    async def check_service_health(self) -> bool:
        """
        Check if Grobid service is available

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.grobid_url}/api/isalive") as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"Grobid health check failed: {e}")
            return False

    async def extract_figures_and_tables(
        self,
        pdf_file_path: str
    ) -> Dict[str, Any]:
        """
        Extract figures and tables from PDF (placeholder for future implementation)

        Args:
            pdf_file_path: Path to the PDF file

        Returns:
            Dictionary containing extracted figures and tables
        """
        # This is a placeholder for future implementation
        # Grobid can extract figures and tables, but requires additional setup
        return {
            'figures': [],
            'tables': [],
            'message': 'Figure and table extraction not yet implemented'
        }
