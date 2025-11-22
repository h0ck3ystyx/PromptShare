# Email Service Issues

## Issue 1: Silent Email Failures
**Location**: `backend/src/services/email_service.py` (lines 164-185)

**Problem**: The `send_email` method swallows every SMTP exception and only prints a message before returning False. Both the registration and password-reset endpoints ignore that return value, so a bad SMTP credential or network issue results in a 200 OK with zero logging.

**Impact**: 
- Email delivery failures are completely silent
- Users receive success responses even when emails fail to send
- No visibility into email delivery issues in logs/metrics
- Tokens are created and committed even when emails fail

**Solution**: 
- Add structured logging (using Python's logging module) instead of print statements
- Re-raise exceptions or log with proper error level
- Have callers check the return value and react appropriately

---

## Issue 2: Ignored Email Send Results
**Location**: 
- `backend/src/routers/auth.py` (lines 279-294) - Registration endpoint
- `backend/src/routers/auth.py` (lines 439-455) - Password reset endpoint

**Problem**: Both endpoints never check the result from `EmailService.send_email`. Even if the helper reports False, the API still commits the token and returns success.

**Impact**:
- Users think emails were sent when they weren't
- Tokens are created but users never receive verification/reset links
- No way to detect email delivery failures
- Poor user experience (users wait for emails that never arrive)

**Solution**:
- Check return value from `send_email`
- Propagate error (e.g., raise HTTPException(502, "Email delivery failed") or enqueue a retry)
- Log failures appropriately
- Consider retry mechanism for transient failures

---

## Issue 3: Incorrect Email Verification URL
**Location**: `backend/src/routers/auth.py` (lines 279-288)

**Problem**: The verification email builds its link with `request.base_url`, while the password-reset mail correctly uses the externally reachable `settings.app_url`. Behind a proxy or when testing from another machine, `request.base_url` resolves to `http://127.0.0.1:7999`, so even if the email arrives, the link points to a host the recipient can't reach.

**Impact**:
- Email verification links are unusable outside the API container
- Links point to localhost/internal IPs that users can't access
- Inconsistent behavior between verification and password reset emails

**Solution**:
- Switch registration verification email to use `settings.app_url` (same pattern as password reset)
- Ensure all email links use the externally reachable frontend URL

---

## Status
- [x] Issues documented
- [x] Fixes implemented
- [ ] Tests updated
- [ ] Documentation updated

## Fixes Applied

### Issue 1: Silent Email Failures - FIXED
- Added structured logging using Python's `logging` module
- Replaced `print()` statements with proper `logger.error()` calls with `exc_info=True`
- Added `logger.info()` for successful email sends
- Added `logger.warning()` when email service is disabled

### Issue 2: Ignored Email Send Results - FIXED
- Registration endpoint now checks `email_sent` return value and logs failures
- Password reset endpoint now checks `email_sent` return value and logs failures
- Both endpoints log errors when email delivery fails
- Note: Password reset still returns success to prevent email enumeration, but failures are now logged

### Issue 3: Incorrect Email Verification URL - FIXED
- Changed verification email URL from `request.base_url` to `settings.app_url`
- Now uses consistent pattern with password reset emails
- Verification link now points to frontend URL that users can actually access

