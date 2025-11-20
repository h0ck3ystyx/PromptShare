"""Tests for password service."""

import pytest

from src.services.password_service import PasswordService


class TestPasswordService:
    """Test cases for password hashing and verification."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = PasswordService.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash format

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = PasswordService.hash_password(password)
        
        assert PasswordService.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = PasswordService.hash_password(password)
        
        assert PasswordService.verify_password(wrong_password, hashed) is False

    def test_hash_password_different_salts(self):
        """Test that same password produces different hashes (different salts)."""
        password = "test_password_123"
        hashed1 = PasswordService.hash_password(password)
        hashed2 = PasswordService.hash_password(password)
        
        # Hashes should be different due to different salts
        assert hashed1 != hashed2
        # But both should verify correctly
        assert PasswordService.verify_password(password, hashed1) is True
        assert PasswordService.verify_password(password, hashed2) is True

