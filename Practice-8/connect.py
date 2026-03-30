import psycopg2
from psycopg2 import pool
from config import DB_CONFIG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def connect(self):
        """Create a connection pool if it doesn't exist"""
        if self._pool is None:
            try:
                self._pool = psycopg2.pool.SimpleConnectionPool(
                    1, 10,
                    host=DB_CONFIG['host'],
                    port=DB_CONFIG['port'],
                    database=DB_CONFIG['database'],
                    user=DB_CONFIG['user'],
                    password=DB_CONFIG['password']
                )
                logger.info("Database connection pool created successfully")
            except Exception as e:
                logger.error(f"Failed to create connection pool: {e}")
                raise
        return self._pool.getconn()
    
    def disconnect(self):
        """Close all connections in the pool"""
        if self._pool:
            self._pool.closeall()
            logger.info("All database connections closed")
    
    def get_connection(self):
        """Get a connection from the pool"""
        return self.connect()
    
    def return_connection(self, conn):
        """Return a connection to the pool"""
        if self._pool:
            self._pool.putconn(conn)

def get_db_connection():
    """Convenience function to get a database connection"""
    db = DatabaseConnection()
    return db.get_connection()

def close_db_connection(conn):
    """Convenience function to return a database connection to the pool"""
    db = DatabaseConnection()
    db.return_connection(conn)