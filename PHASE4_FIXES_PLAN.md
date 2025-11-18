# Phase 4 Fixes Plan

## Issues Identified

### 1. Missing Database Migration
**Issue**: Comments, ratings, and upvotes tables don't exist in database
**Impact**: Will cause "relation does not exist" errors
**Fix**: Create Alembic migration for all three tables with proper indexes and constraints

### 2. Comments Endpoint Authentication Bug
**Issue**: `current_user` always None, permission check never runs, anonymous users can see deleted comments
**Impact**: Security vulnerability, deleted comments exposed
**Fix**: Use proper OptionalUserDep, enforce permission checks

### 3. Tree Mode Not Implemented
**Issue**: Tree mode returns flat list, CommentTreeResponse unused, deleted filter only on top-level
**Impact**: Nested comments feature doesn't work, deleted replies leak
**Fix**: Implement proper tree building with recursive deleted filtering

### 4. Upvotes Summary Requires Auth
**Issue**: Endpoint requires authentication despite optional user in docstring
**Impact**: Public upvote counts not accessible
**Fix**: Use OptionalUserDep instead of CurrentUserDep

### 5. Rating Sort Not Implemented
**Issue**: HIGHEST_RATED/LOWEST_RATED sort options raise ValueError
**Impact**: Cannot sort prompts by rating
**Fix**: Implement rating-based sorting with proper joins and aggregates

### 6. Missing Tests
**Issue**: No tests for comments, ratings, or upvotes
**Impact**: Unverified code, potential bugs
**Fix**: Create comprehensive test suites for all collaboration features

## Implementation Order

1. **Create Database Migration** (Critical - blocks everything)
2. **Fix Authentication Issues** (Security - comments and upvotes)
3. **Implement Tree Mode** (Feature completeness)
4. **Implement Rating Sort** (Feature completeness)
5. **Write Tests** (Quality assurance)

## Files to Modify

- `backend/migrations/versions/` - New migration file
- `backend/src/routers/comments.py` - Fix auth, implement tree mode
- `backend/src/routers/upvotes.py` - Fix optional auth
- `backend/src/services/comment_service.py` - Fix tree building and deleted filtering
- `backend/src/services/search_service.py` - Implement rating sort
- `backend/src/services/prompt_service.py` - Implement rating sort
- `backend/src/dependencies.py` - Add OptionalUserDep if needed
- `backend/tests/test_routers/test_comments.py` - New test file
- `backend/tests/test_routers/test_ratings.py` - New test file
- `backend/tests/test_routers/test_upvotes.py` - New test file
- `backend/tests/test_services/test_comment_service.py` - New test file
- `backend/tests/test_services/test_rating_service.py` - New test file
- `backend/tests/test_services/test_upvote_service.py` - New test file

