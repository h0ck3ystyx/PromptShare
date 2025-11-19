"""Tests for analytics service error handling."""

import pytest
from unittest.mock import patch, MagicMock

from src.constants import AnalyticsEventType
from src.services.analytics_service import AnalyticsService


class TestAnalyticsServiceFailures:
    """Test cases for analytics service error handling."""

    def test_track_event_handles_database_error(self, db_session):
        """Test that track_event handles database errors gracefully."""
        # Simulate a database error by making commit fail
        with patch.object(db_session, 'commit', side_effect=Exception("Database error")):
            result = AnalyticsService.track_event(
                db=db_session,
                event_type=AnalyticsEventType.VIEW,
                prompt_id=None,
                user_id=None,
            )
            
            # Should return None instead of raising
            assert result is None

    def test_track_event_handles_rollback_error(self, db_session):
        """Test that track_event handles rollback errors gracefully."""
        # Simulate commit failure followed by rollback failure
        with patch.object(db_session, 'commit', side_effect=Exception("Commit error")), \
             patch.object(db_session, 'rollback', side_effect=Exception("Rollback error")):
            result = AnalyticsService.track_event(
                db=db_session,
                event_type=AnalyticsEventType.SEARCH,
                prompt_id=None,
                user_id=None,
            )
            
            # Should return None even if rollback fails
            assert result is None

    def test_track_event_handles_missing_table(self, db_session):
        """Test that track_event handles missing table gracefully."""
        # Simulate missing table by making add() fail
        with patch.object(db_session, 'add', side_effect=Exception("Table does not exist")):
            result = AnalyticsService.track_event(
                db=db_session,
                event_type=AnalyticsEventType.COPY,
                prompt_id=None,
                user_id=None,
            )
            
            # Should return None instead of raising
            assert result is None

