#!/usr/bin/env python3
"""
Database module for ZappiMon
Handles SQLite operations for storing grid values and timestamps
"""

import sqlite3
import os
from datetime import datetime


class ZappiDatabase:
    def __init__(self, db_path="zappimon.db"):
        """Initialize database connection and create tables if they don't exist"""
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Create the database and tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create grid_readings table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS grid_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    grd_value INTEGER NOT NULL,
                    timestamp DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create index on timestamp for faster queries
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON grid_readings(timestamp)
            """
            )

            conn.commit()

    def store_grid_reading(self, grd_value, timestamp=None):
        """Store a new grid reading in the database"""
        if timestamp is None:
            timestamp = datetime.now()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO grid_readings (grd_value, timestamp)
                VALUES (?, ?)
            """,
                (grd_value, timestamp),
            )
            conn.commit()

    def get_latest_reading(self):
        """Get the most recent grid reading"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT grd_value, timestamp 
                FROM grid_readings 
                ORDER BY timestamp DESC 
                LIMIT 1
            """
            )
            return cursor.fetchone()

    def get_readings_since(self, hours=24):
        """Get all readings from the last N hours"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT grd_value, timestamp 
                FROM grid_readings 
                WHERE timestamp >= datetime('now', '-{} hours')
                ORDER BY timestamp DESC
            """.format(
                    hours
                )
            )
            return cursor.fetchall()

    def get_statistics(self, hours=24):
        """Get statistics for the last N hours"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_readings,
                    AVG(grd_value) as avg_grd,
                    MIN(grd_value) as min_grd,
                    MAX(grd_value) as max_grd,
                    SUM(CASE WHEN grd_value > 0 THEN 1 ELSE 0 END) as import_count,
                    SUM(CASE WHEN grd_value < 0 THEN 1 ELSE 0 END) as export_count
                FROM grid_readings 
                WHERE timestamp >= datetime('now', '-{} hours')
            """.format(
                    hours
                )
            )
            return cursor.fetchone()
