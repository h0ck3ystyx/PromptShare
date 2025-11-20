# Test Failure Fix Plan

## Summary
- **Total Tests**: 226
- **Passing**: 198 (87.6%)
- **Failing**: 28 (12.4%)

## Failure Categories

### 1. Pydantic DateTime Serialization Issues (13 failures)
**Problem**: `CollectionResponse` and `FAQResponse` schemas expect `created_at` and `updated_at` as strings, but SQLAlchemy models return datetime objects.

**Affected Tests**:
- `test_collections.py`: 6 failures (create, list, get, update)
- `test_faqs.py`: 6 failures (create, list, get, update)
- `test_onboarding.py`: 1 failure (get_onboarding_materials)

**Root Cause**: 
- Schemas define `created_at: str` and `updated_at: str`
- SQLAlchemy models have `created_at` and `updated_at` as `datetime` objects
- `model_validate()` doesn't automatically convert datetime to string

**Fix Strategy**:
1. Add Pydantic validators to convert datetime to ISO format strings
2. OR change schema fields to `datetime` and use Pydantic's datetime serialization
3. OR use `model_serializer` to handle conversion

**Recommended Fix**: Add validators to convert datetime to ISO strings:
```python
from pydantic import field_validator
from datetime import datetime

@field_validator('created_at', 'updated_at', mode='before')
@classmethod
def convert_datetime(cls, v):
    if isinstance(v, datetime):
        return v.isoformat()
    return v
```

**Files to Fix**:
- `backend/src/schemas/collection.py` - Add validators to `CollectionResponse`
- `backend/src/schemas/faq.py` - Add validators to `FAQResponse`

---

### 2. Test Code Issues - Missing Flush/Commit (9 failures)
**Problem**: Tests create User objects but don't flush/commit before using their IDs, resulting in `author_id=None` when creating prompts.

**Affected Tests**:
- `test_analytics.py`: 3 failures
- `test_analytics_service.py`: 4 failures
- `test_prompts.py`: 1 failure (search tracks analytics)
- `test_comment_service.py`: 1 failure (nested comment)

**Root Cause**:
```python
author = User(...)
prompt = Prompt(..., author_id=author.id)  # author.id is None!
db_session.add_all([author, prompt])
db_session.commit()  # Fails because author_id is None
```

**Fix Strategy**:
1. Flush after adding author to get the ID: `db_session.add(author); db_session.flush()`
2. OR commit author first, then create prompt
3. OR use relationship instead of ID: `prompt.author = author`

**Recommended Fix**: Flush after adding author:
```python
author = User(...)
db_session.add(author)
db_session.flush()  # Get the ID
prompt = Prompt(..., author_id=author.id)
db_session.add(prompt)
db_session.commit()
```

**Files to Fix**:
- `backend/tests/test_routers/test_analytics.py`
- `backend/tests/test_services/test_analytics_service.py`
- `backend/tests/test_routers/test_prompts.py`
- `backend/tests/test_services/test_comment_service.py`

---

### 3. Celery Task Signature Issues (5 failures)
**Problem**: `send_notification_task()` is being called incorrectly in tests. The task signature expects `self` as first parameter (bound task), but tests are passing arguments incorrectly.

**Affected Tests**:
- `test_notifications.py`: 5 failures

**Root Cause**:
```python
# Task definition:
def send_notification_task(self: DatabaseTask, user_id: str, ...)

# Test calls it like:
send_notification_task(task_instance, user_id, ...)
# But task_instance is already 'self', so user_id gets passed twice
```

**Fix Strategy**:
1. Fix test mock to call task correctly: `send_notification_task.run(user_id, ...)`
2. OR fix the mock in `conftest.py` to handle bound tasks properly

**Recommended Fix**: Update `conftest.py` mock to use `.run()`:
```python
def sync_notif_task(*args, **kwargs):
    from src.tasks.notifications import send_notification_task
    # Remove task_instance from args since it's bound
    return send_notification_task.run(*args, **kwargs)
```

**Files to Fix**:
- `backend/tests/conftest.py` - Fix `sync_notif_task` function
- `backend/tests/test_tasks/test_notifications.py` - Fix task calls

---

### 4. Redis Connection Errors (1 failure)
**Problem**: Some tests try to connect to Redis which isn't running in test environment.

**Affected Tests**:
- `test_comment_service.py`: 1 failure (nested comment)

**Root Cause**: 
- Test creates nested comment which triggers notification task
- Notification task tries to connect to Redis via Celery
- Redis isn't running in test environment

**Fix Strategy**:
1. Ensure Celery tasks are properly mocked in `conftest.py`
2. OR skip Redis-dependent tests if Redis isn't available
3. OR use in-memory broker for tests

**Recommended Fix**: The mock in `conftest.py` should already handle this, but the nested comment test might be bypassing the mock. Ensure all task calls go through the mock.

**Files to Fix**:
- `backend/tests/test_services/test_comment_service.py` - Ensure task is mocked
- `backend/tests/conftest.py` - Verify mock covers all cases

---

### 5. SQLAlchemy Session Issues (2 failures)
**Problem**: DetachedInstanceError and ForeignKeyViolation in notification tests.

**Affected Tests**:
- `test_notifications.py`: 2 failures (bulk notifications)

**Root Cause**:
1. Users are accessed after session is closed (DetachedInstanceError)
2. Foreign key violation when creating notification for non-existent user

**Fix Strategy**:
1. Ensure users are committed before creating notifications
2. Access user attributes before session closes
3. Use proper session management in bulk task

**Recommended Fix**: 
- Commit users before creating notifications
- Access `user.id` before session operations that might detach objects

**Files to Fix**:
- `backend/tests/test_tasks/test_notifications.py`

---

## Implementation Priority

### Priority 1: High Impact, Easy Fixes
1. **Pydantic DateTime Serialization** (13 failures)
   - Quick fix with validators
   - Affects multiple test files
   - Low risk

2. **Test Code Flush Issues** (9 failures)
   - Simple fix: add `flush()` calls
   - Clear pattern across tests
   - Low risk

### Priority 2: Medium Impact, Moderate Complexity
3. **Celery Task Signature** (5 failures)
   - Requires understanding bound tasks
   - Fix in conftest affects all tests
   - Medium risk

### Priority 3: Low Impact, Complex
4. **Redis Connection** (1 failure)
   - May be fixed by Priority 2
   - Low priority

5. **SQLAlchemy Session** (2 failures)
   - Requires careful session management
   - Medium complexity

---

## Estimated Effort

- **Priority 1**: 2-3 hours
  - Pydantic validators: 30 minutes
  - Test flush fixes: 1-2 hours
  
- **Priority 2**: 1-2 hours
  - Celery task fixes: 1-2 hours
  
- **Priority 3**: 1 hour
  - Session management: 30 minutes
  - Redis mocking: 30 minutes

**Total Estimated Time**: 4-6 hours

---

## Testing Strategy

After fixes:
1. Run full test suite: `pytest`
2. Run specific test files to verify fixes
3. Check for regressions in passing tests
4. Aim for 100% pass rate (226/226)

---

## Notes

- All failures are in test code or schema definitions, not production code
- No production logic changes required
- Fixes are backward compatible
- Some failures may be fixed by fixing others (e.g., Celery fix may fix Redis issue)

