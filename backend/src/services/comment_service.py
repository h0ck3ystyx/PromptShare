"""Comment service for business logic."""

from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.constants import UserRole
from src.models.comment import Comment
from src.models.prompt import Prompt
from src.models.user import User
from src.schemas.comment import CommentCreate, CommentUpdate


class CommentService:
    """Service for handling comment operations."""

    @staticmethod
    def create_comment(
        db: Session,
        prompt_id: UUID,
        comment_data: CommentCreate,
        user_id: UUID,
    ) -> Comment:
        """
        Create a new comment.

        Args:
            db: Database session
            prompt_id: Prompt UUID
            comment_data: Comment creation data
            user_id: ID of the user creating the comment

        Returns:
            Comment: Created comment object

        Raises:
            HTTPException: If prompt not found or parent comment not found
        """
        # Verify prompt exists
        prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt not found",
            )

        # Verify parent comment exists if provided
        if comment_data.parent_comment_id:
            parent = db.query(Comment).filter(Comment.id == comment_data.parent_comment_id).first()
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent comment not found",
                )
            # Ensure parent comment belongs to the same prompt
            if parent.prompt_id != prompt_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent comment does not belong to this prompt",
                )

        from sqlalchemy.orm import joinedload
        
        comment = Comment(
            prompt_id=prompt_id,
            user_id=user_id,
            content=comment_data.content,
            parent_comment_id=comment_data.parent_comment_id,
        )

        db.add(comment)
        db.commit()
        # Reload with user relationship
        comment_with_user = (
            db.query(Comment)
            .options(joinedload(Comment.user))
            .filter(Comment.id == comment.id)
            .first()
        )
        return comment_with_user or comment

    @staticmethod
    def get_comment_by_id(db: Session, comment_id: UUID) -> Optional[Comment]:
        """
        Get comment by ID.

        Args:
            db: Database session
            comment_id: Comment UUID

        Returns:
            Comment: Comment object if found, None otherwise
        """
        return db.query(Comment).filter(Comment.id == comment_id).first()

    @staticmethod
    def get_comments_for_prompt(
        db: Session,
        prompt_id: UUID,
        include_deleted: bool = False,
    ) -> list[Comment]:
        """
        Get all comments for a prompt (as a flat list).

        Args:
            db: Database session
            prompt_id: Prompt UUID
            include_deleted: Whether to include deleted comments

        Returns:
            list: List of comments
        """
        from sqlalchemy.orm import joinedload
        query = (
            db.query(Comment)
            .options(joinedload(Comment.user))
            .filter(Comment.prompt_id == prompt_id)
        )

        if not include_deleted:
            query = query.filter(Comment.is_deleted == False)

        return query.order_by(Comment.created_at.asc()).all()

    @staticmethod
    def get_comment_tree_for_prompt(
        db: Session,
        prompt_id: UUID,
        include_deleted: bool = False,
    ) -> list[Comment]:
        """
        Get comments for a prompt organized as a tree (top-level comments with replies).

        Args:
            db: Database session
            prompt_id: Prompt UUID
            include_deleted: Whether to include deleted comments

        Returns:
            list: List of top-level comments (with replies populated)
        """
        # Get all comments for the prompt with user relationships loaded
        from sqlalchemy.orm import joinedload
        query = (
            db.query(Comment)
            .options(joinedload(Comment.user))
            .filter(Comment.prompt_id == prompt_id)
        )

        if not include_deleted:
            query = query.filter(Comment.is_deleted == False)

        all_comments = query.order_by(Comment.created_at.asc()).all()

        # Build a map of comments by ID for efficient lookup
        comment_map = {c.id: c for c in all_comments}

        # Initialize replies list for all comments
        for comment in all_comments:
            comment.replies = []

        # Build reply relationships
        for comment in all_comments:
            if comment.parent_comment_id:
                parent = comment_map.get(comment.parent_comment_id)
                if parent:
                    parent.replies.append(comment)

        # Filter to only top-level comments
        top_level = [c for c in all_comments if c.parent_comment_id is None]

        # Recursively filter deleted replies if needed
        if not include_deleted:
            CommentService._filter_deleted_replies_recursive(top_level)

        return top_level

    @staticmethod
    def _load_reply_users(db: Session, comment: Comment) -> None:
        """
        Recursively load user relationships for comment replies.

        Args:
            db: Database session
            comment: Comment to load users for
        """
        from sqlalchemy.orm import joinedload
        if hasattr(comment, 'replies') and comment.replies:
            reply_ids = [r.id for r in comment.replies]
            if reply_ids:
                replies_with_users = (
                    db.query(Comment)
                    .options(joinedload(Comment.user))
                    .filter(Comment.id.in_(reply_ids))
                    .all()
                )
                user_map = {r.id: r.user for r in replies_with_users}
                for reply in comment.replies:
                    if reply.id in user_map:
                        reply.user = user_map[reply.id]
                    CommentService._load_reply_users(db, reply)

    @staticmethod
    def _filter_deleted_replies_recursive(comments: list[Comment]) -> None:
        """
        Recursively filter out deleted replies from comments.

        Args:
            comments: List of comments to filter
        """
        for comment in comments:
            if hasattr(comment, 'replies') and comment.replies:
                # Filter deleted replies
                comment.replies = [r for r in comment.replies if not r.is_deleted]
                # Recursively filter nested replies
                CommentService._filter_deleted_replies_recursive(comment.replies)

    @staticmethod
    def build_comment_tree(
        comments: list[Comment],
        include_deleted: bool = False,
    ) -> list:
        """
        Build a nested tree structure from comment list with replies.

        Args:
            comments: List of top-level comments with replies populated
            include_deleted: Whether to include deleted comments in output

        Returns:
            list: List of CommentTreeResponse objects
        """
        from src.schemas.comment import CommentTreeResponse

        result = []
        for comment in comments:
            if not include_deleted and comment.is_deleted:
                continue

            # Build reply tree recursively
            replies = []
            if hasattr(comment, 'replies') and comment.replies:
                # Filter deleted replies if needed
                reply_list = comment.replies
                if not include_deleted:
                    reply_list = [r for r in reply_list if not r.is_deleted]
                replies = CommentService.build_comment_tree(reply_list, include_deleted)

            # Build response
            comment_dict = {
                "id": comment.id,
                "prompt_id": comment.prompt_id,
                "user_id": comment.user_id,
                "content": comment.content,
                "parent_comment_id": comment.parent_comment_id,
                "created_at": comment.created_at,
                "updated_at": comment.updated_at,
                "is_deleted": comment.is_deleted,
                "author_username": comment.user.username,
                "author_full_name": comment.user.full_name,
                "reply_count": len(replies),
                "replies": replies,
            }

            result.append(CommentTreeResponse(**comment_dict))

        return result

    @staticmethod
    def update_comment(
        db: Session,
        comment_id: UUID,
        comment_data: CommentUpdate,
        user: User,
    ) -> Comment:
        """
        Update an existing comment.

        Args:
            db: Database session
            comment_id: Comment UUID
            comment_data: Comment update data
            user: Current user (must be author or admin/moderator)

        Returns:
            Comment: Updated comment object

        Raises:
            HTTPException: If comment not found or user lacks permission
        """
        comment = db.query(Comment).filter(Comment.id == comment_id).first()

        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found",
            )

        # Check permissions: author or admin/moderator can update
        if comment.user_id != user.id and user.role not in (UserRole.ADMIN, UserRole.MODERATOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this comment",
            )

        from sqlalchemy.orm import joinedload
        
        comment.content = comment_data.content
        db.commit()
        # Reload with user relationship
        comment_with_user = (
            db.query(Comment)
            .options(joinedload(Comment.user))
            .filter(Comment.id == comment.id)
            .first()
        )
        return comment_with_user or comment

    @staticmethod
    def delete_comment(
        db: Session,
        comment_id: UUID,
        user: User,
        hard_delete: bool = False,
    ) -> None:
        """
        Delete a comment (soft delete by default, hard delete for admins).

        Args:
            db: Database session
            comment_id: Comment UUID
            user: Current user (must be author or admin/moderator)
            hard_delete: If True, permanently delete (admin only)

        Raises:
            HTTPException: If comment not found or user lacks permission
        """
        comment = db.query(Comment).filter(Comment.id == comment_id).first()

        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found",
            )

        # Check permissions
        if comment.user_id != user.id and user.role not in (UserRole.ADMIN, UserRole.MODERATOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this comment",
            )

        # Hard delete only for admins
        if hard_delete and user.role == UserRole.ADMIN:
            db.delete(comment)
        else:
            # Soft delete
            comment.is_deleted = True
            comment.content = "[deleted]"

        db.commit()

    @staticmethod
    def get_comment_reply_count(db: Session, comment_id: UUID) -> int:
        """
        Get the number of replies for a comment.

        Args:
            db: Database session
            comment_id: Comment UUID

        Returns:
            int: Number of replies
        """
        return (
            db.query(func.count(Comment.id))
            .filter(Comment.parent_comment_id == comment_id, Comment.is_deleted == False)
            .scalar()
            or 0
        )

