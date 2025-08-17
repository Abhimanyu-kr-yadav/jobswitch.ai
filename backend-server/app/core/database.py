"""
Database Configuration and Setup
"""
import os
import logging
from typing import Generator
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./jobswitch.db")

# Create SQLAlchemy engine
if DATABASE_URL.startswith("sqlite"):
    # SQLite configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=os.getenv("SQL_DEBUG", "false").lower() == "true"
    )
else:
    # PostgreSQL/MySQL configuration
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=os.getenv("SQL_DEBUG", "false").lower() == "true"
    )

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_database() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all database tables
    """
    try:
        # Import all models to ensure they're registered with the shared Base
        from app.models.base import Base
        import app.models.user
        import app.models.job
        import app.models.agent
        import app.models.analytics
        import app.models.resume
        import app.models.networking
        import app.models.career_strategy
        
        # Create all tables using the shared Base
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise


def drop_tables():
    """
    Drop all database tables (use with caution)
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
        
    except Exception as e:
        logger.error(f"Error dropping database tables: {str(e)}")
        raise


class DatabaseManager:
    """
    Database management utilities
    """
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def get_session(self) -> Session:
        """
        Get a new database session
        
        Returns:
            Database session
        """
        return self.SessionLocal()
    
    def execute_raw_sql(self, sql: str, params: dict = None) -> any:
        """
        Execute raw SQL query
        
        Args:
            sql: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        with self.engine.connect() as connection:
            result = connection.execute(sql, params or {})
            return result.fetchall()
    
    def check_connection(self) -> bool:
        """
        Check if database connection is working
        
        Returns:
            True if connection is working, False otherwise
        """
        try:
            from sqlalchemy import text
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {str(e)}")
            return False
    
    def get_table_info(self) -> dict:
        """
        Get information about database tables
        
        Returns:
            Dictionary with table information
        """
        try:
            metadata = MetaData()
            metadata.reflect(bind=self.engine)
            
            table_info = {}
            for table_name, table in metadata.tables.items():
                table_info[table_name] = {
                    "columns": [col.name for col in table.columns],
                    "primary_keys": [col.name for col in table.primary_key.columns],
                    "foreign_keys": [
                        {
                            "column": fk.parent.name,
                            "references": f"{fk.column.table.name}.{fk.column.name}"
                        }
                        for fk in table.foreign_keys
                    ]
                }
            
            return table_info
            
        except Exception as e:
            logger.error(f"Error getting table info: {str(e)}")
            return {}


# Global database manager instance
db_manager = DatabaseManager()