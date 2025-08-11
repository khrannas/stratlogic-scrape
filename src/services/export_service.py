"""
Export service for the StratLogic Scraping System.

This module provides data export functionality and report generation.
"""

import io
import json
import csv
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from ..core.models.content_processing import (
    ExportJob, Report, ExportFormat, ReportType, ProcessingStatus
)
from ..core.models import User
from ..core.exceptions import ContentProcessingError
from ..services.logging_service import get_logger
from ..storage.minio_client import MinIOClient


logger = get_logger(__name__)


class ExportService:
    """Service for data export and report generation operations."""
    
    def __init__(self, db: AsyncSession, minio_client: MinIOClient):
        self.db = db
        self.minio_client = minio_client
    
    async def create_export_job(
        self,
        user_id: UUID,
        export_format: ExportFormat,
        export_query: Dict[str, Any] = None
    ) -> ExportJob:
        """Create a new export job."""
        try:
            export_job = ExportJob(
                user_id=user_id,
                export_format=export_format,
                export_query=export_query or {},
                status=ProcessingStatus.PENDING
            )
            
            self.db.add(export_job)
            await self.db.flush()
            
            # Process export job
            await self._process_export_job(export_job)
            
            await self.db.commit()
            
            logger.info(f"Export job created: {export_job.id}")
            return export_job
            
        except Exception as e:
            logger.error(f"Export job creation failed", extra={"error": str(e)})
            raise ContentProcessingError(f"Export job creation failed: {str(e)}")
    
    async def _process_export_job(self, export_job: ExportJob):
        """Process an export job and generate the export file."""
        try:
            export_job.status = ProcessingStatus.PROCESSING
            export_job.progress = 0.0
            await self.db.flush()
            
            # Get sample data for export
            data = await self._get_sample_export_data()
            export_job.progress = 50.0
            await self.db.flush()
            
            # Generate export file
            file_data, file_name = await self._generate_export_file(data, export_job.export_format)
            export_job.progress = 75.0
            await self.db.flush()
            
            # Upload to MinIO
            file_path = f"exports/{export_job.id}/{file_name}"
            await self.minio_client.upload_file(
                bucket_name="artifacts",
                object_name=file_path,
                file_data=file_data,
                content_type=self._get_content_type(export_job.export_format)
            )
            
            # Update job status
            export_job.file_path = file_path
            export_job.file_size = len(file_data)
            export_job.status = ProcessingStatus.COMPLETED
            export_job.progress = 100.0
            export_job.export_metadata = {
                "record_count": len(data),
                "generated_at": datetime.utcnow().isoformat(),
                "file_name": file_name
            }
            
            await self.db.flush()
            
            logger.info(f"Export job completed: {export_job.id}")
            
        except Exception as e:
            export_job.status = ProcessingStatus.FAILED
            export_job.error_message = str(e)
            await self.db.flush()
            logger.error(f"Export job processing failed: {export_job.id}", extra={"error": str(e)})
            raise
    
    async def _get_sample_export_data(self) -> List[Dict[str, Any]]:
        """Get sample data for export."""
        # Return sample data for demonstration
        return [
            {
                "id": "sample-1",
                "title": "Sample Document 1",
                "content_type": "document",
                "quality_score": 0.85,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": "sample-2",
                "title": "Sample Document 2",
                "content_type": "pdf",
                "quality_score": 0.72,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
    
    async def _generate_export_file(self, data: List[Dict[str, Any]], export_format: ExportFormat) -> Tuple[bytes, str]:
        """Generate export file in the specified format."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        if export_format == ExportFormat.CSV:
            return await self._generate_csv_file(data, timestamp)
        elif export_format == ExportFormat.JSON:
            return await self._generate_json_file(data, timestamp)
        else:
            raise ContentProcessingError(f"Unsupported export format: {export_format}")
    
    async def _generate_csv_file(self, data: List[Dict[str, Any]], timestamp: str) -> Tuple[bytes, str]:
        """Generate CSV export file."""
        if not data:
            return b"", f"export_{timestamp}.csv"
        
        # Get all unique keys
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())
        
        # Sort keys for consistent output
        fieldnames = sorted(all_keys)
        
        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for item in data:
            # Convert complex values to strings
            row = {}
            for key in fieldnames:
                value = item.get(key)
                if isinstance(value, (list, dict)):
                    row[key] = json.dumps(value)
                else:
                    row[key] = str(value) if value is not None else ""
            writer.writerow(row)
        
        file_name = f"export_{timestamp}.csv"
        return output.getvalue().encode('utf-8'), file_name
    
    async def _generate_json_file(self, data: List[Dict[str, Any]], timestamp: str) -> Tuple[bytes, str]:
        """Generate JSON export file."""
        export_data = {
            "export_info": {
                "timestamp": datetime.utcnow().isoformat(),
                "record_count": len(data),
                "format": "json"
            },
            "data": data
        }
        
        file_name = f"export_{timestamp}.json"
        return json.dumps(export_data, indent=2, default=str).encode('utf-8'), file_name
    
    def _get_content_type(self, export_format: ExportFormat) -> str:
        """Get content type for export format."""
        content_types = {
            ExportFormat.CSV: "text/csv",
            ExportFormat.JSON: "application/json"
        }
        return content_types.get(export_format, "application/octet-stream")
    
    async def get_export_job(self, job_id: UUID) -> Optional[ExportJob]:
        """Get export job by ID."""
        result = await self.db.execute(
            select(ExportJob).where(ExportJob.id == job_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_export_jobs(self, user_id: UUID, limit: int = 50) -> List[ExportJob]:
        """Get export jobs for a user."""
        result = await self.db.execute(
            select(ExportJob)
            .where(ExportJob.user_id == user_id)
            .order_by(desc(ExportJob.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def create_report(
        self,
        user_id: UUID,
        report_type: ReportType,
        report_title: str,
        report_description: str = None
    ) -> Report:
        """Create a new report."""
        try:
            # Generate report data
            report_data = await self._generate_report_data(report_type)
            
            # Create report record
            report = Report(
                user_id=user_id,
                report_type=report_type,
                report_title=report_title,
                report_description=report_description,
                report_data=report_data
            )
            
            self.db.add(report)
            await self.db.commit()
            
            logger.info(f"Report created: {report.id}")
            return report
            
        except Exception as e:
            logger.error(f"Report creation failed", extra={"error": str(e)})
            raise ContentProcessingError(f"Report creation failed: {str(e)}")
    
    async def _generate_report_data(self, report_type: ReportType) -> Dict[str, Any]:
        """Generate data for report based on type."""
        if report_type == ReportType.CONTENT_ANALYSIS:
            return {
                "total_content": 100,
                "content_by_type": {"document": 50, "pdf": 30, "image": 20},
                "generated_at": datetime.utcnow().isoformat()
            }
        elif report_type == ReportType.USAGE_STATISTICS:
            return {
                "total_views": 1000,
                "total_downloads": 500,
                "generated_at": datetime.utcnow().isoformat()
            }
        else:
            return {"error": "Unsupported report type"}
    
    async def get_user_reports(self, user_id: UUID, limit: int = 50) -> List[Report]:
        """Get reports for a user."""
        result = await self.db.execute(
            select(Report)
            .where(Report.user_id == user_id)
            .order_by(desc(Report.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_report(self, report_id: UUID) -> Optional[Report]:
        """Get report by ID."""
        result = await self.db.execute(
            select(Report).where(Report.id == report_id)
        )
        return result.scalar_one_or_none()
