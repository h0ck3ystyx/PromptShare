"""Tests for comment service."""

import pytest
from fastapi import HTTPException, status
from uuid import uuid4

from src.constants import PlatformTag, PromptStatus, UserRole
from src.models.comment import Comment
from src.models.prompt import Prompt
from src.models.user import User
from src.schemas.comment import CommentCreate, CommentUpdate
from src.services.comment_service import CommentService


class TestCommentService:
    """Test cases for CommentService."""

    def test_create_comment_success(self, db_session):
        """Test creating a comment successfully."""
        # Create author and prompt
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)
        db_session.commit()

        prompt = Prompt(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add(prompt)
        db_session.commit()

        # Create comment
        comment_data = CommentCreate(content="This is a great prompt!")

        comment = CommentService.create_comment(
            db=db_session,
            prompt_id=prompt.id,
            comment_data=comment_data,
            user_id=author.id,
        )

        assert comment.id is not None
        assert comment.content == "This is a great prompt!"
        assert comment.prompt_id == prompt.id
        assert comment.user_id == author.id
        assert comment.parent_comment_id is None

    def test_create_nested_comment(self, db_session):
        """Test creating a nested comment (reply)."""
        # Create users
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        commenter = User(
            username="commenter",
            email="commenter@company.com",
            full_name="Commenter User",
            role=UserRole.MEMBER,
        )
        db_session.add_all([author, commenter])
        db_session.commit()

        # Create prompt
        prompt = Prompt(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add(prompt)
        db_session.commit()

        # Create parent comment
        parent_comment = Comment(
            prompt_id=prompt.id,
            user_id=author.id,
            content="Parent comment",
        )
        db_session.add(parent_comment)
        db_session.commit()

        # Create reply
        reply_data = CommentCreate(
            content="This is a reply",
            parent_comment_id=parent_comment.id,
        )

        reply = CommentService.create_comment(
            db=db_session,
            prompt_id=prompt.id,
            comment_data=reply_data,
            user_id=commenter.id,
        )

        assert reply.parent_comment_id == parent_comment.id

    def test_create_comment_invalid_parent(self, db_session):
        """Test creating a comment with invalid parent."""
        # Create author and prompt
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)
        db_session.commit()

        prompt = Prompt(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add(prompt)
        db_session.commit()

        # Try to create comment with non-existent parent
        comment_data = CommentCreate(
            content="Reply",
            parent_comment_id=uuid4(),
        )

        with pytest.raises(HTTPException) as exc_info:
            CommentService.create_comment(
                db=db_session,
                prompt_id=prompt.id,
                comment_data=comment_data,
                user_id=author.id,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    def test_get_comments_for_prompt(self, db_session):
        """Test getting comments for a prompt."""
        # Create author and prompt
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)
        db_session.commit()

        prompt = Prompt(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add(prompt)
        db_session.commit()

        # Create comments
        comment1 = Comment(
            prompt_id=prompt.id,
            user_id=author.id,
            content="Comment 1",
        )
        comment2 = Comment(
            prompt_id=prompt.id,
            user_id=author.id,
            content="Comment 2",
        )
        db_session.add_all([comment1, comment2])
        db_session.commit()

        comments = CommentService.get_comments_for_prompt(
            db_session, prompt.id
        )

        assert len(comments) == 2

    def test_get_comment_tree_for_prompt(self, db_session):
        """Test getting comments as a tree."""
        # Create author and prompt
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)
        db_session.commit()

        prompt = Prompt(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add(prompt)
        db_session.commit()

        # Create parent comment
        parent = Comment(
            prompt_id=prompt.id,
            user_id=author.id,
            content="Parent",
        )
        db_session.add(parent)
        db_session.commit()

        # Create reply
        reply = Comment(
            prompt_id=prompt.id,
            user_id=author.id,
            content="Reply",
            parent_comment_id=parent.id,
        )
        db_session.add(reply)
        db_session.commit()

        tree = CommentService.get_comment_tree_for_prompt(
            db_session, prompt.id
        )

        assert len(tree) == 1
        assert tree[0].id == parent.id

    def test_update_comment_author(self, db_session):
        """Test updating a comment by its author."""
        # Create author
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)
        db_session.commit()

        # Create prompt and comment
        prompt = Prompt(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add(prompt)
        db_session.commit()

        comment = Comment(
            prompt_id=prompt.id,
            user_id=author.id,
            content="Original comment",
        )
        db_session.add(comment)
        db_session.commit()

        # Update comment
        update_data = CommentUpdate(content="Updated comment")

        updated = CommentService.update_comment(
            db_session, comment.id, update_data, author
        )

        assert updated.content == "Updated comment"

    def test_update_comment_unauthorized(self, db_session):
        """Test updating a comment by unauthorized user."""
        # Create users
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        other_user = User(
            username="otheruser",
            email="otheruser@company.com",
            full_name="Other User",
            role=UserRole.MEMBER,
        )
        db_session.add_all([author, other_user])
        db_session.commit()

        # Create prompt and comment
        prompt = Prompt(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add(prompt)
        db_session.commit()

        comment = Comment(
            prompt_id=prompt.id,
            user_id=author.id,
            content="Original comment",
        )
        db_session.add(comment)
        db_session.commit()

        # Try to update as other user
        update_data = CommentUpdate(content="Unauthorized update")

        with pytest.raises(HTTPException) as exc_info:
            CommentService.update_comment(
                db_session, comment.id, update_data, other_user
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_comment_soft_delete(self, db_session):
        """Test soft deleting a comment."""
        # Create author
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)
        db_session.commit()

        # Create prompt and comment
        prompt = Prompt(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add(prompt)
        db_session.commit()

        comment = Comment(
            prompt_id=prompt.id,
            user_id=author.id,
            content="Comment to delete",
        )
        db_session.add(comment)
        db_session.commit()
        comment_id = comment.id

        # Delete comment
        CommentService.delete_comment(
            db_session, comment_id, author, hard_delete=False
        )

        # Verify soft deleted
        deleted = db_session.query(Comment).filter(Comment.id == comment_id).first()
        assert deleted.is_deleted is True
        assert deleted.content == "[deleted]"

    def test_get_comment_reply_count(self, db_session):
        """Test getting reply count for a comment."""
        # Create author
        author = User(
            username="testauthor",
            email="testauthor@company.com",
            full_name="Test Author",
            role=UserRole.MEMBER,
        )
        db_session.add(author)
        db_session.commit()

        # Create prompt and comment
        prompt = Prompt(
            title="Test Prompt",
            content="Prompt content",
            platform_tags=[PlatformTag.GITHUB_COPILOT],
            author_id=author.id,
            status=PromptStatus.PUBLISHED,
        )
        db_session.add(prompt)
        db_session.commit()

        parent = Comment(
            prompt_id=prompt.id,
            user_id=author.id,
            content="Parent",
        )
        db_session.add(parent)
        db_session.commit()

        # Create replies
        reply1 = Comment(
            prompt_id=prompt.id,
            user_id=author.id,
            content="Reply 1",
            parent_comment_id=parent.id,
        )
        reply2 = Comment(
            prompt_id=prompt.id,
            user_id=author.id,
            content="Reply 2",
            parent_comment_id=parent.id,
        )
        db_session.add_all([reply1, reply2])
        db_session.commit()

        count = CommentService.get_comment_reply_count(db_session, parent.id)
        assert count == 2

