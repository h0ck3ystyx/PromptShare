# Phase 5 Issues

## Issue 1: Self-Protection Bypass in User Profile Update
**File**: `backend/src/services/user_service.py` (lines 206-261)
**Severity**: High
**Description**: 
The `update_user_profile` method allows admins to change their own `role` or `is_active` fields through the general update endpoint (`/api/users/me`), bypassing the safeguards in the dedicated admin endpoints (`update_user_role` and `update_user_status`). This could leave the application with no administrator.

**Current Behavior**:
- `PUT /api/users/{user_id}/role` explicitly blocks self-demotion
- `PUT /api/users/{user_id}/status` explicitly blocks self-deactivation
- `PUT /api/users/me` with `{"role": "member"}` or `{"is_active": false}` bypasses these checks

**Expected Behavior**:
- Admins should not be able to change their own role or deactivate themselves through any endpoint
- The same self-protection checks should be applied in `update_user_profile` before applying role/is_active changes

## Issue 2: User Stats Endpoint Security Vulnerability
**File**: `backend/src/routers/users.py` (lines 262-284)
**Severity**: Medium
**Description**:
The `get_user_stats` endpoint requires authentication but never inspects `current_user`, allowing any logged-in member to fetch statistics for every other user. This contradicts the "role-based access control" goal and exposes prompt/comment activity counts to unauthorized users.

**Current Behavior**:
- Endpoint requires `CurrentUserDep` but doesn't check permissions
- Any authenticated user can access any other user's statistics
- Exposes sensitive activity data (prompt counts, comment counts, etc.)

**Expected Behavior**:
- Only the subject user, admins, or moderators should be able to access user statistics
- Either remove `current_user` and document as public, or enforce proper authorization

## Issue 3: Missing last_login on First Login
**File**: `backend/src/services/auth_service.py` (lines 100-116)
**Severity**: Low
**Description**:
The `last_login` timestamp is only updated in the "user already exists" branch. When a new user authenticates for the first time, the record is created with `last_login=None`, so the "Track user activity" requirement isn't fully satisfied.

**Current Behavior**:
- New users: `last_login` is `None` after first login
- Existing users: `last_login` is updated correctly

**Expected Behavior**:
- Every successful login should update `last_login`, including the first login
- Set `user.last_login = datetime.now(UTC)` after creating the row or before returning in both branches

## Issue 4: Missing Database Migrations for Stats Query
**File**: `backend/src/services/user_service.py` (lines 286-309)
**Severity**: High
**Description**:
The `get_user_stats` method queries the `comments`, `ratings`, and `upvotes` tables, but the Alembic migration history may not include the migration that creates these tables. Without proper migrations, any call to `/api/users/{id}/stats` will crash with `UndefinedTable` error.

**Current Behavior**:
- Migration `6067905012bc_add_comments_ratings_upvotes_tables.py` was created in Phase 4
- However, the migration may not be in the Alembic history or may not have been run
- Stats endpoint will fail if tables don't exist

**Expected Behavior**:
- Verify that the migration exists and is in the Alembic history
- Ensure the migration has been run or is ready to run
- Add verification/error handling if tables are missing

