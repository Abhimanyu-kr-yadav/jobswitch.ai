"""
Database Optimization and Indexing Strategy
Handles database performance optimization, indexing, and query analysis
"""
import logging
from typing import Dict, List, Any, Optional
from sqlalchemy import text, Index, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from app.core.database import db_manager, engine
from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """
    Database optimization and indexing manager
    """
    
    def __init__(self):
        self.engine = engine
        self.db_manager = db_manager
        
        # Define critical indexes for performance
        self.critical_indexes = {
            # User-related indexes
            "users": [
                {"columns": ["email"], "unique": True, "name": "idx_users_email"},
                {"columns": ["created_at"], "unique": False, "name": "idx_users_created_at"},
                {"columns": ["is_active"], "unique": False, "name": "idx_users_is_active"},
            ],
            
            # Job-related indexes
            "jobs": [
                {"columns": ["title"], "unique": False, "name": "idx_jobs_title"},
                {"columns": ["company"], "unique": False, "name": "idx_jobs_company"},
                {"columns": ["location"], "unique": False, "name": "idx_jobs_location"},
                {"columns": ["source"], "unique": False, "name": "idx_jobs_source"},
                {"columns": ["posted_date"], "unique": False, "name": "idx_jobs_posted_date"},
                {"columns": ["salary_min", "salary_max"], "unique": False, "name": "idx_jobs_salary_range"},
                {"columns": ["is_active"], "unique": False, "name": "idx_jobs_is_active"},
                {"columns": ["created_at"], "unique": False, "name": "idx_jobs_created_at"},
            ],
            
            # User profile indexes
            "user_profiles": [
                {"columns": ["user_id"], "unique": True, "name": "idx_user_profiles_user_id"},
                {"columns": ["current_role"], "unique": False, "name": "idx_user_profiles_current_role"},
                {"columns": ["experience_level"], "unique": False, "name": "idx_user_profiles_experience_level"},
                {"columns": ["updated_at"], "unique": False, "name": "idx_user_profiles_updated_at"},
            ],
            
            # Skills indexes
            "user_skills": [
                {"columns": ["user_id"], "unique": False, "name": "idx_user_skills_user_id"},
                {"columns": ["skill_name"], "unique": False, "name": "idx_user_skills_skill_name"},
                {"columns": ["proficiency_level"], "unique": False, "name": "idx_user_skills_proficiency_level"},
                {"columns": ["user_id", "skill_name"], "unique": True, "name": "idx_user_skills_user_skill"},
            ],
            
            # Resume indexes
            "resumes": [
                {"columns": ["user_id"], "unique": False, "name": "idx_resumes_user_id"},
                {"columns": ["target_job_id"], "unique": False, "name": "idx_resumes_target_job_id"},
                {"columns": ["version"], "unique": False, "name": "idx_resumes_version"},
                {"columns": ["ats_score"], "unique": False, "name": "idx_resumes_ats_score"},
                {"columns": ["created_at"], "unique": False, "name": "idx_resumes_created_at"},
                {"columns": ["user_id", "version"], "unique": True, "name": "idx_resumes_user_version"},
            ],
            
            # Interview session indexes
            "interview_sessions": [
                {"columns": ["user_id"], "unique": False, "name": "idx_interview_sessions_user_id"},
                {"columns": ["job_role"], "unique": False, "name": "idx_interview_sessions_job_role"},
                {"columns": ["session_type"], "unique": False, "name": "idx_interview_sessions_session_type"},
                {"columns": ["created_at"], "unique": False, "name": "idx_interview_sessions_created_at"},
                {"columns": ["overall_score"], "unique": False, "name": "idx_interview_sessions_overall_score"},
            ],
            
            # Networking campaign indexes
            "networking_campaigns": [
                {"columns": ["user_id"], "unique": False, "name": "idx_networking_campaigns_user_id"},
                {"columns": ["target_company"], "unique": False, "name": "idx_networking_campaigns_target_company"},
                {"columns": ["status"], "unique": False, "name": "idx_networking_campaigns_status"},
                {"columns": ["created_at"], "unique": False, "name": "idx_networking_campaigns_created_at"},
            ],
            
            # Contact indexes
            "contacts": [
                {"columns": ["campaign_id"], "unique": False, "name": "idx_contacts_campaign_id"},
                {"columns": ["company"], "unique": False, "name": "idx_contacts_company"},
                {"columns": ["role"], "unique": False, "name": "idx_contacts_role"},
                {"columns": ["email"], "unique": False, "name": "idx_contacts_email"},
                {"columns": ["contact_status"], "unique": False, "name": "idx_contacts_contact_status"},
            ],
            
            # Career roadmap indexes
            "career_roadmaps": [
                {"columns": ["user_id"], "unique": False, "name": "idx_career_roadmaps_user_id"},
                {"columns": ["current_role"], "unique": False, "name": "idx_career_roadmaps_current_role"},
                {"columns": ["target_role"], "unique": False, "name": "idx_career_roadmaps_target_role"},
                {"columns": ["created_at"], "unique": False, "name": "idx_career_roadmaps_created_at"},
                {"columns": ["progress"], "unique": False, "name": "idx_career_roadmaps_progress"},
            ],
            
            # Agent task indexes
            "agent_tasks": [
                {"columns": ["agent_id"], "unique": False, "name": "idx_agent_tasks_agent_id"},
                {"columns": ["user_id"], "unique": False, "name": "idx_agent_tasks_user_id"},
                {"columns": ["task_type"], "unique": False, "name": "idx_agent_tasks_task_type"},
                {"columns": ["status"], "unique": False, "name": "idx_agent_tasks_status"},
                {"columns": ["created_at"], "unique": False, "name": "idx_agent_tasks_created_at"},
                {"columns": ["completed_at"], "unique": False, "name": "idx_agent_tasks_completed_at"},
                {"columns": ["priority"], "unique": False, "name": "idx_agent_tasks_priority"},
            ],
            
            # Application tracking indexes
            "job_applications": [
                {"columns": ["user_id"], "unique": False, "name": "idx_job_applications_user_id"},
                {"columns": ["job_id"], "unique": False, "name": "idx_job_applications_job_id"},
                {"columns": ["status"], "unique": False, "name": "idx_job_applications_status"},
                {"columns": ["applied_date"], "unique": False, "name": "idx_job_applications_applied_date"},
                {"columns": ["user_id", "job_id"], "unique": True, "name": "idx_job_applications_user_job"},
            ],
        }
    
    async def create_indexes(self) -> Dict[str, Any]:
        """
        Create all critical indexes for optimal performance
        
        Returns:
            Dictionary with index creation results
        """
        results = {
            "created": [],
            "skipped": [],
            "errors": []
        }
        
        try:
            with self.engine.connect() as connection:
                # Get existing indexes
                existing_indexes = await self._get_existing_indexes(connection)
                
                for table_name, indexes in self.critical_indexes.items():
                    for index_config in indexes:
                        index_name = index_config["name"]
                        
                        # Skip if index already exists
                        if index_name in existing_indexes:
                            results["skipped"].append(index_name)
                            continue
                        
                        try:
                            # Create index
                            await self._create_index(connection, table_name, index_config)
                            results["created"].append(index_name)
                            logger.info(f"Created index: {index_name}")
                            
                        except Exception as e:
                            error_msg = f"Failed to create index {index_name}: {str(e)}"
                            results["errors"].append(error_msg)
                            logger.error(error_msg)
                
                connection.commit()
                
        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")
            results["errors"].append(str(e))
        
        return results
    
    async def _get_existing_indexes(self, connection) -> List[str]:
        """
        Get list of existing indexes
        
        Args:
            connection: Database connection
            
        Returns:
            List of existing index names
        """
        try:
            if self.engine.dialect.name == 'sqlite':
                # SQLite query for indexes
                result = connection.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
                """))
            elif self.engine.dialect.name == 'postgresql':
                # PostgreSQL query for indexes
                result = connection.execute(text("""
                    SELECT indexname FROM pg_indexes 
                    WHERE schemaname = 'public'
                """))
            else:
                # MySQL query for indexes
                result = connection.execute(text("""
                    SELECT INDEX_NAME FROM information_schema.statistics 
                    WHERE TABLE_SCHEMA = DATABASE()
                """))
            
            return [row[0] for row in result.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting existing indexes: {str(e)}")
            return []
    
    async def _create_index(self, connection, table_name: str, index_config: Dict[str, Any]):
        """
        Create a single index
        
        Args:
            connection: Database connection
            table_name: Name of the table
            index_config: Index configuration
        """
        columns = index_config["columns"]
        index_name = index_config["name"]
        unique = index_config.get("unique", False)
        
        # Build CREATE INDEX statement
        unique_clause = "UNIQUE " if unique else ""
        columns_clause = ", ".join(columns)
        
        sql = f"""
        CREATE {unique_clause}INDEX IF NOT EXISTS {index_name} 
        ON {table_name} ({columns_clause})
        """
        
        connection.execute(text(sql))
    
    async def analyze_query_performance(self, query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze query performance and suggest optimizations
        
        Args:
            query: SQL query to analyze
            params: Query parameters
            
        Returns:
            Performance analysis results
        """
        try:
            with self.engine.connect() as connection:
                # Execute EXPLAIN QUERY PLAN (SQLite) or EXPLAIN (PostgreSQL/MySQL)
                if self.engine.dialect.name == 'sqlite':
                    explain_query = f"EXPLAIN QUERY PLAN {query}"
                else:
                    explain_query = f"EXPLAIN {query}"
                
                result = connection.execute(text(explain_query), params or {})
                execution_plan = result.fetchall()
                
                # Analyze the execution plan
                analysis = self._analyze_execution_plan(execution_plan)
                
                return {
                    "query": query,
                    "execution_plan": [dict(row._mapping) for row in execution_plan],
                    "analysis": analysis,
                    "recommendations": self._generate_recommendations(analysis)
                }
                
        except Exception as e:
            logger.error(f"Error analyzing query performance: {str(e)}")
            return {
                "query": query,
                "error": str(e)
            }
    
    def _analyze_execution_plan(self, execution_plan: List) -> Dict[str, Any]:
        """
        Analyze execution plan for performance issues
        
        Args:
            execution_plan: Database execution plan
            
        Returns:
            Analysis results
        """
        analysis = {
            "has_table_scan": False,
            "uses_indexes": False,
            "join_operations": 0,
            "sort_operations": 0,
            "potential_issues": []
        }
        
        for row in execution_plan:
            row_str = str(row).lower()
            
            # Check for table scans
            if "scan table" in row_str or "seq scan" in row_str:
                analysis["has_table_scan"] = True
                analysis["potential_issues"].append("Table scan detected - consider adding indexes")
            
            # Check for index usage
            if "using index" in row_str or "index scan" in row_str:
                analysis["uses_indexes"] = True
            
            # Count join operations
            if "join" in row_str:
                analysis["join_operations"] += 1
            
            # Count sort operations
            if "sort" in row_str or "order by" in row_str:
                analysis["sort_operations"] += 1
        
        return analysis
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Generate optimization recommendations based on analysis
        
        Args:
            analysis: Query analysis results
            
        Returns:
            List of optimization recommendations
        """
        recommendations = []
        
        if analysis["has_table_scan"] and not analysis["uses_indexes"]:
            recommendations.append("Add indexes on frequently queried columns")
        
        if analysis["join_operations"] > 2:
            recommendations.append("Consider optimizing complex joins or breaking into smaller queries")
        
        if analysis["sort_operations"] > 1:
            recommendations.append("Consider adding indexes on ORDER BY columns")
        
        if not recommendations:
            recommendations.append("Query appears to be well-optimized")
        
        return recommendations
    
    async def get_database_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics
        
        Returns:
            Database statistics and performance metrics
        """
        try:
            with self.engine.connect() as connection:
                stats = {
                    "database_type": self.engine.dialect.name,
                    "tables": {},
                    "indexes": {},
                    "performance_metrics": {}
                }
                
                # Get table statistics
                if self.engine.dialect.name == 'sqlite':
                    # SQLite table stats
                    result = connection.execute(text("""
                        SELECT name, sql FROM sqlite_master 
                        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                    """))
                    
                    for table_name, sql in result.fetchall():
                        # Get row count
                        count_result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        row_count = count_result.scalar()
                        
                        stats["tables"][table_name] = {
                            "row_count": row_count,
                            "creation_sql": sql
                        }
                
                # Get index statistics
                result = connection.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
                """))
                
                for index_name, in result.fetchall():
                    stats["indexes"][index_name] = {
                        "exists": True
                    }
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting database statistics: {str(e)}")
            return {"error": str(e)}
    
    async def optimize_database(self) -> Dict[str, Any]:
        """
        Perform comprehensive database optimization
        
        Returns:
            Optimization results
        """
        results = {
            "indexes_created": 0,
            "vacuum_performed": False,
            "analyze_performed": False,
            "errors": []
        }
        
        try:
            # Create missing indexes
            index_results = await self.create_indexes()
            results["indexes_created"] = len(index_results["created"])
            results["errors"].extend(index_results["errors"])
            
            # Perform database maintenance
            with self.engine.connect() as connection:
                if self.engine.dialect.name == 'sqlite':
                    # SQLite optimization
                    connection.execute(text("VACUUM"))
                    connection.execute(text("ANALYZE"))
                    results["vacuum_performed"] = True
                    results["analyze_performed"] = True
                
                elif self.engine.dialect.name == 'postgresql':
                    # PostgreSQL optimization
                    connection.execute(text("VACUUM ANALYZE"))
                    results["vacuum_performed"] = True
                    results["analyze_performed"] = True
                
                connection.commit()
            
            logger.info("Database optimization completed successfully")
            
        except Exception as e:
            error_msg = f"Database optimization failed: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)
        
        return results
    
    async def check_index_usage(self) -> Dict[str, Any]:
        """
        Check which indexes are being used effectively
        
        Returns:
            Index usage statistics
        """
        try:
            with self.engine.connect() as connection:
                if self.engine.dialect.name == 'sqlite':
                    # SQLite doesn't have built-in index usage stats
                    # We'll return the list of existing indexes
                    result = connection.execute(text("""
                        SELECT name, tbl_name FROM sqlite_master 
                        WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
                    """))
                    
                    indexes = {}
                    for index_name, table_name in result.fetchall():
                        indexes[index_name] = {
                            "table": table_name,
                            "usage_stats": "Not available in SQLite"
                        }
                    
                    return {
                        "database_type": "sqlite",
                        "indexes": indexes,
                        "note": "SQLite does not provide index usage statistics"
                    }
                
                else:
                    # For PostgreSQL/MySQL, we could implement more detailed stats
                    return {
                        "database_type": self.engine.dialect.name,
                        "note": "Index usage statistics not implemented for this database type"
                    }
                    
        except Exception as e:
            logger.error(f"Error checking index usage: {str(e)}")
            return {"error": str(e)}


# Global database optimizer instance
db_optimizer = DatabaseOptimizer()


# Convenience functions for common optimization tasks
async def optimize_database_performance() -> Dict[str, Any]:
    """Perform comprehensive database optimization"""
    return await db_optimizer.optimize_database()


async def create_performance_indexes() -> Dict[str, Any]:
    """Create all performance-critical indexes"""
    return await db_optimizer.create_indexes()


async def analyze_slow_query(query: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Analyze a potentially slow query for optimization opportunities"""
    return await db_optimizer.analyze_query_performance(query, params)


async def get_db_performance_stats() -> Dict[str, Any]:
    """Get comprehensive database performance statistics"""
    return await db_optimizer.get_database_statistics()