"""
Document processing service for the StratLogic Scraping System.

This module provides advanced document processing functionality including
OCR, document structure analysis, table extraction, and document comparison.
"""

import io
import time
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..core.models.content_processing import (
    DocumentStructure, DocumentTable, DocumentAnnotation, OCRResult,
    ContentEnrichment, ProcessingStatus
)
from ..core.models import Artifact
from ..core.exceptions import ContentProcessingError
from ..services.logging_service import get_logger
from ..storage.minio_client import MinIOClient


logger = get_logger(__name__)


class DocumentProcessingService:
    """Service for advanced document processing operations."""
    
    def __init__(self, db: AsyncSession, minio_client: MinIOClient):
        self.db = db
        self.minio_client = minio_client
    
    async def process_document(self, content_enrichment_id: UUID) -> DocumentStructure:
        """Process document and extract structure, tables, and perform OCR if needed."""
        try:
            # Get content enrichment
            enrichment = await self._get_content_enrichment(content_enrichment_id)
            if not enrichment:
                raise ContentProcessingError(f"Content enrichment {content_enrichment_id} not found")
            
            # Check if document structure already exists
            existing_structure = await self._get_existing_structure(content_enrichment_id)
            if existing_structure:
                logger.info(f"Document structure already exists for content {content_enrichment_id}")
                return existing_structure
            
            # Get artifact
            artifact = await self._get_artifact(enrichment.artifact_id)
            if not artifact:
                raise ContentProcessingError(f"Artifact {enrichment.artifact_id} not found")
            
            # Create document structure
            document_structure = await self._create_document_structure(enrichment)
            
            # Perform document analysis based on content type
            if enrichment.content_type.value in ['pdf', 'image']:
                await self._perform_ocr_processing(enrichment, artifact)
            
            await self._analyze_document_structure(document_structure, artifact)
            await self._extract_tables_from_document(document_structure, artifact)
            
            logger.info(f"Document processing completed for content {content_enrichment_id}")
            return document_structure
            
        except Exception as e:
            logger.error(f"Document processing failed for content {content_enrichment_id}", extra={"error": str(e)})
            raise ContentProcessingError(f"Document processing failed: {str(e)}")
    
    async def _get_content_enrichment(self, enrichment_id: UUID) -> Optional[ContentEnrichment]:
        """Get content enrichment by ID."""
        result = await self.db.execute(
            select(ContentEnrichment).where(ContentEnrichment.id == enrichment_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_existing_structure(self, content_id: UUID) -> Optional[DocumentStructure]:
        """Get existing document structure for content."""
        result = await self.db.execute(
            select(DocumentStructure)
            .options(
                selectinload(DocumentStructure.tables),
                selectinload(DocumentStructure.annotations)
            )
            .where(DocumentStructure.content_id == content_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_artifact(self, artifact_id: UUID) -> Optional[Artifact]:
        """Get artifact by ID."""
        result = await self.db.execute(
            select(Artifact).where(Artifact.id == artifact_id)
        )
        return result.scalar_one_or_none()
    
    async def _create_document_structure(self, enrichment: ContentEnrichment) -> DocumentStructure:
        """Create initial document structure record."""
        document_structure = DocumentStructure(
            content_id=enrichment.id
        )
        
        self.db.add(document_structure)
        await self.db.flush()
        return document_structure
    
    async def _perform_ocr_processing(self, enrichment: ContentEnrichment, artifact: Artifact):
        """Perform OCR processing on image or PDF content."""
        try:
            # Download file from MinIO
            file_data = await self.minio_client.download_file(
                bucket_name="artifacts",
                object_name=artifact.minio_path
            )
            
            if not file_data:
                logger.warning(f"No file data found for artifact {artifact.id}")
                return
            
            # Perform OCR
            start_time = time.time()
            ocr_text, confidence, language = await self._extract_text_with_ocr(file_data, artifact.mime_type)
            processing_time = time.time() - start_time
            
            # Create OCR result
            ocr_result = OCRResult(
                content_id=enrichment.id,
                extracted_text=ocr_text,
                confidence_score=confidence,
                language=language,
                ocr_engine="tesseract",  # Default engine
                processing_time=processing_time,
                ocr_metadata={
                    "file_size": len(file_data),
                    "mime_type": artifact.mime_type,
                    "processing_timestamp": time.time()
                }
            )
            
            self.db.add(ocr_result)
            await self.db.flush()
            
            # Update content enrichment with OCR text if no existing text
            if not enrichment.extracted_text and ocr_text:
                enrichment.extracted_text = ocr_text
                enrichment.word_count = len(ocr_text.split())
                enrichment.character_count = len(ocr_text)
            
            logger.info(f"OCR processing completed for artifact {artifact.id}")
            
        except Exception as e:
            logger.error(f"OCR processing failed for artifact {artifact.id}", extra={"error": str(e)})
            # Don't fail the entire process if OCR fails
    
    async def _extract_text_with_ocr(self, file_data: bytes, mime_type: str) -> Tuple[str, float, str]:
        """Extract text from file using OCR."""
        try:
            # Import OCR libraries
            import pytesseract
            from PIL import Image
            import fitz  # PyMuPDF for PDF processing
            
            if "pdf" in mime_type.lower():
                # Handle PDF
                doc = fitz.open(stream=file_data, filetype="pdf")
                text_parts = []
                total_confidence = 0.0
                page_count = 0
                
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    # Convert PDF page to image
                    pix = page.get_pixmap()
                    img_data = pix.tobytes("png")
                    
                    # Perform OCR on image
                    img = Image.open(io.BytesIO(img_data))
                    page_text = pytesseract.image_to_string(img)
                    text_parts.append(page_text)
                    
                    # Get confidence (simplified)
                    confidence = 0.8  # Default confidence for PDF
                    total_confidence += confidence
                    page_count += 1
                
                doc.close()
                extracted_text = "\n".join(text_parts)
                avg_confidence = total_confidence / page_count if page_count > 0 else 0.0
                
            else:
                # Handle image
                img = Image.open(io.BytesIO(file_data))
                extracted_text = pytesseract.image_to_string(img)
                avg_confidence = 0.8  # Default confidence for images
            
            # Detect language (simplified)
            language = "en"  # Default to English
            
            return extracted_text, avg_confidence, language
            
        except ImportError:
            logger.warning("OCR libraries not available, skipping OCR processing")
            return "", 0.0, "unknown"
        except Exception as e:
            logger.error(f"OCR extraction failed", extra={"error": str(e)})
            return "", 0.0, "unknown"
    
    async def _analyze_document_structure(self, document_structure: DocumentStructure, artifact: Artifact):
        """Analyze document structure and extract metadata."""
        text_content = artifact.content_text or ""
        
        if not text_content:
            return
        
        # Extract title (first line or first heading)
        lines = text_content.split('\n')
        title = lines[0].strip() if lines else ""
        if len(title) > 500:  # Truncate long titles
            title = title[:497] + "..."
        
        # Extract headings (lines that look like headings)
        headings = []
        for line in lines:
            line = line.strip()
            if line and (
                line.isupper() or  # ALL CAPS
                line.startswith('#') or  # Markdown headings
                len(line.split()) <= 10 and line.endswith(':') or  # Short lines ending with colon
                (len(line) < 100 and line[0].isupper() and not line.endswith('.'))  # Short capitalized lines
            ):
                headings.append(line)
        
        # Extract abstract (look for common patterns)
        abstract = ""
        abstract_keywords = ['abstract', 'summary', 'overview', 'introduction']
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in abstract_keywords):
                # Take next few lines as abstract
                abstract_lines = []
                for j in range(i + 1, min(i + 10, len(lines))):
                    if lines[j].strip() and not any(h in lines[j] for h in headings):
                        abstract_lines.append(lines[j].strip())
                    else:
                        break
                abstract = " ".join(abstract_lines)
                break
        
        # Extract authors (look for common patterns)
        authors = []
        author_keywords = ['author', 'by', 'written by', 'prepared by']
        for line in lines[:20]:  # Check first 20 lines
            line_lower = line.lower().strip()
            if any(keyword in line_lower for keyword in author_keywords):
                # Extract author names
                author_text = line.split(':', 1)[1] if ':' in line else line
                author_names = [name.strip() for name in author_text.split(',')]
                authors.extend(author_names)
        
        # Determine document type
        document_type = self._determine_document_type(text_content, artifact.mime_type)
        
        # Count pages (estimate based on content length)
        estimated_pages = max(1, len(text_content) // 2000)  # Rough estimate
        
        # Update document structure
        document_structure.title = title
        document_structure.authors = authors
        document_structure.abstract = abstract
        document_structure.headings = headings[:50]  # Limit to first 50 headings
        document_structure.page_count = estimated_pages
        document_structure.document_type = document_type
        document_structure.language = "en"  # Default to English
        document_structure.structure_metadata = {
            "analysis_timestamp": time.time(),
            "content_length": len(text_content),
            "line_count": len(lines),
            "heading_count": len(headings)
        }
        
        await self.db.flush()
    
    def _determine_document_type(self, text_content: str, mime_type: str) -> str:
        """Determine document type based on content and MIME type."""
        text_lower = text_content.lower()
        
        # Check for specific document patterns
        if any(word in text_lower for word in ['research', 'study', 'analysis', 'findings']):
            return "research_paper"
        elif any(word in text_lower for word in ['report', 'annual', 'quarterly']):
            return "report"
        elif any(word in text_lower for word in ['policy', 'regulation', 'guideline']):
            return "policy_document"
        elif any(word in text_lower for word in ['manual', 'guide', 'instruction']):
            return "manual"
        elif any(word in text_lower for word in ['proposal', 'proposition', 'suggestion']):
            return "proposal"
        elif "table" in text_lower or "chart" in text_lower:
            return "data_document"
        else:
            return "general_document"
    
    async def _extract_tables_from_document(self, document_structure: DocumentStructure, artifact: Artifact):
        """Extract tables from document content."""
        text_content = artifact.content_text or ""
        
        if not text_content:
            return
        
        # Simple table extraction based on patterns
        tables = self._find_table_patterns(text_content)
        
        for i, table_data in enumerate(tables):
            table = DocumentTable(
                document_structure_id=document_structure.id,
                table_title=f"Table {i + 1}",
                table_data=table_data,
                headers=table_data[0] if table_data else [],
                row_count=len(table_data),
                column_count=len(table_data[0]) if table_data else 0,
                page_number=1,  # Default page
                confidence_score=0.7,  # Default confidence
                extraction_metadata={
                    "extraction_method": "pattern_based",
                    "table_index": i
                }
            )
            
            self.db.add(table)
        
        await self.db.flush()
    
    def _find_table_patterns(self, text_content: str) -> List[List[List[str]]]:
        """Find table patterns in text content."""
        tables = []
        lines = text_content.split('\n')
        
        current_table = []
        in_table = False
        
        for line in lines:
            line = line.strip()
            
            # Check if line looks like table data (contains multiple separators)
            separators = ['|', '\t', '  ']  # Common table separators
            has_separators = any(sep in line for sep in separators)
            
            if has_separators and len(line.split()) > 2:
                # This looks like table data
                if not in_table:
                    in_table = True
                    current_table = []
                
                # Parse table row
                if '|' in line:
                    # Pipe-separated
                    row = [cell.strip() for cell in line.split('|')]
                elif '\t' in line:
                    # Tab-separated
                    row = [cell.strip() for cell in line.split('\t')]
                else:
                    # Space-separated (multiple spaces)
                    row = [cell.strip() for cell in line.split('  ') if cell.strip()]
                
                if row:
                    current_table.append(row)
            else:
                # End of table
                if in_table and current_table:
                    tables.append(current_table)
                    current_table = []
                    in_table = False
        
        # Add final table if exists
        if in_table and current_table:
            tables.append(current_table)
        
        return tables
    
    async def add_document_annotation(
        self,
        document_structure_id: UUID,
        user_id: UUID,
        annotation_type: str,
        annotation_text: str,
        page_number: int = None,
        start_position: int = None,
        end_position: int = None,
        annotation_data: Dict[str, Any] = None
    ) -> DocumentAnnotation:
        """Add annotation to document."""
        annotation = DocumentAnnotation(
            document_structure_id=document_structure_id,
            user_id=user_id,
            annotation_type=annotation_type,
            annotation_text=annotation_text,
            page_number=page_number,
            start_position=start_position,
            end_position=end_position,
            annotation_data=annotation_data or {}
        )
        
        self.db.add(annotation)
        await self.db.commit()
        return annotation
    
    async def get_document_structure(self, structure_id: UUID) -> Optional[DocumentStructure]:
        """Get document structure by ID with all relationships."""
        result = await self.db.execute(
            select(DocumentStructure)
            .options(
                selectinload(DocumentStructure.tables),
                selectinload(DocumentStructure.annotations)
            )
            .where(DocumentStructure.id == structure_id)
        )
        return result.scalar_one_or_none()
    
    async def get_document_tables(self, structure_id: UUID) -> List[DocumentTable]:
        """Get all tables for a document structure."""
        result = await self.db.execute(
            select(DocumentTable)
            .where(DocumentTable.document_structure_id == structure_id)
            .order_by(DocumentTable.page_number, DocumentTable.created_at)
        )
        return result.scalars().all()
    
    async def compare_documents(self, structure_id_1: UUID, structure_id_2: UUID) -> Dict[str, Any]:
        """Compare two documents and return similarity metrics."""
        structure_1 = await self.get_document_structure(structure_id_1)
        structure_2 = await self.get_document_structure(structure_id_2)
        
        if not structure_1 or not structure_2:
            raise ContentProcessingError("One or both document structures not found")
        
        # Get content for comparison
        content_1 = await self._get_content_enrichment(structure_1.content_id)
        content_2 = await self._get_content_enrichment(structure_2.content_id)
        
        if not content_1 or not content_2:
            raise ContentProcessingError("Content enrichment not found for comparison")
        
        # Calculate similarity metrics
        similarity_metrics = {
            "title_similarity": self._calculate_text_similarity(
                content_1.extracted_text or "", content_2.extracted_text or ""
            ),
            "structure_similarity": self._calculate_structure_similarity(structure_1, structure_2),
            "table_similarity": self._calculate_table_similarity(structure_1, structure_2),
            "overall_similarity": 0.0
        }
        
        # Calculate overall similarity
        similarities = [
            similarity_metrics["title_similarity"],
            similarity_metrics["structure_similarity"],
            similarity_metrics["table_similarity"]
        ]
        similarity_metrics["overall_similarity"] = sum(similarities) / len(similarities)
        
        return similarity_metrics
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using simple metrics."""
        if not text1 or not text2:
            return 0.0
        
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_structure_similarity(self, structure1: DocumentStructure, structure2: DocumentStructure) -> float:
        """Calculate document structure similarity."""
        # Compare headings
        headings1 = set(structure1.headings or [])
        headings2 = set(structure2.headings or [])
        
        if not headings1 or not headings2:
            return 0.0
        
        intersection = headings1.intersection(headings2)
        union = headings1.union(headings2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_table_similarity(self, structure1: DocumentStructure, structure2: DocumentStructure) -> float:
        """Calculate table similarity."""
        tables1 = structure1.tables
        tables2 = structure2.tables
        
        if not tables1 or not tables2:
            return 0.0
        
        # Compare table counts
        count_similarity = 1.0 - abs(len(tables1) - len(tables2)) / max(len(tables1), len(tables2))
        
        # Compare table structures
        structure_similarities = []
        for table1 in tables1:
            for table2 in tables2:
                similarity = self._compare_table_structure(table1, table2)
                structure_similarities.append(similarity)
        
        avg_structure_similarity = sum(structure_similarities) / len(structure_similarities) if structure_similarities else 0.0
        
        return (count_similarity + avg_structure_similarity) / 2
    
    def _compare_table_structure(self, table1: DocumentTable, table2: DocumentTable) -> float:
        """Compare structure of two tables."""
        # Compare column counts
        col_similarity = 1.0 - abs(table1.column_count - table2.column_count) / max(table1.column_count, table2.column_count)
        
        # Compare row counts
        row_similarity = 1.0 - abs(table1.row_count - table2.row_count) / max(table1.row_count, table2.row_count)
        
        return (col_similarity + row_similarity) / 2
