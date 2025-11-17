"""Tests for category service."""

import pytest
from fastapi import HTTPException, status

from src.constants import UserRole
from src.models.category import Category
from src.models.user import User
from src.schemas.category import CategoryCreate, CategoryUpdate
from src.services.category_service import CategoryService


class TestCategoryService:
    """Test cases for CategoryService."""

    def test_create_category_as_admin(self, db_session):
        """Test creating category as admin."""
        admin = User(
            username="admin",
            email="admin@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        db_session.commit()

        category_data = CategoryCreate(
            name="Test Category",
            slug="test-category",
            description="Test description",
        )

        category = CategoryService.create_category(db_session, category_data, admin)

        assert category.id is not None
        assert category.name == "Test Category"
        assert category.slug == "test-category"
        assert category.description == "Test description"

    def test_create_category_as_moderator(self, db_session):
        """Test creating category as moderator."""
        moderator = User(
            username="moderator",
            email="moderator@company.com",
            full_name="Moderator User",
            role=UserRole.MODERATOR,
        )
        db_session.add(moderator)
        db_session.commit()

        category_data = CategoryCreate(
            name="Mod Category",
            slug="mod-category",
            description="Moderator category",
        )

        category = CategoryService.create_category(db_session, category_data, moderator)

        assert category.name == "Mod Category"

    def test_create_category_as_member_forbidden(self, db_session):
        """Test that members cannot create categories."""
        member = User(
            username="member",
            email="member@company.com",
            full_name="Member User",
            role=UserRole.MEMBER,
        )
        db_session.add(member)
        db_session.commit()

        category_data = CategoryCreate(
            name="Member Category",
            slug="member-category",
            description="Should fail",
        )

        with pytest.raises(HTTPException) as exc_info:
            CategoryService.create_category(db_session, category_data, member)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_create_category_duplicate_name(self, db_session):
        """Test creating category with duplicate name."""
        admin = User(
            username="admin",
            email="admin@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        db_session.commit()

        # Create first category
        existing = Category(name="Existing", slug="existing", description="Exists")
        db_session.add(existing)
        db_session.commit()

        category_data = CategoryCreate(
            name="Existing",  # Duplicate name
            slug="different-slug",
            description="Should fail",
        )

        with pytest.raises(HTTPException) as exc_info:
            CategoryService.create_category(db_session, category_data, admin)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT

    def test_create_category_duplicate_slug(self, db_session):
        """Test creating category with duplicate slug."""
        admin = User(
            username="admin",
            email="admin@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        db_session.commit()

        # Create first category
        existing = Category(name="Different Name", slug="existing", description="Exists")
        db_session.add(existing)
        db_session.commit()

        category_data = CategoryCreate(
            name="New Name",
            slug="existing",  # Duplicate slug
            description="Should fail",
        )

        with pytest.raises(HTTPException) as exc_info:
            CategoryService.create_category(db_session, category_data, admin)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT

    def test_get_category_by_id(self, db_session):
        """Test getting category by ID."""
        category = Category(name="Test", slug="test", description="Test category")
        db_session.add(category)
        db_session.commit()

        result = CategoryService.get_category_by_id(db_session, category.id)

        assert result is not None
        assert result.id == category.id
        assert result.name == "Test"

    def test_get_category_by_id_not_found(self, db_session):
        """Test getting non-existent category by ID."""
        from uuid import uuid4

        result = CategoryService.get_category_by_id(db_session, uuid4())

        assert result is None

    def test_get_category_by_slug(self, db_session):
        """Test getting category by slug."""
        category = Category(name="Test", slug="test-slug", description="Test")
        db_session.add(category)
        db_session.commit()

        result = CategoryService.get_category_by_slug(db_session, "test-slug")

        assert result is not None
        assert result.slug == "test-slug"

    def test_get_category_by_slug_not_found(self, db_session):
        """Test getting non-existent category by slug."""
        result = CategoryService.get_category_by_slug(db_session, "non-existent")

        assert result is None

    def test_get_categories(self, db_session):
        """Test getting list of categories."""
        cat1 = Category(name="Category A", slug="category-a", description="A")
        cat2 = Category(name="Category B", slug="category-b", description="B")
        cat3 = Category(name="Category C", slug="category-c", description="C")
        db_session.add_all([cat1, cat2, cat3])
        db_session.commit()

        categories, total = CategoryService.get_categories(db_session, skip=0, limit=10)

        assert total == 3
        assert len(categories) == 3
        # Should be ordered by name
        assert categories[0].name == "Category A"

    def test_get_categories_pagination(self, db_session):
        """Test category pagination."""
        for i in range(5):
            cat = Category(name=f"Category {i}", slug=f"category-{i}", description=f"Cat {i}")
            db_session.add(cat)
        db_session.commit()

        categories, total = CategoryService.get_categories(db_session, skip=2, limit=2)

        assert total == 5
        assert len(categories) == 2

    def test_update_category_as_admin(self, db_session):
        """Test updating category as admin."""
        admin = User(
            username="admin",
            email="admin@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        category = Category(name="Original", slug="original", description="Original")
        db_session.add(category)
        db_session.commit()

        update_data = CategoryUpdate(name="Updated", description="Updated description")

        result = CategoryService.update_category(db_session, category.id, update_data, admin)

        assert result.name == "Updated"
        assert result.description == "Updated description"
        assert result.slug == "original"  # Slug unchanged

    def test_update_category_as_member_forbidden(self, db_session):
        """Test that members cannot update categories."""
        member = User(
            username="member",
            email="member@company.com",
            full_name="Member User",
            role=UserRole.MEMBER,
        )
        db_session.add(member)
        category = Category(name="Test", slug="test", description="Test")
        db_session.add(category)
        db_session.commit()

        update_data = CategoryUpdate(name="Updated")

        with pytest.raises(HTTPException) as exc_info:
            CategoryService.update_category(db_session, category.id, update_data, member)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_update_category_slug_conflict(self, db_session):
        """Test updating category with conflicting slug."""
        admin = User(
            username="admin",
            email="admin@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        cat1 = Category(name="Category 1", slug="cat-1", description="First")
        cat2 = Category(name="Category 2", slug="cat-2", description="Second")
        db_session.add_all([cat1, cat2])
        db_session.commit()

        update_data = CategoryUpdate(slug="cat-2")  # Conflict with cat2

        with pytest.raises(HTTPException) as exc_info:
            CategoryService.update_category(db_session, cat1.id, update_data, admin)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT

    def test_delete_category_as_admin(self, db_session):
        """Test deleting category as admin."""
        admin = User(
            username="admin",
            email="admin@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        category = Category(name="To Delete", slug="to-delete", description="Delete")
        db_session.add(category)
        db_session.commit()
        category_id = category.id

        CategoryService.delete_category(db_session, category_id, admin)

        # Verify deleted
        result = CategoryService.get_category_by_id(db_session, category_id)
        assert result is None

    def test_delete_category_as_moderator_forbidden(self, db_session):
        """Test that moderators cannot delete categories."""
        moderator = User(
            username="moderator",
            email="moderator@company.com",
            full_name="Moderator User",
            role=UserRole.MODERATOR,
        )
        db_session.add(moderator)
        category = Category(name="Test", slug="test", description="Test")
        db_session.add(category)
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            CategoryService.delete_category(db_session, category.id, moderator)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_category_in_use(self, db_session):
        """Test that categories in use cannot be deleted."""
        from src.models.prompt import Prompt
        from src.constants import PromptStatus, PlatformTag

        admin = User(
            username="admin",
            email="admin@company.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
        )
        db_session.add(admin)
        category = Category(name="In Use", slug="in-use", description="Used")
        db_session.add(category)
        db_session.commit()

        # Create prompt with this category
        prompt = Prompt(
            title="Test Prompt",
            content="Content",
            platform_tags=[PlatformTag.CURSOR],
            author_id=admin.id,
            status=PromptStatus.PUBLISHED,
        )
        prompt.categories = [category]
        db_session.add(prompt)
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            CategoryService.delete_category(db_session, category.id, admin)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert "associated with prompts" in exc_info.value.detail.lower()

