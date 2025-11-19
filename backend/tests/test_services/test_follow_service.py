"""Tests for follow service."""

from uuid import uuid4

import pytest
from fastapi import status

from src.models.category import Category
from src.models.user import User
from src.models.user_follow import UserFollow
from src.services.follow_service import FollowService


def test_follow_category_success(db_session):
    """Test successfully following a category."""
    # Create user and category
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    category = Category(name="Test Category", slug="test-category", description="Test")
    db_session.add(category)
    db_session.commit()

    # Follow category
    follow = FollowService.follow_category(
        db=db_session,
        user_id=user.id,
        category_id=category.id,
    )

    assert follow is not None
    assert follow.user_id == user.id
    assert follow.category_id == category.id

    # Verify in database
    db_follow = db_session.query(UserFollow).filter(UserFollow.id == follow.id).first()
    assert db_follow is not None
    assert db_follow.user_id == user.id
    assert db_follow.category_id == category.id


def test_follow_category_not_found(db_session):
    """Test following a non-existent category."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    with pytest.raises(Exception) as exc_info:
        FollowService.follow_category(
            db=db_session,
            user_id=user.id,
            category_id=uuid4(),
        )

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


def test_follow_category_already_following(db_session):
    """Test following a category that is already being followed."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    category = Category(name="Test Category", slug="test-category", description="Test")
    db_session.add(category)
    db_session.commit()

    # Follow once
    FollowService.follow_category(
        db=db_session,
        user_id=user.id,
        category_id=category.id,
    )

    # Try to follow again
    with pytest.raises(Exception) as exc_info:
        FollowService.follow_category(
            db=db_session,
            user_id=user.id,
            category_id=category.id,
        )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "already following" in str(exc_info.value.detail).lower()


def test_unfollow_category_success(db_session):
    """Test successfully unfollowing a category."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    category = Category(name="Test Category", slug="test-category", description="Test")
    db_session.add(category)
    db_session.commit()

    # Follow category
    follow = FollowService.follow_category(
        db=db_session,
        user_id=user.id,
        category_id=category.id,
    )

    # Unfollow
    FollowService.unfollow_category(
        db=db_session,
        user_id=user.id,
        category_id=category.id,
    )

    # Verify removed from database
    db_follow = db_session.query(UserFollow).filter(UserFollow.id == follow.id).first()
    assert db_follow is None


def test_unfollow_category_not_following(db_session):
    """Test unfollowing a category that is not being followed."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    category = Category(name="Test Category", slug="test-category", description="Test")
    db_session.add(category)
    db_session.commit()

    with pytest.raises(Exception) as exc_info:
        FollowService.unfollow_category(
            db=db_session,
            user_id=user.id,
            category_id=category.id,
        )

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


def test_get_user_follows(db_session):
    """Test getting categories followed by a user."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    # Create multiple categories
    category1 = Category(name="Category 1", slug="category-1", description="Test")
    category2 = Category(name="Category 2", slug="category-2", description="Test")
    category3 = Category(name="Category 3", slug="category-3", description="Test")
    db_session.add_all([category1, category2, category3])
    db_session.commit()

    # Follow two categories
    FollowService.follow_category(db=db_session, user_id=user.id, category_id=category1.id)
    FollowService.follow_category(db=db_session, user_id=user.id, category_id=category2.id)

    # Get follows
    categories, total = FollowService.get_user_follows(
        db=db_session,
        user_id=user.id,
    )

    assert total == 2
    assert len(categories) == 2
    category_ids = {cat.id for cat in categories}
    assert category1.id in category_ids
    assert category2.id in category_ids
    assert category3.id not in category_ids


def test_get_user_follows_pagination(db_session):
    """Test pagination for user follows."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    # Create multiple categories
    categories = []
    for i in range(5):
        cat = Category(name=f"Category {i}", slug=f"category-{i}", description="Test")
        categories.append(cat)
        db_session.add(cat)
    db_session.commit()

    # Follow all categories
    for cat in categories:
        FollowService.follow_category(db=db_session, user_id=user.id, category_id=cat.id)

    # Get first page
    page1, total = FollowService.get_user_follows(
        db=db_session,
        user_id=user.id,
        skip=0,
        limit=2,
    )

    assert total == 5
    assert len(page1) == 2

    # Get second page
    page2, total = FollowService.get_user_follows(
        db=db_session,
        user_id=user.id,
        skip=2,
        limit=2,
    )

    assert total == 5
    assert len(page2) == 2

    # Verify no overlap
    page1_ids = {cat.id for cat in page1}
    page2_ids = {cat.id for cat in page2}
    assert page1_ids.isdisjoint(page2_ids)


def test_is_following_category(db_session):
    """Test checking if user is following a category."""
    user = User(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
    )
    db_session.add(user)
    db_session.commit()

    category1 = Category(name="Category 1", slug="category-1", description="Test")
    category2 = Category(name="Category 2", slug="category-2", description="Test")
    db_session.add_all([category1, category2])
    db_session.commit()

    # Follow category1
    FollowService.follow_category(db=db_session, user_id=user.id, category_id=category1.id)

    # Check follow status
    assert FollowService.is_following_category(db=db_session, user_id=user.id, category_id=category1.id) is True
    assert FollowService.is_following_category(db=db_session, user_id=user.id, category_id=category2.id) is False


def test_get_category_followers(db_session):
    """Test getting users following a category."""
    # Create multiple users
    users = []
    for i in range(3):
        user = User(
            email=f"user{i}@example.com",
            username=f"user{i}",
            full_name=f"User {i}",
        )
        users.append(user)
        db_session.add(user)
    db_session.commit()

    category = Category(name="Test Category", slug="test-category", description="Test")
    db_session.add(category)
    db_session.commit()

    # First two users follow the category
    FollowService.follow_category(db=db_session, user_id=users[0].id, category_id=category.id)
    FollowService.follow_category(db=db_session, user_id=users[1].id, category_id=category.id)

    # Get followers
    followers, total = FollowService.get_category_followers(
        db=db_session,
        category_id=category.id,
    )

    assert total == 2
    assert len(followers) == 2
    follower_ids = {f.id for f in followers}
    assert users[0].id in follower_ids
    assert users[1].id in follower_ids
    assert users[2].id not in follower_ids

