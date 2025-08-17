"""
Data Management API Endpoints
Handles caching, backup, recovery, and data export operations
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from app.core.auth import get_current_user
from app.core.cache import cache_manager, get_cache_stats
from app.core.database_optimization import db_optimizer
from app.core.backup_manager import backup_manager
from app.core.data_export import data_export_manager
from app.models.auth_schemas import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-management", tags=["Data Management"])


# Pydantic models for request/response
class CacheStatsResponse(BaseModel):
    enabled: bool
    connected_clients: Optional[int] = None
    used_memory: Optional[str] = None
    total_commands_processed: Optional[int] = None
    keyspace_hits: Optional[int] = None
    keyspace_misses: Optional[int] = None
    hit_rate: Optional[float] = None
    key_counts: Optional[Dict[str, int]] = None
    cache_ttl_settings: Optional[Dict[str, int]] = None
    error: Optional[str] = None


class BackupRequest(BaseModel):
    backup_name: Optional[str] = Field(None, description="Custom backup name")
    backup_type: str = Field("full", description="Backup type: full or incremental")
    since_date: Optional[datetime] = Field(None, description="For incremental backups: backup changes since this date")


class RestoreRequest(BaseModel):
    backup_filename: str = Field(..., description="Backup file to restore from")
    clear_existing: bool = Field(False, description="Whether to clear existing data before restore")


class DataExportRequest(BaseModel):
    export_format: str = Field("json", description="Export format: json, csv, xml, or zip")
    include_tables: Optional[List[str]] = Field(None, description="Specific tables to include in export")


class ApplicationExportRequest(BaseModel):
    application_ids: Optional[List[str]] = Field(None, description="Specific application IDs to export")


# Cache Management Endpoints
@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_statistics(current_user: UserResponse = Depends(get_current_user)):
    """
    Get Redis cache statistics and performance metrics
    """
    try:
        stats = await cache_manager.get_cache_stats()
        return CacheStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache statistics: {str(e)}")


@router.delete("/cache/clear")
async def clear_cache(current_user: UserResponse = Depends(get_current_user)):
    """
    Clear all cache data (admin only)
    """
    try:
        # Only allow admin users to clear cache
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        success = await cache_manager.clear_all()
        
        if success:
            return {"message": "Cache cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear cache")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.delete("/cache/user/{user_id}")
async def clear_user_cache(user_id: str, current_user: UserResponse = Depends(get_current_user)):
    """
    Clear cache data for a specific user
    """
    try:
        # Users can only clear their own cache, admins can clear any user's cache
        if str(current_user.user_id) != user_id and not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Access denied")
        
        from app.core.cache import invalidate_user_cache
        deleted_count = await invalidate_user_cache(user_id)
        
        return {
            "message": f"User cache cleared successfully",
            "deleted_entries": deleted_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing user cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear user cache: {str(e)}")


# Database Optimization Endpoints
@router.post("/database/optimize")
async def optimize_database(current_user: UserResponse = Depends(get_current_user)):
    """
    Perform comprehensive database optimization (admin only)
    """
    try:
        # Only allow admin users to optimize database
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        results = await db_optimizer.optimize_database()
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database optimization failed: {str(e)}")


@router.post("/database/create-indexes")
async def create_performance_indexes(current_user: UserResponse = Depends(get_current_user)):
    """
    Create performance-critical database indexes (admin only)
    """
    try:
        # Only allow admin users to create indexes
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        results = await db_optimizer.create_indexes()
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating indexes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Index creation failed: {str(e)}")


@router.get("/database/stats")
async def get_database_statistics(current_user: UserResponse = Depends(get_current_user)):
    """
    Get comprehensive database statistics (admin only)
    """
    try:
        # Only allow admin users to view database stats
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        stats = await db_optimizer.get_database_statistics()
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get database statistics: {str(e)}")


@router.post("/database/analyze-query")
async def analyze_query_performance(
    query: str,
    params: Optional[Dict[str, Any]] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Analyze query performance and get optimization recommendations (admin only)
    """
    try:
        # Only allow admin users to analyze queries
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        analysis = await db_optimizer.analyze_query_performance(query, params)
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query analysis failed: {str(e)}")


