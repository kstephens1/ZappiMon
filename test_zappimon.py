#!/usr/bin/env python3
"""
Test suite for ZappiMon
Tests grid power monitoring, database operations, and notification functionality
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import os
import tempfile
import shutil

# Import the modules to test
from ZappiMon import check_excessive_export, sendNotif
from database import ZappiDatabase


class TestZappiMon:
    """Test class for ZappiMon functionality"""

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables"""
        with patch.dict(
            os.environ,
            {
                "MYENERGI_USERNAME": "test_user",
                "MYENERGI_PASSWORD": "test_pass",
                "PUSHOVER_APP_TOKEN": "test_token",
                "PUSHOVER_USER_KEY": "test_key",
            },
        ):
            yield

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_zappimon.db")
        db = ZappiDatabase(db_path)
        yield db
        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_zappi_response(self):
        """Mock Zappi API response"""
        return {
            "zappi": [
                {
                    "deviceClass": "ZAPPI",
                    "sno": 13000699,
                    "dat": "25-08-2025",
                    "tim": "18:41:30",
                    "grd": 0,  # Will be overridden in tests
                    "ectp1": 0,
                    "ectp2": 65,
                    "ectp3": 5,
                    "ectt1": "Internal Load",
                    "ectt2": "Grid",
                    "ectt3": "None",
                    "sta": 1,
                    "pst": "A",
                }
            ]
        }

    def test_check_excessive_export_initial_state(self):
        """Test initial state of excessive export tracking"""
        # Reset global variables
        import ZappiMon

        ZappiMon.excessive_export_start = None
        ZappiMon.notification_sent = False

        current_time = datetime.now()
        result = check_excessive_export(-1200, current_time)

        # Should not send notification on first excessive export
        assert result == False
        assert ZappiMon.excessive_export_start == current_time
        assert ZappiMon.notification_sent == False

    def test_check_excessive_export_15_minutes(self):
        """Test excessive export after 15 minutes"""
        # Reset global variables
        import ZappiMon

        ZappiMon.excessive_export_start = None
        ZappiMon.notification_sent = False

        start_time = datetime.now()
        current_time = start_time + timedelta(minutes=15)

        # First call - start tracking
        check_excessive_export(-1200, start_time)

        # Second call - after 15 minutes
        result = check_excessive_export(-1200, current_time)

        # Should send notification after 15 minutes
        assert result == True
        assert ZappiMon.notification_sent == True

    def test_check_excessive_export_reset_on_import(self):
        """Test that export tracking resets when importing"""
        # Reset global variables
        import ZappiMon

        ZappiMon.excessive_export_start = None
        ZappiMon.notification_sent = False

        start_time = datetime.now()

        # Start excessive export
        check_excessive_export(-1200, start_time)
        assert ZappiMon.excessive_export_start is not None

        # Switch to import
        result = check_excessive_export(500, start_time + timedelta(minutes=5))

        # Should reset tracking
        assert result == False
        assert ZappiMon.excessive_export_start is None
        assert ZappiMon.notification_sent == False

    def test_check_excessive_export_below_threshold(self):
        """Test that export below 1000W doesn't trigger tracking"""
        # Reset global variables
        import ZappiMon

        ZappiMon.excessive_export_start = None
        ZappiMon.notification_sent = False

        current_time = datetime.now()
        result = check_excessive_export(-500, current_time)

        # Should not track exports below 1000W
        assert result == False
        assert ZappiMon.excessive_export_start is None

    def test_check_excessive_export_one_notification_only(self):
        """Test that only one notification is sent per sustained period"""
        # Reset global variables
        import ZappiMon

        ZappiMon.excessive_export_start = None
        ZappiMon.notification_sent = False

        start_time = datetime.now()
        current_time_15min = start_time + timedelta(minutes=15)
        current_time_20min = start_time + timedelta(minutes=20)

        # Start tracking
        check_excessive_export(-1200, start_time)

        # First notification at 15 minutes
        result1 = check_excessive_export(-1200, current_time_15min)
        assert result1 == True

        # Second check at 20 minutes - should not send another notification
        result2 = check_excessive_export(-1200, current_time_20min)
        assert result2 == False

    @patch("ZappiMon.requests.post")
    def test_send_notification_success(self, mock_post, mock_env_vars):
        """Test successful notification sending"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 1}
        mock_post.return_value = mock_response

        result = sendNotif("Test message", "Test title", 1)

        assert result == True
        mock_post.assert_called_once()

        # Check the call arguments
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.pushover.net/1/messages.json"

        # Check data parameters
        data = call_args[1]["data"]
        assert data["message"] == "Test message"
        assert data["title"] == "Test title"
        assert data["priority"] == 1

    @patch("ZappiMon.requests.post")
    def test_send_notification_failure(self, mock_post, mock_env_vars):
        """Test notification sending failure"""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"status": 0, "errors": ["Invalid token"]}
        mock_post.return_value = mock_response

        result = sendNotif("Test message")

        assert result == False

    def test_database_store_and_retrieve(self, temp_db):
        """Test database storage and retrieval"""
        current_time = datetime.now()

        # Store a reading
        temp_db.store_grid_reading(-1200, current_time)

        # Retrieve the latest reading
        latest = temp_db.get_latest_reading()

        assert latest is not None
        assert latest[0] == -1200  # grd_value
        # SQLite returns timestamp as string, so compare as strings
        assert str(latest[1]) == str(current_time)  # timestamp

    def test_database_statistics(self, temp_db):
        """Test database statistics calculation"""
        base_time = datetime.now()

        # Store multiple readings
        readings = [
            (-1200, base_time - timedelta(hours=1)),  # Export
            (500, base_time - timedelta(minutes=30)),  # Import
            (-800, base_time - timedelta(minutes=15)),  # Export
            (300, base_time),  # Import
        ]

        for grd_value, timestamp in readings:
            temp_db.store_grid_reading(grd_value, timestamp)

        # Get statistics for last 2 hours
        stats = temp_db.get_statistics(2)

        assert stats is not None
        total_readings, avg_grd, min_grd, max_grd, import_count, export_count = stats

        assert total_readings == 4
        assert avg_grd == -300.0  # (-1200 + 500 - 800 + 300) / 4
        assert min_grd == -1200
        assert max_grd == 500
        assert import_count == 2
        assert export_count == 2


class TestZappiMonIntegration:
    """Integration tests for complete ZappiMon workflow"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_zappimon.db")
        db = ZappiDatabase(db_path)
        yield db
        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_requests(self):
        """Mock requests for API calls"""
        with patch("ZappiMon.requests.get") as mock_get, patch(
            "ZappiMon.requests.post"
        ) as mock_post:

            # Mock successful MyEnergi response
            mock_zappi_response = Mock()
            mock_zappi_response.status_code = 200
            mock_zappi_response.json.return_value = {
                "zappi": [{"grd": 0, "sta": 1, "pst": "A"}]
            }
            mock_get.return_value = mock_zappi_response

            # Mock successful Pushover response
            mock_pushover_response = Mock()
            mock_pushover_response.status_code = 200
            mock_pushover_response.json.return_value = {"status": 1}
            mock_post.return_value = mock_pushover_response

            yield mock_get, mock_post

    @patch.dict(
        os.environ,
        {
            "MYENERGI_USERNAME": "test_user",
            "MYENERGI_PASSWORD": "test_pass",
            "PUSHOVER_APP_TOKEN": "test_token",
            "PUSHOVER_USER_KEY": "test_key",
        },
    )
    def test_1200w_export_scenario(self, mock_requests, temp_db):
        """Test complete workflow with 1200W export"""
        mock_get, mock_post = mock_requests

        # Mock response with 1200W export
        mock_get.return_value.json.return_value = {
            "zappi": [{"grd": -1200, "sta": 1, "pst": "A"}]
        }

        # Import and run main function
        from ZappiMon import main

        # Mock the database to use our temp database
        with patch("ZappiMon.ZappiDatabase") as mock_db_class:
            mock_db_class.return_value = temp_db
            main()

        # Verify API was called
        mock_get.assert_called_once()

        # Verify database storage
        latest = temp_db.get_latest_reading()
        assert latest is not None
        assert latest[0] == -1200

    @patch.dict(
        os.environ,
        {
            "MYENERGI_USERNAME": "test_user",
            "MYENERGI_PASSWORD": "test_pass",
            "PUSHOVER_APP_TOKEN": "test_token",
            "PUSHOVER_USER_KEY": "test_key",
        },
    )
    def test_1200w_import_scenario(self, mock_requests, temp_db):
        """Test complete workflow with 1200W import"""
        mock_get, mock_post = mock_requests

        # Mock response with 1200W import
        mock_get.return_value.json.return_value = {
            "zappi": [{"grd": 1200, "sta": 1, "pst": "A"}]
        }

        # Import and run main function
        from ZappiMon import main

        # Mock the database to use our temp database
        with patch("ZappiMon.ZappiDatabase") as mock_db_class:
            mock_db_class.return_value = temp_db
            main()

        # Verify API was called
        mock_get.assert_called_once()

        # Verify database storage
        latest = temp_db.get_latest_reading()
        assert latest is not None
        assert latest[0] == 1200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
