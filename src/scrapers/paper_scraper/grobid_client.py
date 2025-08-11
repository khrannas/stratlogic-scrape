"""
Grobid client for PDF text extraction and metadata extraction.
"""

import aiohttp
import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List, Tuple
import tempfile
import os
from datetime import datetime
import hashlib


class GrobidClient:
    """Client for interacting with Grobid service for PDF processing."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.base_url = config.grobid_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=config.grobid_timeout)
    
    async def extract_pdf_content(
        self,
        pdf_file_path: str,
        filename: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extract full text and metadata from PDF using Grobid.
        
        Args:
            pdf_file_path: Path to the PDF file
            filename: Optional filename for the PDF
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        try:
            if not os.path.exists(pdf_file_path):
                self.logger.error(f"PDF file not found: {pdf_file_path}")
                return None
            
            if filename is None:
                filename = os.path.basename(pdf_file_path)
            
            self.logger.info(f"Processing PDF with Grobid: {filename}")
            
            # Prepare form data
            data = aiohttp.FormData()
            with open(pdf_file_path, 'rb') as f:
                data.add_field('input', f, filename=filename)
            
            # Make request to Grobid
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/processFulltextDocument",
                    data=data
                ) as response:
                    if response.status == 200:
                        xml_content = await response.text()
                        return self._parse_grobid_xml(xml_content, filename)
                    else:
                        self.logger.error(f"Grobid request failed: {response.status}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Failed to extract PDF content: {e}")
            return None
    
    async def extract_header_only(
        self,
        pdf_file_path: str,
        filename: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extract only header information from PDF (faster than full extraction).
        
        Args:
            pdf_file_path: Path to the PDF file
            filename: Optional filename for the PDF
            
        Returns:
            Dictionary containing header metadata
        """
        try:
            if not os.path.exists(pdf_file_path):
                self.logger.error(f"PDF file not found: {pdf_file_path}")
                return None
            
            if filename is None:
                filename = os.path.basename(pdf_file_path)
            
            self.logger.info(f"Extracting header from PDF: {filename}")
            
            # Prepare form data
            data = aiohttp.FormData()
            with open(pdf_file_path, 'rb') as f:
                data.add_field('input', f, filename=filename)
            
            # Make request to Grobid
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/processHeaderDocument",
                    data=data
                ) as response:
                    if response.status == 200:
                        xml_content = await response.text()
                        return self._parse_grobid_header_xml(xml_content, filename)
                    else:
                        self.logger.error(f"Grobid header extraction failed: {response.status}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"Failed to extract PDF header: {e}")
            return None
    
    async def extract_citations(
        self,
        pdf_file_path: str,
        filename: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract citations from PDF.
        
        Args:
            pdf_file_path: Path to the PDF file
            filename: Optional filename for the PDF
            
        Returns:
            List of citation dictionaries
        """
        try:
            if not os.path.exists(pdf_file_path):
                self.logger.error(f"PDF file not found: {pdf_file_path}")
                return []
            
            if filename is None:
                filename = os.path.basename(pdf_file_path)
            
            self.logger.info(f"Extracting citations from PDF: {filename}")
            
            # Prepare form data
            data = aiohttp.FormData()
            with open(pdf_file_path, 'rb') as f:
                data.add_field('input', f, filename=filename)
            
            # Make request to Grobid
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/processReferences",
                    data=data
                ) as response:
                    if response.status == 200:
                        xml_content = await response.text()
                        return self._parse_grobid_citations_xml(xml_content)
                    else:
                        self.logger.error(f"Grobid citation extraction failed: {response.status}")
                        return []
                        
        except Exception as e:
            self.logger.error(f"Failed to extract citations: {e}")
            return []
    
    def _parse_grobid_xml(self, xml_content: str, filename: str) -> Dict[str, Any]:
        """
        Parse Grobid XML response for full text extraction.
        
        Args:
            xml_content: XML content from Grobid
            filename: Original filename
            
        Returns:
            Dictionary containing parsed content
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Extract header information
            header = root.find('.//{http://www.tei-c.org/ns/1.0}teiHeader')
            header_data = self._extract_header_data(header) if header is not None else {}
            
            # Extract body text
            body = root.find('.//{http://www.tei-c.org/ns/1.0}body')
            body_data = self._extract_body_data(body) if body is not None else {}
            
            # Calculate content hash
            content_for_hash = f"{header_data.get('title', '')}{body_data.get('text', '')}"
            content_hash = hashlib.sha256(content_for_hash.encode()).hexdigest()
            
            return {
                'filename': filename,
                'header': header_data,
                'body': body_data,
                'content_hash': content_hash,
                'extraction_timestamp': datetime.utcnow().isoformat(),
                'word_count': len(body_data.get('text', '').split()),
                'section_count': len(body_data.get('sections', [])),
                'figure_count': len(body_data.get('figures', [])),
                'table_count': len(body_data.get('tables', []))
            }
            
        except Exception as e:
            self.logger.error(f"Failed to parse Grobid XML: {e}")
            return {}
    
    def _parse_grobid_header_xml(self, xml_content: str, filename: str) -> Dict[str, Any]:
        """
        Parse Grobid XML response for header extraction.
        
        Args:
            xml_content: XML content from Grobid
            filename: Original filename
            
        Returns:
            Dictionary containing parsed header data
        """
        try:
            root = ET.fromstring(xml_content)
            header = root.find('.//{http://www.tei-c.org/ns/1.0}teiHeader')
            
            if header is not None:
                header_data = self._extract_header_data(header)
                header_data['filename'] = filename
                header_data['extraction_timestamp'] = datetime.utcnow().isoformat()
                return header_data
            else:
                return {'filename': filename, 'extraction_timestamp': datetime.utcnow().isoformat()}
                
        except Exception as e:
            self.logger.error(f"Failed to parse Grobid header XML: {e}")
            return {'filename': filename, 'extraction_timestamp': datetime.utcnow().isoformat()}
    
    def _parse_grobid_citations_xml(self, xml_content: str) -> List[Dict[str, Any]]:
        """
        Parse Grobid XML response for citation extraction.
        
        Args:
            xml_content: XML content from Grobid
            
        Returns:
            List of citation dictionaries
        """
        try:
            root = ET.fromstring(xml_content)
            citations = []
            
            # Find all reference elements
            ref_elements = root.findall('.//{http://www.tei-c.org/ns/1.0}listBibl//{http://www.tei-c.org/ns/1.0}biblStruct')
            
            for i, ref in enumerate(ref_elements):
                citation = self._extract_citation_data(ref, i + 1)
                if citation:
                    citations.append(citation)
            
            return citations
            
        except Exception as e:
            self.logger.error(f"Failed to parse Grobid citations XML: {e}")
            return []
    
    def _extract_header_data(self, header_element) -> Dict[str, Any]:
        """
        Extract header data from TEI header element.
        
        Args:
            header_element: TEI header element
            
        Returns:
            Dictionary containing header data
        """
        try:
            header_data = {}
            
            # Extract title
            title_elem = header_element.find('.//{http://www.tei-c.org/ns/1.0}title')
            if title_elem is not None:
                header_data['title'] = title_elem.text.strip() if title_elem.text else ""
            
            # Extract authors
            authors = []
            author_elements = header_element.findall('.//{http://www.tei-c.org/ns/1.0}author')
            for author_elem in author_elements:
                author = {}
                
                # Extract author name
                pers_name = author_elem.find('.//{http://www.tei-c.org/ns/1.0}persName')
                if pers_name is not None:
                    forename = pers_name.find('.//{http://www.tei-c.org/ns/1.0}forename')
                    surname = pers_name.find('.//{http://www.tei-c.org/ns/1.0}surname')
                    
                    if forename is not None and surname is not None:
                        author['name'] = f"{forename.text} {surname.text}".strip()
                    elif forename is not None:
                        author['name'] = forename.text.strip()
                    elif surname is not None:
                        author['name'] = surname.text.strip()
                
                # Extract author email
                email = author_elem.find('.//{http://www.tei-c.org/ns/1.0}email')
                if email is not None:
                    author['email'] = email.text.strip()
                
                # Extract author affiliation
                affiliation = author_elem.find('.//{http://www.tei-c.org/ns/1.0}affiliation')
                if affiliation is not None:
                    org_name = affiliation.find('.//{http://www.tei-c.org/ns/1.0}orgName')
                    if org_name is not None:
                        author['affiliation'] = org_name.text.strip()
                
                if author:
                    authors.append(author)
            
            header_data['authors'] = authors
            
            # Extract abstract
            abstract_elem = header_element.find('.//{http://www.tei-c.org/ns/1.0}abstract')
            if abstract_elem is not None:
                header_data['abstract'] = abstract_elem.text.strip() if abstract_elem.text else ""
            
            # Extract keywords
            keywords = []
            keyword_elements = header_element.findall('.//{http://www.tei-c.org/ns/1.0}keywords//{http://www.tei-c.org/ns/1.0}term')
            for keyword_elem in keyword_elements:
                if keyword_elem.text:
                    keywords.append(keyword_elem.text.strip())
            header_data['keywords'] = keywords
            
            # Extract publication date
            date_elem = header_element.find('.//{http://www.tei-c.org/ns/1.0}date')
            if date_elem is not None:
                header_data['publication_date'] = date_elem.text.strip() if date_elem.text else ""
            
            return header_data
            
        except Exception as e:
            self.logger.error(f"Failed to extract header data: {e}")
            return {}
    
    def _extract_body_data(self, body_element) -> Dict[str, Any]:
        """
        Extract body data from TEI body element.
        
        Args:
            body_element: TEI body element
            
        Returns:
            Dictionary containing body data
        """
        try:
            body_data = {}
            
            # Extract full text
            text_elements = body_element.findall('.//{http://www.tei-c.org/ns/1.0}p')
            text_parts = []
            for text_elem in text_elements:
                if text_elem.text:
                    text_parts.append(text_elem.text.strip())
            
            body_data['text'] = ' '.join(text_parts)
            
            # Extract sections
            sections = []
            section_elements = body_element.findall('.//{http://www.tei-c.org/ns/1.0}div')
            for section_elem in section_elements:
                section = {}
                
                # Extract section title
                head = section_elem.find('.//{http://www.tei-c.org/ns/1.0}head')
                if head is not None:
                    section['title'] = head.text.strip() if head.text else ""
                
                # Extract section text
                section_text_elements = section_elem.findall('.//{http://www.tei-c.org/ns/1.0}p')
                section_text_parts = []
                for text_elem in section_text_elements:
                    if text_elem.text:
                        section_text_parts.append(text_elem.text.strip())
                
                section['text'] = ' '.join(section_text_parts)
                
                if section:
                    sections.append(section)
            
            body_data['sections'] = sections
            
            # Extract figures
            figures = []
            figure_elements = body_element.findall('.//{http://www.tei-c.org/ns/1.0}figure')
            for figure_elem in figure_elements:
                figure = {}
                
                # Extract figure caption
                fig_desc = figure_elem.find('.//{http://www.tei-c.org/ns/1.0}figDesc')
                if fig_desc is not None:
                    figure['caption'] = fig_desc.text.strip() if fig_desc.text else ""
                
                # Extract figure label
                label = figure_elem.find('.//{http://www.tei-c.org/ns/1.0}label')
                if label is not None:
                    figure['label'] = label.text.strip() if label.text else ""
                
                if figure:
                    figures.append(figure)
            
            body_data['figures'] = figures
            
            # Extract tables
            tables = []
            table_elements = body_element.findall('.//{http://www.tei-c.org/ns/1.0}table')
            for table_elem in table_elements:
                table = {}
                
                # Extract table caption
                head = table_elem.find('.//{http://www.tei-c.org/ns/1.0}head')
                if head is not None:
                    table['caption'] = head.text.strip() if head.text else ""
                
                # Extract table label
                label = table_elem.find('.//{http://www.tei-c.org/ns/1.0}label')
                if label is not None:
                    table['label'] = label.text.strip() if label.text else ""
                
                if table:
                    tables.append(table)
            
            body_data['tables'] = tables
            
            return body_data
            
        except Exception as e:
            self.logger.error(f"Failed to extract body data: {e}")
            return {}
    
    def _extract_citation_data(self, citation_element, index: int) -> Optional[Dict[str, Any]]:
        """
        Extract citation data from TEI biblStruct element.
        
        Args:
            citation_element: TEI biblStruct element
            index: Citation index
            
        Returns:
            Dictionary containing citation data
        """
        try:
            citation = {'index': index}
            
            # Extract title
            title_elem = citation_element.find('.//{http://www.tei-c.org/ns/1.0}title')
            if title_elem is not None:
                citation['title'] = title_elem.text.strip() if title_elem.text else ""
            
            # Extract authors
            authors = []
            author_elements = citation_element.findall('.//{http://www.tei-c.org/ns/1.0}author')
            for author_elem in author_elements:
                pers_name = author_elem.find('.//{http://www.tei-c.org/ns/1.0}persName')
                if pers_name is not None:
                    forename = pers_name.find('.//{http://www.tei-c.org/ns/1.0}forename')
                    surname = pers_name.find('.//{http://www.tei-c.org/ns/1.0}surname')
                    
                    if forename is not None and surname is not None:
                        authors.append(f"{forename.text} {surname.text}".strip())
                    elif forename is not None:
                        authors.append(forename.text.strip())
                    elif surname is not None:
                        authors.append(surname.text.strip())
            
            citation['authors'] = authors
            
            # Extract journal/book title
            monogr = citation_element.find('.//{http://www.tei-c.org/ns/1.0}monogr')
            if monogr is not None:
                title_elem = monogr.find('.//{http://www.tei-c.org/ns/1.0}title')
                if title_elem is not None:
                    citation['journal'] = title_elem.text.strip() if title_elem.text else ""
            
            # Extract publication date
            date_elem = citation_element.find('.//{http://www.tei-c.org/ns/1.0}date')
            if date_elem is not None:
                citation['date'] = date_elem.text.strip() if date_elem.text else ""
            
            # Extract DOI
            idno_elements = citation_element.findall('.//{http://www.tei-c.org/ns/1.0}idno')
            for idno_elem in idno_elements:
                if idno_elem.get('type') == 'DOI':
                    citation['doi'] = idno_elem.text.strip() if idno_elem.text else ""
                    break
            
            return citation
            
        except Exception as e:
            self.logger.error(f"Failed to extract citation data: {e}")
            return None
    
    async def check_service_health(self) -> bool:
        """
        Check if Grobid service is healthy and responding.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{self.base_url}/api/isalive") as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"Grobid health check failed: {e}")
            return False
