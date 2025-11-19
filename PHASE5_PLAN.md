# Phase 5: User Management and Permissions - Implementation Plan

## Overview
Implement role-based access control, user management endpoints, and permission decorators.

## Tasks

### 1. Permission Dependencies
- Create reusable permission dependencies:
  - `AdminDep` - Requires admin role
  - `ModeratorDep` - Requires moderator role  
  - `AdminOrModeratorDep` - Requires admin or moderator role
- Add to `src/dependencies.py`

### 2. User Management Service
- Create `src/services/user_service.py` with:
  - `get_users()` - List all users (with pagination, filters)
  - `get_user_by_id()` - Get user by ID
  - `update_user_role()` - Update user role (admin only)
  - `update_user_status()` - Activate/deactivate user (admin only)
  - `update_user_profile()` - Update user's own profile
  - `get_user_stats()` - Get user statistics (prompts, comments, etc.)

### 3. User Router
- Create `src/routers/users.py` with endpoints:
  - `GET /api/users` - List users (admin only, with pagination)
  - `GET /api/users/{user_id}` - Get user profile (public or own profile)
  - `PUT /api/users/{user_id}` - Update user (own profile or admin)
  - `PUT /api/users/{user_id}/role` - Update user role (admin only)
  - `PUT /api/users/{user_id}/status` - Activate/deactivate (admin only)
  - `GET /api/users/me` - Get current user profile
  - `PUT /api/users/me` - Update own profile

### 4. User Schemas
- Update `src/schemas/user.py`:
  - Add `UserListResponse` for paginated user lists
  - Add `UserRoleUpdate` schema
  - Add `UserStatusUpdate` schema
  - Add `UserStats` schema

### 5. Activity Tracking
- Update `AuthService.login()` to update `last_login` timestamp
- Track user activity in user model

### 6. Tests
- Create `tests/test_routers/test_users.py`
- Create `tests/test_services/test_user_service.py`
- Test permission checks
- Test admin-only endpoints
- Test user profile updates

## Implementation Order
1. Permission dependencies
2. User service
3. User schemas
4. User router
5. Activity tracking
6. Tests

