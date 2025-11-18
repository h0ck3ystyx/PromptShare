"""Comment router endpoints."""

from typing import Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.constants import UserRole
from src.dependencies import CurrentUserDep, DatabaseDep, OptionalUserDep
from src.schemas.comment import CommentCreate, CommentResponse, CommentTreeResponse, CommentUpdate
from src.schemas.common import MessageResponse
from src.services.comment_service import CommentService

router = APIRouter(prefix="/prompts/{prompt_id}/comments", tags=["comments"])


@router.get(
    "",
    summary="Get comments for a prompt",
)
async def get_comments(
    prompt_id: UUID,
    db: DatabaseDep,
    tree: bool = Query(False, description="Return comments as a tree structure"),
    include_deleted: bool = Query(False, description="Include deleted comments (admin/moderator only)"),
    current_user: OptionalUserDep = None,
) -> Union[list[CommentResponse], list[CommentTreeResponse]]:
    """
    Get all comments for a prompt.

    Args:
        prompt_id: Prompt UUID
        db: Database session
        tree: Return comments as a tree structure (nested)
        include_deleted: Include deleted comments (admin/moderator only)
        current_user: Current authenticated user (optional)

    Returns:
        list: List of comments (flat or tree structure)
    """
    # Enforce permissions for include_deleted
    if include_deleted:
        if not current_user or current_user.role not in (UserRole.ADMIN, UserRole.MODERATOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins and moderators can view deleted comments",
            )

    if tree:
        comments = CommentService.get_comment_tree_for_prompt(
            db=db,
            prompt_id=prompt_id,
            include_deleted=include_deleted,
        )
        # User relationships are already loaded by get_comment_tree_for_prompt
        # Just ensure replies have users loaded
        for comment in comments:
            CommentService._load_reply_users(db, comment)
        # Build nested tree structure
        return CommentService.build_comment_tree(comments, include_deleted)
    else:
        comments = CommentService.get_comments_for_prompt(
            db=db,
            prompt_id=prompt_id,
            include_deleted=include_deleted,
        )
    # Eagerly load user relationships
    from sqlalchemy.orm import joinedload
    comment_ids = [c.id for c in comments]
    if comment_ids:
        comments_with_users = (
            db.query(Comment)
            .options(joinedload(Comment.user))
            .filter(Comment.id.in_(comment_ids))
            .all()
        )
        user_map = {c.id: c.user for c in comments_with_users}
        for comment in comments:
            if comment.id in user_map:
                comment.user = user_map[comment.id]

    # Convert to response format
    comment_responses = []
    for comment in comments:
        reply_count = CommentService.get_comment_reply_count(db, comment.id)
        comment_dict = CommentResponse.model_validate(comment).model_dump()
        comment_dict["author_username"] = comment.user.username
        comment_dict["author_full_name"] = comment.user.full_name
        comment_dict["reply_count"] = reply_count
        comment_responses.append(CommentResponse(**comment_dict))

    return comment_responses


@router.post(
    "",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new comment",
)
async def create_comment(
    prompt_id: UUID,
    comment_data: CommentCreate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> CommentResponse:
    """
    Create a new comment on a prompt.

    Args:
        prompt_id: Prompt UUID
        comment_data: Comment creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        CommentResponse: Created comment
    """
    comment = CommentService.create_comment(
        db=db,
        prompt_id=prompt_id,
        comment_data=comment_data,
        user_id=current_user.id,
    )

    # Build response (user relationship already loaded by service)
    reply_count = CommentService.get_comment_reply_count(db, comment.id)
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
        "reply_count": reply_count,
    }

    return CommentResponse(**comment_dict)


@router.put(
    "/{comment_id}",
    response_model=CommentResponse,
    summary="Update a comment",
)
async def update_comment(
    prompt_id: UUID,
    comment_id: UUID,
    comment_data: CommentUpdate,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> CommentResponse:
    """
    Update an existing comment (author or admin/moderator only).

    Args:
        prompt_id: Prompt UUID
        comment_id: Comment UUID
        comment_data: Comment update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        CommentResponse: Updated comment

    Raises:
        HTTPException: If comment not found or user lacks permission
    """
    # Verify comment belongs to prompt
    comment = CommentService.get_comment_by_id(db, comment_id)
    if not comment or comment.prompt_id != prompt_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    updated_comment = CommentService.update_comment(
        db=db,
        comment_id=comment_id,
        comment_data=comment_data,
        user=current_user,
    )

    # Build response (user relationship already loaded by service)
    reply_count = CommentService.get_comment_reply_count(db, updated_comment.id)
    comment_dict = {
        "id": updated_comment.id,
        "prompt_id": updated_comment.prompt_id,
        "user_id": updated_comment.user_id,
        "content": updated_comment.content,
        "parent_comment_id": updated_comment.parent_comment_id,
        "created_at": updated_comment.created_at,
        "updated_at": updated_comment.updated_at,
        "is_deleted": updated_comment.is_deleted,
        "author_username": updated_comment.user.username,
        "author_full_name": updated_comment.user.full_name,
        "reply_count": reply_count,
    }

    return CommentResponse(**comment_dict)


@router.delete(
    "/{comment_id}",
    response_model=MessageResponse,
    summary="Delete a comment",
)
async def delete_comment(
    prompt_id: UUID,
    comment_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
    hard_delete: bool = Query(False, description="Permanently delete (admin only)"),
) -> MessageResponse:
    """
    Delete a comment (author or admin/moderator only).

    Args:
        prompt_id: Prompt UUID
        comment_id: Comment UUID
        db: Database session
        current_user: Current authenticated user
        hard_delete: Permanently delete (admin only)

    Returns:
        MessageResponse: Success message

    Raises:
        HTTPException: If comment not found or user lacks permission
    """
    # Verify comment belongs to prompt
    comment = CommentService.get_comment_by_id(db, comment_id)
    if not comment or comment.prompt_id != prompt_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    CommentService.delete_comment(
        db=db,
        comment_id=comment_id,
        user=current_user,
        hard_delete=hard_delete,
    )

    return MessageResponse(message="Comment deleted successfully")

