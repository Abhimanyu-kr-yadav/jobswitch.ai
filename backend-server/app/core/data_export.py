"""
Data Export Manager for JobSwitch.ai
Handles user data export for GDPR compliance and data portability
"""
import json
import csv
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import zipfile
import tempfile
from io import StringIO, BytesIO
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import db_manager
from app.core.config import settings

logger = logging.getLogger(__name__)


class DataExportManager:
    """
    Comprehensive data export manager for user data portability and GDPR compliance
    """
    
    def __init__(self):
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)
        
        # Define user data tables and their relationships
        self.user_data_tables = {
            "users": {
                "primary_key": "id",
                "user_field": "id",
                "export_name": "user_profile",
                "description": "Basic user account information"
            },
            "user_profiles": {
                "primary_key": "id",
                "user_field": "user_id",
                "export_name": "profile_details",
                "description": "Detailed user profile information"
            },
            "user_skills": {
                "primary_key": "id",
                "user_field": "user_id",
                "export_name": "skills",
                "description": "User skills and proficiency levels"
            },
            "resumes": {
                "primary_key": "id",
                "user_field": "user_id",
                "export_name": "resumes",
                "description": "Resume versions and optimizations"
            },
            "job_applications": {
                "primary_key": "id",
                "user_field": "user_id",
                "export_name": "job_applications",
                "description": "Job application history and status"
            },
            "interview_sessions": {
                "primary_key": "id",
                "user_field": "user_id",
                "export_name": "interview_sessions",
                "description": "Interview preparation sessions and feedback"
            },
            "networking_campaigns": {
                "primary_key": "id",
                "user_field": "user_id",
                "export_name": "networking_campaigns",
                "description": "Networking campaigns and outreach activities"
            },
            "career_roadmaps": {
                "primary_key": "id",
                "user_field": "user_id",
                "export_name": "career_roadmaps",
                "description": "Career planning and goal tracking"
            },
            "agent_tasks": {
                "primary_key": "id",
                "user_field": "user_id",
                "export_name": "ai_interactions",
                "description": "AI agent interactions and task history"
            }
        }
        
        # Supported export formats
        self.export_formats = ["json", "csv", "xml", "zip"]
    
    async def export_user_data(self, user_id: str, export_format: str = "json", include_tables: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Export all data for a specific user
        
        Args:
            user_id: User ID to export data for
            export_format: Export format (json, csv, xml, zip)
            include_tables: Optional list of specific tables to include
            
        Returns:
            Export operation results
        """
        try:
            if export_format not in self.export_formats:
                raise ValueError(f"Unsupported export format: {export_format}")
            
            logger.info(f"Starting data export for user {user_id} in format {export_format}")
            
            # Determine which tables to export
            tables_to_export = include_tables or list(self.user_data_tables.keys())
            
            # Collect user data
            user_data = {}
            total_records = 0
            
            with db_manager.get_session() as session:
                for table_name in tables_to_export:
                    if table_name not in self.user_data_tables:
                        logger.warning(f"Unknown table for export: {table_name}")
                        continue
                    
                    try:
                        table_config = self.user_data_tables[table_name]
                        table_data = await self._export_table_data(session, table_name, table_config, user_id)
                        
                        if table_data:
                            user_data[table_config["export_name"]] = {
                                "description": table_config["description"],
                                "records": table_data,
                                "count": len(table_data)
                            }
                            total_records += len(table_data)
                            logger.debug(f"Exported {len(table_data)} records from {table_name}")
                        
                    except Exception as e:
                        logger.error(f"Error exporting table {table_name}: {str(e)}")
                        user_data[table_name] = {
                            "error": str(e),
                            "records": [],
                            "count": 0
                        }
            
            # Add export metadata
            export_metadata = {
                "export_id": f"export_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "user_id": user_id,
                "export_date": datetime.now().isoformat(),
                "export_format": export_format,
                "total_records": total_records,
                "tables_exported": len([t for t in user_data.values() if t.get("count", 0) > 0]),
                "gdpr_compliant": True,
                "data_retention_notice": "This export contains all your personal data stored in JobSwitch.ai as of the export date."
            }
            
            # Generate export file
            export_result = await self._generate_export_file(user_data, export_metadata, export_format)
            
            logger.info(f"Data export completed for user {user_id}: {total_records} records exported")
            return export_result
            
        except Exception as e:
            logger.error(f"Data export failed for user {user_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _export_table_data(self, session: Session, table_name: str, table_config: Dict[str, Any], user_id: str) -> List[Dict[str, Any]]:
        """
        Export data from a specific table for a user
        
        Args:
            session: Database session
            table_name: Name of table to export
            table_config: Table configuration
            user_id: User ID to filter by
            
        Returns:
            List of table records
        """
        try:
            user_field = table_config["user_field"]
            
            # Query user's data from the table
            query = f"SELECT * FROM {table_name} WHERE {user_field} = :user_id"
            result = session.execute(text(query), {"user_id": user_id})
            columns = result.keys()
            
            records = []
            for row in result.fetchall():
                record = dict(zip(columns, row))
                
                # Convert datetime objects to ISO strings
                for key, value in record.items():
                    if isinstance(value, datetime):
                        record[key] = value.isoformat()
                    elif value is None:
                        record[key] = None
                    else:
                        record[key] = str(value) if not isinstance(value, (str, int, float, bool)) else value
                
                records.append(record)
            
            return records
            
        except Exception as e:
            logger.error(f"Error exporting data from table {table_name}: {str(e)}")
            raise
    
    async def _generate_export_file(self, user_data: Dict[str, Any], metadata: Dict[str, Any], export_format: str) -> Dict[str, Any]:
        """
        Generate export file in the specified format
        
        Args:
            user_data: User data to export
            metadata: Export metadata
            export_format: Target export format
            
        Returns:
            Export file generation results
        """
        try:
            export_filename = f"{metadata['export_id']}.{export_format}"
            export_path = self.export_dir / export_filename
            
            if export_format == "json":
                return await self._generate_json_export(user_data, metadata, export_path)
            elif export_format == "csv":
                return await self._generate_csv_export(user_data, metadata, export_path)
            elif export_format == "xml":
                return await self._generate_xml_export(user_data, metadata, export_path)
            elif export_format == "zip":
                return await self._generate_zip_export(user_data, metadata, export_path)
            else:
                raise ValueError(f"Unsupported export format: {export_format}")
                
        except Exception as e:
            logger.error(f"Error generating export file: {str(e)}")
            raise
    
    async def _generate_json_export(self, user_data: Dict[str, Any], metadata: Dict[str, Any], export_path: Path) -> Dict[str, Any]:
        """Generate JSON export file"""
        export_data = {
            "metadata": metadata,
            "data": user_data
        }
        
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "export_path": str(export_path),
            "export_size": export_path.stat().st_size,
            "format": "json",
            "metadata": metadata
        }
    
    async def _generate_csv_export(self, user_data: Dict[str, Any], metadata: Dict[str, Any], export_path: Path) -> Dict[str, Any]:
        """Generate CSV export files (one per table)"""
        # For CSV, create a ZIP file containing multiple CSV files
        zip_path = export_path.with_suffix('.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add metadata file
            metadata_csv = StringIO()
            metadata_writer = csv.writer(metadata_csv)
            metadata_writer.writerow(["Field", "Value"])
            for key, value in metadata.items():
                metadata_writer.writerow([key, value])
            
            zipf.writestr("metadata.csv", metadata_csv.getvalue())
            
            # Add data files
            for table_name, table_info in user_data.items():
                if table_info.get("records"):
                    csv_content = StringIO()
                    records = table_info["records"]
                    
                    if records:
                        # Write CSV header
                        fieldnames = records[0].keys()
                        writer = csv.DictWriter(csv_content, fieldnames=fieldnames)
                        writer.writeheader()
                        
                        # Write data rows
                        for record in records:
                            writer.writerow(record)
                    
                    zipf.writestr(f"{table_name}.csv", csv_content.getvalue())
        
        return {
            "success": True,
            "export_path": str(zip_path),
            "export_size": zip_path.stat().st_size,
            "format": "csv",
            "metadata": metadata
        }
    
    async def _generate_xml_export(self, user_data: Dict[str, Any], metadata: Dict[str, Any], export_path: Path) -> Dict[str, Any]:
        """Generate XML export file"""
        xml_content = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_content.append('<user_data_export>')
        
        # Add metadata
        xml_content.append('  <metadata>')
        for key, value in metadata.items():
            xml_content.append(f'    <{key}>{self._escape_xml(str(value))}</{key}>')
        xml_content.append('  </metadata>')
        
        # Add data
        xml_content.append('  <data>')
        for table_name, table_info in user_data.items():
            xml_content.append(f'    <{table_name}>')
            xml_content.append(f'      <description>{self._escape_xml(table_info.get("description", ""))}</description>')
            xml_content.append(f'      <count>{table_info.get("count", 0)}</count>')
            xml_content.append('      <records>')
            
            for record in table_info.get("records", []):
                xml_content.append('        <record>')
                for field, value in record.items():
                    xml_content.append(f'          <{field}>{self._escape_xml(str(value) if value is not None else "")}</{field}>')
                xml_content.append('        </record>')
            
            xml_content.append('      </records>')
            xml_content.append(f'    </{table_name}>')
        xml_content.append('  </data>')
        xml_content.append('</user_data_export>')
        
        with open(export_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(xml_content))
        
        return {
            "success": True,
            "export_path": str(export_path),
            "export_size": export_path.stat().st_size,
            "format": "xml",
            "metadata": metadata
        }
    
    async def _generate_zip_export(self, user_data: Dict[str, Any], metadata: Dict[str, Any], export_path: Path) -> Dict[str, Any]:
        """Generate comprehensive ZIP export with multiple formats"""
        with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add JSON version
            json_data = {
                "metadata": metadata,
                "data": user_data
            }
            zipf.writestr("data.json", json.dumps(json_data, indent=2, ensure_ascii=False))
            
            # Add CSV files for each table
            csv_dir = "csv_files/"
            for table_name, table_info in user_data.items():
                if table_info.get("records"):
                    csv_content = StringIO()
                    records = table_info["records"]
                    
                    if records:
                        fieldnames = records[0].keys()
                        writer = csv.DictWriter(csv_content, fieldnames=fieldnames)
                        writer.writeheader()
                        for record in records:
                            writer.writerow(record)
                    
                    zipf.writestr(f"{csv_dir}{table_name}.csv", csv_content.getvalue())
            
            # Add metadata file
            metadata_content = StringIO()
            metadata_writer = csv.writer(metadata_content)
            metadata_writer.writerow(["Field", "Value"])
            for key, value in metadata.items():
                metadata_writer.writerow([key, value])
            zipf.writestr("metadata.csv", metadata_content.getvalue())
            
            # Add README file
            readme_content = self._generate_readme_content(metadata)
            zipf.writestr("README.txt", readme_content)
        
        return {
            "success": True,
            "export_path": str(export_path),
            "export_size": export_path.stat().st_size,
            "format": "zip",
            "metadata": metadata
        }
    
    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters"""
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace('"', "&quot;")
                   .replace("'", "&apos;"))
    
    def _generate_readme_content(self, metadata: Dict[str, Any]) -> str:
        """Generate README content for export"""
        return f"""
JobSwitch.ai Data Export
========================

Export ID: {metadata.get('export_id', 'N/A')}
User ID: {metadata.get('user_id', 'N/A')}
Export Date: {metadata.get('export_date', 'N/A')}
Total Records: {metadata.get('total_records', 0)}
Tables Exported: {metadata.get('tables_exported', 0)}

This export contains all your personal data stored in JobSwitch.ai as of the export date.

Files Included:
- data.json: Complete data export in JSON format
- csv_files/: Individual CSV files for each data table
- metadata.csv: Export metadata and statistics
- README.txt: This file

Data Tables:
- user_profile: Basic user account information
- profile_details: Detailed user profile information
- skills: User skills and proficiency levels
- resumes: Resume versions and optimizations
- job_applications: Job application history and status
- interview_sessions: Interview preparation sessions and feedback
- networking_campaigns: Networking campaigns and outreach activities
- career_roadmaps: Career planning and goal tracking
- ai_interactions: AI agent interactions and task history

GDPR Compliance:
This export is provided in compliance with GDPR Article 20 (Right to data portability).
You have the right to receive your personal data in a structured, commonly used, and machine-readable format.

For questions about this export or your data rights, please contact support@jobswitch.ai
        """.strip()
    
    async def export_application_data(self, user_id: str, application_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Export specific job application data
        
        Args:
            user_id: User ID
            application_ids: Optional list of specific application IDs to export
            
        Returns:
            Export results
        """
        try:
            logger.info(f"Exporting application data for user {user_id}")
            
            with db_manager.get_session() as session:
                # Base query for job applications
                if application_ids:
                    placeholders = ", ".join([f":app_id_{i}" for i in range(len(application_ids))])
                    query = f"""
                    SELECT ja.*, j.title, j.company, j.location, j.description, j.salary_min, j.salary_max
                    FROM job_applications ja
                    LEFT JOIN jobs j ON ja.job_id = j.id
                    WHERE ja.user_id = :user_id AND ja.id IN ({placeholders})
                    """
                    params = {"user_id": user_id}
                    for i, app_id in enumerate(application_ids):
                        params[f"app_id_{i}"] = app_id
                else:
                    query = """
                    SELECT ja.*, j.title, j.company, j.location, j.description, j.salary_min, j.salary_max
                    FROM job_applications ja
                    LEFT JOIN jobs j ON ja.job_id = j.id
                    WHERE ja.user_id = :user_id
                    """
                    params = {"user_id": user_id}
                
                result = session.execute(text(query), params)
                columns = result.keys()
                
                applications = []
                for row in result.fetchall():
                    record = dict(zip(columns, row))
                    
                    # Convert datetime objects to ISO strings
                    for key, value in record.items():
                        if isinstance(value, datetime):
                            record[key] = value.isoformat()
                    
                    applications.append(record)
                
                # Also get related resume data
                resume_query = """
                SELECT * FROM resumes 
                WHERE user_id = :user_id AND target_job_id IN (
                    SELECT job_id FROM job_applications WHERE user_id = :user_id
                )
                """
                
                resume_result = session.execute(text(resume_query), {"user_id": user_id})
                resume_columns = resume_result.keys()
                
                resumes = []
                for row in resume_result.fetchall():
                    record = dict(zip(resume_columns, row))
                    
                    # Convert datetime objects to ISO strings
                    for key, value in record.items():
                        if isinstance(value, datetime):
                            record[key] = value.isoformat()
                    
                    resumes.append(record)
            
            # Create export data structure
            export_data = {
                "metadata": {
                    "export_type": "job_applications",
                    "user_id": user_id,
                    "export_date": datetime.now().isoformat(),
                    "applications_count": len(applications),
                    "resumes_count": len(resumes)
                },
                "job_applications": applications,
                "related_resumes": resumes
            }
            
            # Generate JSON export
            export_filename = f"applications_export_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            export_path = self.export_dir / export_filename
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return {
                "success": True,
                "export_path": str(export_path),
                "export_size": export_path.stat().st_size,
                "applications_exported": len(applications),
                "resumes_exported": len(resumes)
            }
            
        except Exception as e:
            logger.error(f"Application data export failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_user_exports(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all exports for a specific user
        
        Args:
            user_id: User ID to list exports for
            
        Returns:
            List of user exports
        """
        try:
            exports = []
            
            # Look for export files containing the user ID
            for export_file in self.export_dir.glob(f"*{user_id}*"):
                try:
                    stat = export_file.stat()
                    
                    export_info = {
                        "filename": export_file.name,
                        "path": str(export_file),
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "format": export_file.suffix.lstrip('.')
                    }
                    
                    # Try to read metadata if it's a JSON file
                    if export_file.suffix == '.json':
                        try:
                            with open(export_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                if "metadata" in data:
                                    export_info.update(data["metadata"])
                        except:
                            pass
                    
                    exports.append(export_info)
                    
                except Exception as e:
                    logger.error(f"Error reading export file {export_file}: {str(e)}")
            
            # Sort by creation date (newest first)
            exports.sort(key=lambda x: x["created"], reverse=True)
            
            return exports
            
        except Exception as e:
            logger.error(f"Error listing user exports: {str(e)}")
            return []
    
    async def delete_user_export(self, user_id: str, export_filename: str) -> Dict[str, Any]:
        """
        Delete a specific user export file
        
        Args:
            user_id: User ID (for security verification)
            export_filename: Export filename to delete
            
        Returns:
            Deletion results
        """
        try:
            export_path = self.export_dir / export_filename
            
            # Verify the export belongs to the user
            if user_id not in export_filename:
                return {
                    "success": False,
                    "error": "Export file does not belong to the specified user"
                }
            
            if not export_path.exists():
                return {
                    "success": False,
                    "error": f"Export file not found: {export_filename}"
                }
            
            export_path.unlink()
            
            logger.info(f"Deleted user export: {export_filename}")
            return {
                "success": True,
                "message": f"Export deleted successfully: {export_filename}"
            }
            
        except Exception as e:
            logger.error(f"Error deleting user export {export_filename}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Global data export manager instance
data_export_manager = DataExportManager()


# Convenience functions for common export operations
async def export_user_data_json(user_id: str) -> Dict[str, Any]:
    """Export all user data in JSON format"""
    return await data_export_manager.export_user_data(user_id, "json")


async def export_user_data_csv(user_id: str) -> Dict[str, Any]:
    """Export all user data in CSV format"""
    return await data_export_manager.export_user_data(user_id, "csv")


async def export_user_data_complete(user_id: str) -> Dict[str, Any]:
    """Export all user data in comprehensive ZIP format"""
    return await data_export_manager.export_user_data(user_id, "zip")


async def export_job_applications(user_id: str, application_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """Export job application data for a user"""
    return await data_export_manager.export_application_data(user_id, application_ids)


async def list_user_data_exports(user_id: str) -> List[Dict[str, Any]]:
    """List all data exports for a user"""
    return await data_export_manager.list_user_exports(user_id)