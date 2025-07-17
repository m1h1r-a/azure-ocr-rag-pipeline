import logging
import os
import time
from typing import Optional, Tuple

import pymssql


class DatabaseConnection:
    """Manages database connections with retry logic"""

    def __init__(self):
        """Initialize connection parameters - same as original"""
        self.server = os.environ.get("SQL_SERVER_NAME")
        self.database = os.environ.get("SQL_DATABASE_NAME")
        self.username = os.environ.get("SQL_USERNAME")
        self.password = os.environ.get("SQL_PASSWORD")
        self.logger = logging.getLogger(__name__)

    def connect_with_retry(
        self, max_retries: int = 5, retry_delay: int = 5
    ) -> Tuple[Optional[object], Optional[object]]:
        """
        Connect to database with retry logic - exact same logic as original

        Args:
            max_retries: Maximum number of connection attempts
            retry_delay: Delay between retries in seconds

        Returns:
            Tuple of (connection, cursor) or (None, None) if failed
        """
        for attempt in range(max_retries):
            try:
                self.logger.info(
                    f"🔄 Database connection attempt {attempt + 1}/{max_retries}"
                )

                # Connect with same parameters as original
                conn = pymssql.connect(
                    server=self.server,
                    user=self.username,
                    password=self.password,
                    database=self.database,
                    port=1433,
                    timeout=60,  # Connection timeout
                    login_timeout=60,  # Login timeout
                    as_dict=True,
                )

                # Test the connection - same as original
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as test_value")
                result = cursor.fetchone()

                if result and result["test_value"] == 1:
                    self.logger.info(
                        f"✅ SQL Database connection successful on attempt {attempt + 1}!"
                    )
                    return conn, cursor
                else:
                    raise Exception("Connection test failed")

            except Exception as e:
                self.logger.warning(
                    f"⚠️ Connection attempt {attempt + 1} failed: {str(e)}"
                )
                if attempt < max_retries - 1:
                    self.logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    self.logger.error(
                        f"❌ All {max_retries} connection attempts failed"
                    )
                    raise e

        return None, None