# Backup Management Endpoints
@router.post("/backup/create")
async def create_backup(
    backup_request: BackupRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a database backup (admin only)
    """
    try:
        # Only allow admin users to create backups
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        if backup_request.backup_type == "full":
            # Create full backup in background
            background_tasks.add_task(
                backup_manager.create_full_backup,
                backup_request.backup_name
            )
            return {"message": "Full backup started in background"}
            
        elif backup_request.backup_type == "incremental":
            if not backup_request.since_date:
                raise HTTPException(status_code=400, detail="since_date required for incremental backup")
            
            # Create incremental backup in background
            background_tasks.add_task(
                backup_manager.create_incremental_backup,
                backup_request.since_date,
                backup_request.backup_name
            )
            return {"message": "Incremental backup started in background"}
            
        else:
            raise HTTPException(status_code=400, detail="Invalid backup type. Use 'full' or 'incremental'")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backup creation failed: {str(e)}")


@router.get("/backup/list")
async def list_backups(current_user: UserResponse = Depends(get_current_user)):
    """
    List all available backups (admin only)
    """
    try:
        # Only allow admin users to list backups
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        backups = await backup_manager.list_backups()
        return {"backups": backups}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing backups: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")


@router.post("/backup/restore")
async def restore_backup(
    restore_request: RestoreRequest,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Restore database from backup (admin only)
    """
    try:
        # Only allow admin users to restore backups
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Restore backup in background
        restore_options = {"clear_existing": restore_request.clear_existing}
        background_tasks.add_task(
            backup_manager.restore_backup,
            f"backups/{restore_request.backup_filename}",
            restore_options
        )
        
        return {"message": "Database restore started in background"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring backup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backup restore failed: {str(e)}")


@router.delete("/backup/{backup_filename}")
async def delete_backup(backup_filename: str, current_user: UserResponse = Depends(get_current_user)):
    """
    Delete a specific backup file (admin only)
    """
    try:
        # Only allow admin users to delete backups
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        result = await backup_manager.delete_backup(backup_filename)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting backup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backup deletion failed: {str(e)}")


# Data Export Endpoints
@router.post("/export/user-data")
async def export_user_data(
    export_request: DataExportRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Export all user data for GDPR compliance and data portability
    """
    try:
        user_id = str(current_user.user_id)
        
        result = await data_export_manager.export_user_data(
            user_id,
            export_request.export_format,
            export_request.include_tables
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting user data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Data export failed: {str(e)}")


@router.post("/export/applications")
async def export_application_data(
    export_request: ApplicationExportRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Export job application data for a user
    """
    try:
        user_id = str(current_user.user_id)
        
        result = await data_export_manager.export_application_data(
            user_id,
            export_request.application_ids
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting application data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Application data export failed: {str(e)}")


@router.get("/export/list")
async def list_user_exports(current_user: UserResponse = Depends(get_current_user)):
    """
    List all data exports for the current user
    """
    try:
        user_id = str(current_user.user_id)
        exports = await data_export_manager.list_user_exports(user_id)
        return {"exports": exports}
        
    except Exception as e:
        logger.error(f"Error listing user exports: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list exports: {str(e)}")


@router.get("/export/download/{export_filename}")
async def download_export_file(
    export_filename: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Download a specific export file
    """
    try:
        user_id = str(current_user.user_id)
        
        # Verify the export belongs to the user
        if user_id not in export_filename:
            raise HTTPException(status_code=403, detail="Access denied")
        
        export_path = f"exports/{export_filename}"
        
        # Check if file exists
        from pathlib import Path
        if not Path(export_path).exists():
            raise HTTPException(status_code=404, detail="Export file not found")
        
        return FileResponse(
            path=export_path,
            filename=export_filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading export file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export download failed: {str(e)}")


@router.delete("/export/{export_filename}")
async def delete_user_export(
    export_filename: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete a specific user export file
    """
    try:
        user_id = str(current_user.user_id)
        
        result = await data_export_manager.delete_user_export(user_id, export_filename)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user export: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export deletion failed: {str(e)}")


# System Health Endpoints
@router.get("/health")
async def get_system_health(current_user: UserResponse = Depends(get_current_user)):
    """
    Get comprehensive system health status including cache, database, and backup systems
    """
    try:
        # Only allow admin users to view system health
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get cache health
        cache_stats = await cache_manager.get_cache_stats()
        cache_healthy = cache_stats.get("enabled", False) and "error" not in cache_stats
        
        # Get database health
        from app.core.database import db_manager
        db_healthy = db_manager.check_connection()
        
        # Get backup system health
        backups = await backup_manager.list_backups()
        backup_healthy = len(backups) > 0  # At least one backup exists
        
        overall_health = "healthy" if all([cache_healthy, db_healthy, backup_healthy]) else "degraded"
        
        return {
            "overall_status": overall_health,
            "components": {
                "cache": {
                    "status": "healthy" if cache_healthy else "unhealthy",
                    "details": cache_stats
                },
                "database": {
                    "status": "healthy" if db_healthy else "unhealthy",
                    "connection": db_healthy
                },
                "backup_system": {
                    "status": "healthy" if backup_healthy else "warning",
                    "backup_count": len(backups),
                    "latest_backup": backups[0] if backups else None
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")