"""Authentication router endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.dependencies import CurrentUserDep, DatabaseDep
from src.schemas.user import Token, UserResponse
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token, summary="Login with LDAP/AD credentials")
async def login(
    db: DatabaseDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """
    Authenticate user with LDAP/Active Directory credentials.

    Args:
        form_data: OAuth2 form data containing username and password
        db: Database session

    Returns:
        Token: JWT access token

    Raises:
        HTTPException: If authentication fails
    """
    # Authenticate with LDAP
    ldap_user_info = AuthService.authenticate_ldap(form_data.username, form_data.password)

    if not ldap_user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get or create user in database
    user = AuthService.get_or_create_user(db, ldap_user_info)

    # Create access token
    access_token = AuthService.create_access_token(user.id)

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse, summary="Get current user information")
async def get_current_user_info(
    current_user: CurrentUserDep,
) -> UserResponse:
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user from dependency

    Returns:
        UserResponse: Current user information
    """
    return UserResponse.model_validate(current_user)


@router.post("/logout", summary="Logout current user")
async def logout() -> dict:
    """
    Logout current user (client should discard token).

    Returns:
        dict: Success message
    """
    return {"message": "Successfully logged out"}

