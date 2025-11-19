"""Analytics service for tracking usage and engagement."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from src.models.analytics_event import AnalyticsEvent
from src.models.constants import AnalyticsEventType
from src.models.prompt import Prompt
from src.models.prompt_copy_event import PromptCopyEvent


class AnalyticsService:
    """Service for handling analytics operations."""

    @staticmethod
    def track_event(
        db: Session,
        event_type: AnalyticsEventType,
        prompt_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[AnalyticsEvent]:
        """
        Track an analytics event (best-effort).

        This method is designed to never raise exceptions, as analytics failures
        should not impact core functionality. Errors are logged but not propagated.

        Args:
            db: Database session
            event_type: Type of event (VIEW, COPY, SEARCH)
            prompt_id: Optional prompt ID related to the event
            user_id: Optional user ID who triggered the event
            metadata: Optional JSON metadata for additional event data

        Returns:
            AnalyticsEvent: Created analytics event, or None if tracking failed
        """
        try:
            event = AnalyticsEvent(
                event_type=event_type,
                prompt_id=prompt_id,
                user_id=user_id,
                event_metadata=metadata,
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            return event
        except Exception as e:
            # Log error but don't fail the request
            logger.warning(
                f"Failed to track analytics event (type={event_type}, prompt_id={prompt_id}): {e}",
                exc_info=True,
            )
            # Rollback the failed transaction
            try:
                db.rollback()
            except Exception:
                pass  # Ignore rollback errors
            return None

    @staticmethod
    def get_prompt_analytics(
        db: Session,
        prompt_id: UUID,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific prompt.

        Args:
            db: Database session
            prompt_id: Prompt ID to get analytics for
            days: Number of days to look back (default: 30)

        Returns:
            dict: Analytics data including view count, copy count, and time series
        """
        # Verify prompt exists
        prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if not prompt:
            raise ValueError(f"Prompt {prompt_id} not found")

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Get view count from analytics_events
        view_count = (
            db.query(func.count(AnalyticsEvent.id))
            .filter(
                and_(
                    AnalyticsEvent.prompt_id == prompt_id,
                    AnalyticsEvent.event_type == AnalyticsEventType.VIEW,
                    AnalyticsEvent.created_at >= cutoff_date,
                )
            )
            .scalar()
            or 0
        )

        # Get copy count from prompt_copy_events (existing table)
        copy_count = (
            db.query(func.count(PromptCopyEvent.id))
            .filter(
                and_(
                    PromptCopyEvent.prompt_id == prompt_id,
                    PromptCopyEvent.copied_at >= cutoff_date,
                )
            )
            .scalar()
            or 0
        )

        # Also track copies in analytics_events for consistency
        copy_events_count = (
            db.query(func.count(AnalyticsEvent.id))
            .filter(
                and_(
                    AnalyticsEvent.prompt_id == prompt_id,
                    AnalyticsEvent.event_type == AnalyticsEventType.COPY,
                    AnalyticsEvent.created_at >= cutoff_date,
                )
            )
            .scalar()
            or 0
        )

        # Use the higher count (either from copy_events or analytics_events)
        total_copy_count = max(copy_count, copy_events_count)

        # Get time series data (daily counts)
        daily_views = (
            db.query(
                func.date(AnalyticsEvent.created_at).label("date"),
                func.count(AnalyticsEvent.id).label("count"),
            )
            .filter(
                and_(
                    AnalyticsEvent.prompt_id == prompt_id,
                    AnalyticsEvent.event_type == AnalyticsEventType.VIEW,
                    AnalyticsEvent.created_at >= cutoff_date,
                )
            )
            .group_by(func.date(AnalyticsEvent.created_at))
            .order_by(func.date(AnalyticsEvent.created_at))
            .all()
        )

        daily_copies = (
            db.query(
                func.date(PromptCopyEvent.copied_at).label("date"),
                func.count(PromptCopyEvent.id).label("count"),
            )
            .filter(
                and_(
                    PromptCopyEvent.prompt_id == prompt_id,
                    PromptCopyEvent.copied_at >= cutoff_date,
                )
            )
            .group_by(func.date(PromptCopyEvent.copied_at))
            .order_by(func.date(PromptCopyEvent.copied_at))
            .all()
        )

        # Format time series data
        views_series = {str(row.date): row.count for row in daily_views}
        copies_series = {str(row.date): row.count for row in daily_copies}

        return {
            "prompt_id": str(prompt_id),
            "prompt_title": prompt.title,
            "total_views": view_count,
            "total_copies": total_copy_count,
            "views_series": views_series,
            "copies_series": copies_series,
            "period_days": days,
        }

    @staticmethod
    def get_overview_analytics(
        db: Session,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get overall analytics for the platform.

        Args:
            db: Database session
            days: Number of days to look back (default: 30)

        Returns:
            dict: Overall analytics including total events, top prompts, etc.
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Total events by type
        event_counts = (
            db.query(
                AnalyticsEvent.event_type,
                func.count(AnalyticsEvent.id).label("count"),
            )
            .filter(AnalyticsEvent.created_at >= cutoff_date)
            .group_by(AnalyticsEvent.event_type)
            .all()
        )

        event_counts_dict = {event_type.value: count for event_type, count in event_counts}

        # Total searches
        search_count = event_counts_dict.get(AnalyticsEventType.SEARCH.value, 0)

        # Total views
        view_count = event_counts_dict.get(AnalyticsEventType.VIEW.value, 0)

        # Total copies (from both tables)
        copy_events_count = event_counts_dict.get(AnalyticsEventType.COPY.value, 0)
        copy_events_from_table = (
            db.query(func.count(PromptCopyEvent.id))
            .filter(PromptCopyEvent.copied_at >= cutoff_date)
            .scalar()
            or 0
        )
        total_copies = max(copy_events_count, copy_events_from_table)

        # Top viewed prompts
        top_viewed = (
            db.query(
                Prompt.id,
                Prompt.title,
                func.count(AnalyticsEvent.id).label("view_count"),
            )
            .join(AnalyticsEvent, AnalyticsEvent.prompt_id == Prompt.id)
            .filter(
                and_(
                    AnalyticsEvent.event_type == AnalyticsEventType.VIEW,
                    AnalyticsEvent.created_at >= cutoff_date,
                )
            )
            .group_by(Prompt.id, Prompt.title)
            .order_by(func.count(AnalyticsEvent.id).desc())
            .limit(10)
            .all()
        )

        # Top copied prompts
        top_copied = (
            db.query(
                Prompt.id,
                Prompt.title,
                func.count(PromptCopyEvent.id).label("copy_count"),
            )
            .join(PromptCopyEvent, PromptCopyEvent.prompt_id == Prompt.id)
            .filter(PromptCopyEvent.copied_at >= cutoff_date)
            .group_by(Prompt.id, Prompt.title)
            .order_by(func.count(PromptCopyEvent.id).desc())
            .limit(10)
            .all()
        )

        # Daily activity (aggregated)
        daily_activity = (
            db.query(
                func.date(AnalyticsEvent.created_at).label("date"),
                AnalyticsEvent.event_type,
                func.count(AnalyticsEvent.id).label("count"),
            )
            .filter(AnalyticsEvent.created_at >= cutoff_date)
            .group_by(func.date(AnalyticsEvent.created_at), AnalyticsEvent.event_type)
            .order_by(func.date(AnalyticsEvent.created_at))
            .all()
        )

        # Format daily activity
        activity_by_date: Dict[str, Dict[str, int]] = {}
        for row in daily_activity:
            date_str = str(row.date)
            if date_str not in activity_by_date:
                activity_by_date[date_str] = {}
            activity_by_date[date_str][row.event_type.value] = row.count

        return {
            "period_days": days,
            "total_views": view_count,
            "total_copies": total_copies,
            "total_searches": search_count,
            "top_viewed_prompts": [
                {"prompt_id": str(prompt_id), "title": title, "view_count": count}
                for prompt_id, title, count in top_viewed
            ],
            "top_copied_prompts": [
                {"prompt_id": str(prompt_id), "title": title, "copy_count": count}
                for prompt_id, title, count in top_copied
            ],
            "daily_activity": activity_by_date,
        }

