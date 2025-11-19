# Phase 5 Fixes Plan

## Overview
This plan addresses 4 issues identified in Phase 5 implementation related to security, data integrity, and migration management.

## Fix 1: Add Self-Protection to update_user_profile
**File**: `backend/src/services/user_service.py`
**Lines**: 206-261

### Changes
1. Add check before updating `role` field:
   - If `user_data.role` is provided and `current_user.role == UserRole.ADMIN`
   - And `user.id == current_user.id` (admin updating themselves)
   - Raise `HTTPException` with 400 status: "Cannot change your own role"

2. Add check before updating `is_active` field:
   - If `user_data.is_active` is provided and `current_user.role == UserRole.ADMIN`
   - And `user.id == current_user.id` and `user_data.is_active == False` (admin deactivating themselves)
   - Raise `HTTPException` with 400 status: "Cannot deactivate your own account"

### Code Location
```python
# In update_user_profile method, before applying role/is_active changes
if user_data.role is not None and current_user.role == UserRole.ADMIN:
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role",
        )

if user_data.is_active is not None and current_user.role == UserRole.ADMIN:
    if user.id == current_user.id and not user_data.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )
```

### Tests
- Test admin cannot change own role via `/api/users/me`
- Test admin cannot deactivate self via `/api/users/me`
- Test admin can still change other users' role/is_active via `/api/users/me`

---

## Fix 2: Add Authorization Check to User Stats Endpoint
**File**: `backend/src/routers/users.py`
**Lines**: 262-284

### Changes
1. Add authorization check in `get_user_stats` endpoint:
   - Allow access if `user_id == current_user.id` (own stats)
   - Allow access if `current_user.role` is `ADMIN` or `MODERATOR`
   - Otherwise, raise `HTTPException` with 403 status: "Not authorized to view this user's statistics"

### Code Location
```python
@router.get(
    "/{user_id}/stats",
    response_model=UserStats,
    summary="Get user statistics",
)
async def get_user_stats(
    user_id: UUID,
    db: DatabaseDep,
    current_user: CurrentUserDep,
) -> UserStats:
    """
    Get user statistics (prompts, comments, ratings, upvotes).
    Users can view their own stats, admins and moderators can view any user's stats.
    """
    # Authorization check
    if user_id != current_user.id:
        if current_user.role not in (UserRole.ADMIN, UserRole.MODERATOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this user's statistics",
            )
    
    stats = UserService.get_user_stats(db, user_id)
    return UserStats(**stats)
```

### Tests
- Test user can view own stats
- Test admin can view any user's stats
- Test moderator can view any user's stats
- Test member cannot view other user's stats (403 error)

---

## Fix 3: Set last_login on First Login
**File**: `backend/src/services/auth_service.py`
**Lines**: 100-116

### Changes
1. Set `last_login` timestamp after creating new user:
   - After `db.add(user)` and before `db.commit()`
   - Set `user.last_login = datetime.now(UTC)`

### Code Location
```python
if not user:
    user = User(
        username=ldap_user_info["username"],
        email=ldap_user_info["email"],
        full_name=ldap_user_info["full_name"],
        role=UserRole.MEMBER,
        is_active=True,
    )
    db.add(user)
    # Set last_login for new users
    user.last_login = datetime.now(UTC)
    db.commit()
    db.refresh(user)
else:
    # Update last login timestamp for existing users
    user.last_login = datetime.now(UTC)
    db.commit()
    db.refresh(user)
```

### Tests
- Test new user has `last_login` set after first login
- Test existing user has `last_login` updated on login

---

## Fix 4: Verify and Document Migration Status
**File**: `backend/src/services/user_service.py` (and migration files)
**Lines**: 286-309

### Changes
1. Verify migration exists:
   - Check that `6067905012bc_add_comments_ratings_upvotes_tables.py` exists
   - Verify it's in the Alembic history

2. Add error handling in `get_user_stats`:
   - Catch `UndefinedTable` or similar database errors
   - Provide helpful error message about running migrations

3. Document migration requirement:
   - Add comment in `get_user_stats` about required tables
   - Update README or migration docs if needed

### Code Location
```python
@staticmethod
def get_user_stats(db: Session, user_id: UUID) -> dict:
    """
    Get user statistics (prompts, comments, ratings, upvotes).
    
    Note: Requires comments, ratings, and upvotes tables to exist.
    Run migration 6067905012bc_add_comments_ratings_upvotes_tables if needed.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        # Count user's prompts
        prompt_count = db.query(func.count(Prompt.id)).filter(
            Prompt.author_id == user_id
        ).scalar() or 0

        # Count user's comments
        comment_count = db.query(func.count(Comment.id)).filter(
            Comment.user_id == user_id
        ).scalar() or 0

        # Count user's ratings
        rating_count = db.query(func.count(Rating.id)).filter(
            Rating.user_id == user_id
        ).scalar() or 0

        # Count user's upvotes
        upvote_count = db.query(func.count(Upvote.id)).filter(
            Upvote.user_id == user_id
        ).scalar() or 0

        # Get total views for user's prompts
        total_views = db.query(func.sum(Prompt.view_count)).filter(
            Prompt.author_id == user_id
        ).scalar() or 0

        return {
            "user_id": user_id,
            "prompt_count": prompt_count,
            "comment_count": comment_count,
            "rating_count": rating_count,
            "upvote_count": upvote_count,
            "total_prompt_views": total_views,
        }
    except Exception as e:
        # Handle case where tables don't exist
        if "does not exist" in str(e) or "UndefinedTable" in str(type(e).__name__):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database tables not found. Please run migrations: alembic upgrade head",
            )
        raise
```

### Verification Steps
1. Check migration file exists: `backend/migrations/versions/6067905012bc_add_comments_ratings_upvotes_tables.py`
2. Verify migration is in Alembic history: `alembic history`
3. Test that stats endpoint works after running migrations
4. Test error handling when tables don't exist

---

## Implementation Order
1. Fix 1: Self-protection in update_user_profile (security critical)
2. Fix 2: Authorization check for stats endpoint (security critical)
3. Fix 3: Set last_login on first login (data integrity)
4. Fix 4: Verify migrations and add error handling (robustness)

## Testing Strategy
- Add unit tests for each fix
- Add integration tests for security fixes
- Test edge cases (self-modification, unauthorized access)
- Verify all existing tests still pass

## Files to Modify
1. `backend/src/services/user_service.py` - Fixes 1 and 4
2. `backend/src/routers/users.py` - Fix 2
3. `backend/src/services/auth_service.py` - Fix 3
4. `backend/tests/test_services/test_user_service.py` - New tests
5. `backend/tests/test_routers/test_users.py` - New tests

