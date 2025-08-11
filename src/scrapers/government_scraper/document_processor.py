"""
Government document processor for extracting text and metadata from various document formats.
"""

import io
import logging
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
import aiohttp
import asyncio

# Document processing libraries
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("PyPDF2 not available. PDF processing will be disabled.")

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logging.warning("python-docx not available. DOCX processing will be disabled.")

try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    logging.warning("openpyxl not available. Excel processing will be disabled.")

from .config import GovernmentScraperSettings


@dataclass
class ProcessedDocument:
    """Processed government document information."""
    url: str
    text_content: str
    metadata: Dict[str, Any]
    analysis: Dict[str, Any]
    content_hash: str
    word_count: int
    processing_timestamp: str
    document_type: str
    language: Optional[str] = None
    quality_score: float = 0.0


class GovernmentDocumentProcessor:
    """Processor for government documents."""
    
    def __init__(self, settings: GovernmentScraperSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Check available libraries
        self.pdf_available = PDF_AVAILABLE
        self.docx_available = DOCX_AVAILABLE
        self.excel_available = EXCEL_AVAILABLE
        
        if not self.pdf_available:
            self.logger.warning("PDF processing is disabled due to missing PyPDF2")
        if not self.docx_available:
            self.logger.warning("DOCX processing is disabled due to missing python-docx")
        if not self.excel_available:
            self.logger.warning("Excel processing is disabled due to missing openpyxl")
    
    async def process_document(
        self,
        document_url: str,
        document_data: bytes,
        content_type: str
    ) -> Optional[ProcessedDocument]:
        """Process government document."""
        
        try:
            # Validate document size
            if len(document_data) > self.settings.max_document_size:
                self.logger.warning(f"Document too large: {len(document_data)} bytes")
                return None
            
            # Extract text content
            text_content = await self._extract_text(document_data, content_type)
            
            if not text_content:
                self.logger.warning(f"No text content extracted from {document_url}")
                return None
            
            # Extract metadata
            metadata = await self._extract_metadata(document_data, content_type)
            
            # Analyze content
            analysis = await self._analyze_content(text_content)
            
            # Calculate content hash
            content_hash = hashlib.sha256(text_content.encode('utf-8')).hexdigest()
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(text_content, metadata, analysis)
            
            # Detect language
            language = self._detect_language(text_content)
            
            return ProcessedDocument(
                url=document_url,
                text_content=text_content,
                metadata=metadata,
                analysis=analysis,
                content_hash=content_hash,
                word_count=len(text_content.split()),
                processing_timestamp=datetime.utcnow().isoformat(),
                document_type=metadata.get('document_type', 'unknown'),
                language=language,
                quality_score=quality_score
            )
            
        except Exception as e:
            self.logger.error(f"Document processing failed for {document_url}: {e}")
            return None
    
    async def _extract_text(
        self,
        document_data: bytes,
        content_type: str
    ) -> Optional[str]:
        """Extract text from document."""
        
        try:
            content_type_lower = content_type.lower()
            
            if 'pdf' in content_type_lower:
                if self.pdf_available:
                    return self._extract_pdf_text(document_data)
                else:
                    self.logger.error("PDF processing not available")
                    return None
            elif 'word' in content_type_lower or 'docx' in content_type_lower:
                if self.docx_available:
                    return self._extract_docx_text(document_data)
                else:
                    self.logger.error("DOCX processing not available")
                    return None
            elif 'excel' in content_type_lower or 'spreadsheet' in content_type_lower:
                if self.excel_available:
                    return self._extract_excel_text(document_data)
                else:
                    self.logger.error("Excel processing not available")
                    return None
            elif 'text' in content_type_lower or 'plain' in content_type_lower:
                return document_data.decode('utf-8', errors='ignore')
            else:
                self.logger.warning(f"Unsupported content type: {content_type}")
                return None
                
        except Exception as e:
            self.logger.error(f"Text extraction failed: {e}")
            return None
    
    def _extract_pdf_text(self, pdf_data: bytes) -> str:
        """Extract text from PDF."""
        
        text_content = []
        
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                except Exception as e:
                    self.logger.warning(f"Failed to extract text from PDF page {page_num}: {e}")
                    continue
            
            return '\n\n'.join(text_content)
            
        except Exception as e:
            self.logger.error(f"PDF text extraction failed: {e}")
            return ""
    
    def _extract_docx_text(self, docx_data: bytes) -> str:
        """Extract text from DOCX."""
        
        try:
            doc = docx.Document(io.BytesIO(docx_data))
            
            text_content = []
            
            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text_content.append(paragraph.text)
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text:
                            row_text.append(cell.text)
                    if row_text:
                        text_content.append(' | '.join(row_text))
            
            return '\n\n'.join(text_content)
            
        except Exception as e:
            self.logger.error(f"DOCX text extraction failed: {e}")
            return ""
    
    def _extract_excel_text(self, excel_data: bytes) -> str:
        """Extract text from Excel file."""
        
        try:
            workbook = openpyxl.load_workbook(io.BytesIO(excel_data), data_only=True)
            
            text_content = []
            
            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                sheet_text = [f"Sheet: {sheet_name}"]
                
                for row in sheet.iter_rows(values_only=True):
                    row_text = []
                    for cell_value in row:
                        if cell_value is not None:
                            row_text.append(str(cell_value))
                    if row_text:
                        sheet_text.append(' | '.join(row_text))
                
                if len(sheet_text) > 1:  # More than just sheet name
                    text_content.extend(sheet_text)
                    text_content.append('')  # Empty line between sheets
            
            return '\n'.join(text_content)
            
        except Exception as e:
            self.logger.error(f"Excel text extraction failed: {e}")
            return ""
    
    async def _extract_metadata(
        self,
        document_data: bytes,
        content_type: str
    ) -> Dict[str, Any]:
        """Extract document metadata."""
        
        metadata = {
            'content_type': content_type,
            'file_size': len(document_data),
            'extraction_timestamp': datetime.utcnow().isoformat(),
            'document_type': self._classify_document_type(content_type)
        }
        
        # Add content-type specific metadata
        content_type_lower = content_type.lower()
        
        if 'pdf' in content_type_lower and self.pdf_available:
            metadata.update(self._extract_pdf_metadata(document_data))
        elif ('word' in content_type_lower or 'docx' in content_type_lower) and self.docx_available:
            metadata.update(self._extract_docx_metadata(document_data))
        elif ('excel' in content_type_lower or 'spreadsheet' in content_type_lower) and self.excel_available:
            metadata.update(self._extract_excel_metadata(document_data))
        
        return metadata
    
    def _extract_pdf_metadata(self, pdf_data: bytes) -> Dict[str, Any]:
        """Extract metadata from PDF."""
        
        metadata = {}
        
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_data))
            
            if pdf_reader.metadata:
                info = pdf_reader.metadata
                metadata.update({
                    'pdf_pages': len(pdf_reader.pages),
                    'pdf_title': info.get('/Title'),
                    'pdf_author': info.get('/Author'),
                    'pdf_subject': info.get('/Subject'),
                    'pdf_creator': info.get('/Creator'),
                    'pdf_producer': info.get('/Producer'),
                    'pdf_creation_date': info.get('/CreationDate'),
                    'pdf_modification_date': info.get('/ModDate')
                })
            else:
                metadata['pdf_pages'] = len(pdf_reader.pages)
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"PDF metadata extraction failed: {e}")
            return metadata
    
    def _extract_docx_metadata(self, docx_data: bytes) -> Dict[str, Any]:
        """Extract metadata from DOCX."""
        
        metadata = {}
        
        try:
            doc = docx.Document(io.BytesIO(docx_data))
            
            # Extract core properties
            core_props = doc.core_properties
            if core_props:
                metadata.update({
                    'docx_title': core_props.title,
                    'docx_author': core_props.author,
                    'docx_subject': core_props.subject,
                    'docx_created': core_props.created.isoformat() if core_props.created else None,
                    'docx_modified': core_props.modified.isoformat() if core_props.modified else None,
                    'docx_revision': core_props.revision,
                    'docx_keywords': core_props.keywords
                })
            
            # Count paragraphs and tables
            metadata['docx_paragraphs'] = len(doc.paragraphs)
            metadata['docx_tables'] = len(doc.tables)
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"DOCX metadata extraction failed: {e}")
            return metadata
    
    def _extract_excel_metadata(self, excel_data: bytes) -> Dict[str, Any]:
        """Extract metadata from Excel file."""
        
        metadata = {}
        
        try:
            workbook = openpyxl.load_workbook(io.BytesIO(excel_data), data_only=True)
            
            metadata.update({
                'excel_sheets': workbook.sheetnames,
                'excel_sheet_count': len(workbook.sheetnames)
            })
            
            # Extract properties
            props = workbook.properties
            if props:
                metadata.update({
                    'excel_title': props.title,
                    'excel_author': props.creator,
                    'excel_subject': props.subject,
                    'excel_created': props.created.isoformat() if props.created else None,
                    'excel_modified': props.modified.isoformat() if props.modified else None,
                    'excel_keywords': props.keywords
                })
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Excel metadata extraction failed: {e}")
            return metadata
    
    async def _analyze_content(self, text_content: str) -> Dict[str, Any]:
        """Analyze document content."""
        
        # Basic content analysis
        analysis = {
            'language': self._detect_language(text_content),
            'document_type': self._classify_document_type_by_content(text_content),
            'key_topics': self._extract_key_topics(text_content),
            'entities': self._extract_entities(text_content),
            'summary': await self._generate_summary(text_content),
            'sentiment': self._analyze_sentiment(text_content),
            'complexity': self._assess_complexity(text_content),
            'government_terms': self._extract_government_terms(text_content)
        }
        
        return analysis
    
    def _detect_language(self, text: str) -> str:
        """Detect document language."""
        # Simple language detection (can be enhanced with proper library)
        indonesian_words = [
            'yang', 'dan', 'atau', 'dalam', 'untuk', 'dengan', 'oleh', 'dari', 'ke', 'di',
            'peraturan', 'pemerintah', 'negara', 'republik', 'indonesia', 'menteri',
            'kementerian', 'departemen', 'lembaga', 'badan', 'instansi'
        ]
        english_words = [
            'the', 'and', 'or', 'in', 'for', 'with', 'by', 'from', 'to', 'at',
            'regulation', 'government', 'state', 'republic', 'minister', 'ministry',
            'department', 'agency', 'institution', 'authority'
        ]
        
        text_lower = text.lower()
        indonesian_count = sum(1 for word in indonesian_words if word in text_lower)
        english_count = sum(1 for word in english_words if word in text_lower)
        
        return 'id' if indonesian_count > english_count else 'en'
    
    def _classify_document_type(self, content_type: str) -> str:
        """Classify document type based on content type."""
        content_type_lower = content_type.lower()
        
        if 'pdf' in content_type_lower:
            return 'pdf'
        elif 'word' in content_type_lower or 'docx' in content_type_lower:
            return 'word'
        elif 'excel' in content_type_lower or 'spreadsheet' in content_type_lower:
            return 'excel'
        elif 'powerpoint' in content_type_lower or 'presentation' in content_type_lower:
            return 'powerpoint'
        elif 'text' in content_type_lower or 'plain' in content_type_lower:
            return 'text'
        else:
            return 'unknown'
    
    def _classify_document_type_by_content(self, text: str) -> str:
        """Classify document type based on content."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['peraturan', 'regulation', 'law', 'undang-undang', 'uu']):
            return 'regulation'
        elif any(word in text_lower for word in ['laporan', 'report', 'annual', 'tahunan']):
            return 'report'
        elif any(word in text_lower for word in ['keputusan', 'decision', 'decree', 'sk']):
            return 'decision'
        elif any(word in text_lower for word in ['surat', 'letter', 'circular', 'edaran']):
            return 'letter'
        elif any(word in text_lower for word in ['anggaran', 'budget', 'keuangan', 'finance']):
            return 'budget'
        elif any(word in text_lower for word in ['proposal', 'usulan', 'proposal']):
            return 'proposal'
        else:
            return 'document'
    
    def _extract_key_topics(self, text: str) -> List[str]:
        """Extract key topics from text."""
        # Simple keyword extraction (can be enhanced with NLP)
        topics = []
        text_lower = text.lower()
        
        # Government-related keywords
        government_keywords = [
            'pemerintah', 'government', 'negara', 'state', 'republik', 'republic',
            'menteri', 'minister', 'kementerian', 'ministry', 'departemen', 'department',
            'lembaga', 'agency', 'badan', 'authority', 'instansi', 'institution',
            'peraturan', 'regulation', 'undang-undang', 'law', 'keputusan', 'decision',
            'laporan', 'report', 'anggaran', 'budget', 'keuangan', 'finance'
        ]
        
        for keyword in government_keywords:
            if keyword in text_lower:
                topics.append(keyword)
        
        return topics[:10]  # Limit to top 10 topics
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text."""
        # Simple entity extraction (can be enhanced with NLP)
        entities = []
        
        # Look for government agency names
        agency_patterns = [
            'Kementerian', 'Ministry', 'Badan', 'Agency', 'Lembaga', 'Institution',
            'Departemen', 'Department', 'Direktorat', 'Directorate'
        ]
        
        for pattern in agency_patterns:
            if pattern in text:
                entities.append(pattern)
        
        return entities[:5]  # Limit to top 5 entities
    
    async def _generate_summary(self, text: str) -> str:
        """Generate document summary."""
        # Simple summary generation (can be enhanced with LLM)
        sentences = text.split('.')
        if len(sentences) <= 3:
            return text
        
        # Take first few sentences as summary
        summary_sentences = sentences[:3]
        return '. '.join(summary_sentences) + '.'
    
    def _analyze_sentiment(self, text: str) -> str:
        """Analyze document sentiment."""
        # Simple sentiment analysis (can be enhanced with NLP)
        positive_words = ['baik', 'positif', 'berhasil', 'sukses', 'meningkat', 'good', 'positive', 'success']
        negative_words = ['buruk', 'negatif', 'gagal', 'menurun', 'masalah', 'bad', 'negative', 'fail', 'problem']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _assess_complexity(self, text: str) -> str:
        """Assess document complexity."""
        words = text.split()
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        if avg_word_length > 8:
            return 'high'
        elif avg_word_length > 6:
            return 'medium'
        else:
            return 'low'
    
    def _extract_government_terms(self, text: str) -> List[str]:
        """Extract government-specific terms."""
        government_terms = [
            'peraturan pemerintah', 'government regulation',
            'undang-undang', 'law',
            'keputusan presiden', 'presidential decree',
            'keputusan menteri', 'ministerial decision',
            'surat edaran', 'circular letter',
            'laporan tahunan', 'annual report',
            'anggaran belanja', 'budget allocation'
        ]
        
        found_terms = []
        text_lower = text.lower()
        
        for term in government_terms:
            if term in text_lower:
                found_terms.append(term)
        
        return found_terms
    
    def _calculate_quality_score(self, text: str, metadata: Dict[str, Any], analysis: Dict[str, Any]) -> float:
        """Calculate document quality score."""
        score = 0.0
        
        # Text length score
        word_count = len(text.split())
        if word_count > 1000:
            score += 0.3
        elif word_count > 500:
            score += 0.2
        elif word_count > 100:
            score += 0.1
        
        # Metadata completeness score
        metadata_fields = ['title', 'author', 'subject', 'created', 'modified']
        metadata_score = sum(1 for field in metadata_fields if metadata.get(field)) / len(metadata_fields)
        score += metadata_score * 0.2
        
        # Language detection score
        if analysis.get('language'):
            score += 0.1
        
        # Document type classification score
        if analysis.get('document_type') != 'unknown':
            score += 0.1
        
        # Government terms score
        gov_terms = analysis.get('government_terms', [])
        if len(gov_terms) > 0:
            score += min(len(gov_terms) * 0.05, 0.2)
        
        # Sentiment analysis score
        if analysis.get('sentiment'):
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get document processing statistics."""
        return {
            'pdf_available': self.pdf_available,
            'docx_available': self.docx_available,
            'excel_available': self.excel_available,
            'max_document_size': self.settings.max_document_size,
            'supported_formats': self.settings.supported_formats
        }
