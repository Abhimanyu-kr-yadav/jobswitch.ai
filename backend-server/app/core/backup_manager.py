"""
Data Backup and Recovery Manager
Handles automated backups, data export, and recovery procedures for JobSwitch.ai
"""
import os
import json
import gzip
import shutil
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import sqlite3
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import db_manager, engine
from app.core.config import settings

logger = logging.getLogger(__name__)


class BackupManager:
    """
    Comprehensive backup and recovery manager
    """
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Backup configuration
        self.backup_config = {
            "retention_days": 30,  # Keep backups for 30 days
            "max_backups": 50,     # Maximum number of backups to keep
            "compress_backups": True,
            "backup_schedule": {
                "daily": True,
                "weekly": True,
                "monthly": True
            }
        }
        
        # Tables to include in backups (all by default)
        self.backup_tables = [
            "users",
            "user_profiles", 
            "user_skills",
            "jobs",
            "job_applications",
            "resumes",
            "interview_sessions",
            "networking_campaigns",
            "contacts",
            "career_roadmaps",
            "agent_tasks",
            "agent_responses"
        ]
    
    async def create_full_backup(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a complete database backup
        
        Args:
            backup_name: Optional custom backup name
            
        Returns:
            Backup creation results
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = backup_name or f"full_backup_{timestamp}"
            
            backup_path = self.backup_dir / f"{backup_name}.json"
            
            logger.info(f"Starting full backup: {backup_name}")
            
            backup_data = {
                "metadata": {
                    "backup_name": backup_name,
                    "created_at": datetime.now().isoformat(),
                    "database_type": engine.dialect.name,
                    "backup_type": "full",
                    "version": "1.0"
                },
                "tables": {}
            }
            
            # Backup each table
            with db_manager.get_session() as session:
                for table_name in self.backup_tables:
                    try:
                        table_data = await self._backup_table(session, table_name)
                        backup_data["tables"][table_name] = table_data
                        logger.debug(f"Backed up table: {table_name} ({len(table_data)} records)")
                        
                    except Exception as e:
                        logger.error(f"Error backing up table {table_name}: {str(e)}")
                        backup_data["tables"][table_name] = {
                            "error": str(e),
                            "records": []
                        }
            
            # Save backup file
            if self.backup_config["compress_backups"]:
                # Save as compressed JSON
                compressed_path = backup_path.with_suffix('.json.gz')
                with gzip.open(compressed_path, 'wt', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, default=str)
                backup_path = compressed_path
            else:
                # Save as regular JSON
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, default=str)
            
            # Calculate backup size
            backup_size = backup_path.stat().st_size
            
            # Clean up old backups
            await self._cleanup_old_backups()
            
            result = {
                "success": True,
                "backup_name": backup_name,
                "backup_path": str(backup_path),
                "backup_size": backup_size,
                "tables_backed_up": len([t for t in backup_data["tables"] if "error" not in backup_data["tables"][t]]),
                "total_tables": len(self.backup_tables),
                "created_at": backup_data["metadata"]["created_at"]
            }
            
            logger.info(f"Full backup completed successfully: {backup_name}")
            return result
            
        except Exception as e:
            logger.error(f"Full backup failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_incremental_backup(self, since: datetime, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create an incremental backup of changes since a specific date
        
        Args:
            since: Date to backup changes since
            backup_name: Optional custom backup name
            
        Returns:
            Backup creation results
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = backup_name or f"incremental_backup_{timestamp}"
            
            backup_path = self.backup_dir / f"{backup_name}.json"
            
            logger.info(f"Starting incremental backup since {since}: {backup_name}")
            
            backup_data = {
                "metadata": {
                    "backup_name": backup_name,
                    "created_at": datetime.now().isoformat(),
                    "database_type": engine.dialect.name,
                    "backup_type": "incremental",
                    "since": since.isoformat(),
                    "version": "1.0"
                },
                "tables": {}
            }
            
            # Backup changes for each table
            with db_manager.get_session() as session:
                for table_name in self.backup_tables:
                    try:
                        table_data = await self._backup_table_incremental(session, table_name, since)
                        if table_data:  # Only include tables with changes
                            backup_data["tables"][table_name] = table_data
                            logger.debug(f"Backed up incremental changes for table: {table_name} ({len(table_data)} records)")
                        
                    except Exception as e:
                        logger.error(f"Error backing up incremental changes for table {table_name}: {str(e)}")
            
            # Save backup file only if there are changes
            if backup_data["tables"]:
                if self.backup_config["compress_backups"]:
                    compressed_path = backup_path.with_suffix('.json.gz')
                    with gzip.open(compressed_path, 'wt', encoding='utf-8') as f:
                        json.dump(backup_data, f, indent=2, default=str)
                    backup_path = compressed_path
                else:
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        json.dump(backup_data, f, indent=2, default=str)
                
                backup_size = backup_path.stat().st_size
                
                result = {
                    "success": True,
                    "backup_name": backup_name,
                    "backup_path": str(backup_path),
                    "backup_size": backup_size,
                    "tables_with_changes": len(backup_data["tables"]),
                    "total_tables": len(self.backup_tables),
                    "created_at": backup_data["metadata"]["created_at"],
                    "since": since.isoformat()
                }
            else:
                result = {
                    "success": True,
                    "backup_name": backup_name,
                    "message": "No changes found since specified date",
                    "tables_with_changes": 0,
                    "since": since.isoformat()
                }
            
            logger.info(f"Incremental backup completed: {backup_name}")
            return result
            
        except Exception as e:
            logger.error(f"Incremental backup failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _backup_table(self, session: Session, table_name: str) -> List[Dict[str, Any]]:
        """
        Backup all data from a specific table
        
        Args:
            session: Database session
            table_name: Name of table to backup
            
        Returns:
            List of table records
        """
        try:
            # Execute raw SQL to get all data
            result = session.execute(text(f"SELECT * FROM {table_name}"))
            columns = result.keys()
            
            records = []
            for row in result.fetchall():
                record = dict(zip(columns, row))
                # Convert datetime objects to ISO strings
                for key, value in record.items():
                    if isinstance(value, datetime):
                        record[key] = value.isoformat()
                records.append(record)
            
            return records
            
        except Exception as e:
            logger.error(f"Error backing up table {table_name}: {str(e)}")
            raise
    
    async def _backup_table_incremental(self, session: Session, table_name: str, since: datetime) -> List[Dict[str, Any]]:
        """
        Backup incremental changes from a specific table
        
        Args:
            session: Database session
            table_name: Name of table to backup
            since: Date to backup changes since
            
        Returns:
            List of changed records
        """
        try:
            # Try to find records with updated_at or created_at columns
            date_columns = ["updated_at", "created_at", "modified_at"]
            
            for date_column in date_columns:
                try:
                    # Check if column exists
                    result = session.execute(text(f"SELECT {date_column} FROM {table_name} LIMIT 1"))
                    
                    # If successful, use this column for incremental backup
                    query = f"SELECT * FROM {table_name} WHERE {date_column} >= :since_date"
                    result = session.execute(text(query), {"since_date": since})
                    columns = result.keys()
                    
                    records = []
                    for row in result.fetchall():
                        record = dict(zip(columns, row))
                        # Convert datetime objects to ISO strings
                        for key, value in record.items():
                            if isinstance(value, datetime):
                                record[key] = value.isoformat()
                        records.append(record)
                    
                    return records
                    
                except Exception:
                    # Column doesn't exist, try next one
                    continue
            
            # If no date columns found, return empty list
            logger.warning(f"No date columns found for incremental backup of table: {table_name}")
            return []
            
        except Exception as e:
            logger.error(f"Error backing up incremental changes for table {table_name}: {str(e)}")
            raise
    
    async def restore_backup(self, backup_path: str, restore_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Restore database from backup file
        
        Args:
            backup_path: Path to backup file
            restore_options: Optional restore configuration
            
        Returns:
            Restore operation results
        """
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            logger.info(f"Starting database restore from: {backup_path}")
            
            # Load backup data
            if backup_file.suffix == '.gz':
                with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                    backup_data = json.load(f)
            else:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
            
            restore_options = restore_options or {}
            
            # Validate backup format
            if "metadata" not in backup_data or "tables" not in backup_data:
                raise ValueError("Invalid backup format")
            
            results = {
                "success": True,
                "backup_name": backup_data["metadata"].get("backup_name", "unknown"),
                "backup_created_at": backup_data["metadata"].get("created_at", "unknown"),
                "tables_restored": 0,
                "records_restored": 0,
                "errors": []
            }
            
            # Restore each table
            with db_manager.get_session() as session:
                for table_name, table_data in backup_data["tables"].items():
                    if "error" in table_data:
                        results["errors"].append(f"Skipping table {table_name}: {table_data['error']}")
                        continue
                    
                    try:
                        # Clear existing data if full restore
                        if restore_options.get("clear_existing", False):
                            session.execute(text(f"DELETE FROM {table_name}"))
                        
                        # Insert backup data
                        records_count = await self._restore_table_data(session, table_name, table_data)
                        results["tables_restored"] += 1
                        results["records_restored"] += records_count
                        
                        logger.debug(f"Restored table: {table_name} ({records_count} records)")
                        
                    except Exception as e:
                        error_msg = f"Error restoring table {table_name}: {str(e)}"
                        results["errors"].append(error_msg)
                        logger.error(error_msg)
                
                session.commit()
            
            logger.info(f"Database restore completed: {results['tables_restored']} tables, {results['records_restored']} records")
            return results
            
        except Exception as e:
            logger.error(f"Database restore failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _restore_table_data(self, session: Session, table_name: str, table_data: List[Dict[str, Any]]) -> int:
        """
        Restore data to a specific table
        
        Args:
            session: Database session
            table_name: Name of table to restore
            table_data: List of records to restore
            
        Returns:
            Number of records restored
        """
        if not table_data:
            return 0
        
        # Get column names from first record
        columns = list(table_data[0].keys())
        columns_str = ", ".join(columns)
        placeholders = ", ".join([f":{col}" for col in columns])
        
        # Prepare insert statement
        insert_sql = f"INSERT OR REPLACE INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        # Insert all records
        for record in table_data:
            # Convert ISO strings back to datetime objects where needed
            processed_record = {}
            for key, value in record.items():
                if isinstance(value, str) and key.endswith(('_at', '_date')):
                    try:
                        processed_record[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except:
                        processed_record[key] = value
                else:
                    processed_record[key] = value
            
            session.execute(text(insert_sql), processed_record)
        
        return len(table_data)
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """
        List all available backups
        
        Returns:
            List of backup information
        """
        try:
            backups = []
            
            for backup_file in self.backup_dir.glob("*.json*"):
                try:
                    # Get file stats
                    stat = backup_file.stat()
                    
                    # Try to read metadata
                    metadata = None
                    try:
                        if backup_file.suffix == '.gz':
                            with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                                data = json.load(f)
                        else:
                            with open(backup_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                        
                        metadata = data.get("metadata", {})
                    except:
                        pass
                    
                    backup_info = {
                        "filename": backup_file.name,
                        "path": str(backup_file),
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "compressed": backup_file.suffix == '.gz'
                    }
                    
                    if metadata:
                        backup_info.update({
                            "backup_name": metadata.get("backup_name"),
                            "backup_type": metadata.get("backup_type"),
                            "database_type": metadata.get("database_type"),
                            "version": metadata.get("version")
                        })
                    
                    backups.append(backup_info)
                    
                except Exception as e:
                    logger.error(f"Error reading backup file {backup_file}: {str(e)}")
            
            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x["created"], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Error listing backups: {str(e)}")
            return []
    
    async def delete_backup(self, backup_filename: str) -> Dict[str, Any]:
        """
        Delete a specific backup file
        
        Args:
            backup_filename: Name of backup file to delete
            
        Returns:
            Deletion results
        """
        try:
            backup_path = self.backup_dir / backup_filename
            
            if not backup_path.exists():
                return {
                    "success": False,
                    "error": f"Backup file not found: {backup_filename}"
                }
            
            backup_path.unlink()
            
            logger.info(f"Deleted backup: {backup_filename}")
            return {
                "success": True,
                "message": f"Backup deleted successfully: {backup_filename}"
            }
            
        except Exception as e:
            logger.error(f"Error deleting backup {backup_filename}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _cleanup_old_backups(self):
        """
        Clean up old backups based on retention policy
        """
        try:
            backups = await self.list_backups()
            
            # Remove backups older than retention period
            cutoff_date = datetime.now() - timedelta(days=self.backup_config["retention_days"])
            
            old_backups = [
                b for b in backups 
                if datetime.fromisoformat(b["created"]) < cutoff_date
            ]
            
            # Also remove excess backups if we have too many
            if len(backups) > self.backup_config["max_backups"]:
                excess_backups = backups[self.backup_config["max_backups"]:]
                old_backups.extend(excess_backups)
            
            # Delete old backups
            for backup in old_backups:
                await self.delete_backup(backup["filename"])
            
            if old_backups:
                logger.info(f"Cleaned up {len(old_backups)} old backups")
                
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {str(e)}")
    
    async def schedule_automated_backups(self):
        """
        Set up automated backup scheduling
        """
        logger.info("Starting automated backup scheduler")
        
        while True:
            try:
                now = datetime.now()
                
                # Daily backup at 2 AM
                if now.hour == 2 and now.minute == 0:
                    if self.backup_config["backup_schedule"]["daily"]:
                        await self.create_full_backup(f"daily_backup_{now.strftime('%Y%m%d')}")
                
                # Weekly backup on Sunday at 3 AM
                if now.weekday() == 6 and now.hour == 3 and now.minute == 0:
                    if self.backup_config["backup_schedule"]["weekly"]:
                        await self.create_full_backup(f"weekly_backup_{now.strftime('%Y%m%d')}")
                
                # Monthly backup on 1st day at 4 AM
                if now.day == 1 and now.hour == 4 and now.minute == 0:
                    if self.backup_config["backup_schedule"]["monthly"]:
                        await self.create_full_backup(f"monthly_backup_{now.strftime('%Y%m%d')}")
                
                # Sleep for 1 minute
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in automated backup scheduler: {str(e)}")
                await asyncio.sleep(300)  # Sleep 5 minutes on error


# Global backup manager instance
backup_manager = BackupManager()


# Convenience functions for common backup operations
async def create_database_backup(backup_name: Optional[str] = None) -> Dict[str, Any]:
    """Create a full database backup"""
    return await backup_manager.create_full_backup(backup_name)


async def create_incremental_backup_since(since: datetime, backup_name: Optional[str] = None) -> Dict[str, Any]:
    """Create an incremental backup since a specific date"""
    return await backup_manager.create_incremental_backup(since, backup_name)


async def restore_database_from_backup(backup_path: str, clear_existing: bool = False) -> Dict[str, Any]:
    """Restore database from a backup file"""
    restore_options = {"clear_existing": clear_existing}
    return await backup_manager.restore_backup(backup_path, restore_options)


async def list_available_backups() -> List[Dict[str, Any]]:
    """List all available backup files"""
    return await backup_manager.list_backups()


async def start_backup_scheduler():
    """Start the automated backup scheduler"""
    asyncio.create_task(backup_manager.schedule_automated_backups())