"""Tests for password validation service."""

import pytest

from src.services.password_validation_service import PasswordValidationService


class TestPasswordValidationService:
    """Test cases for password strength validation."""

    def test_validate_weak_password(self):
        """Test validation of weak password."""
        result = PasswordValidationService.validate_password_strength("password")
        
        assert result["valid"] is False
        assert result["score"] < 2
        assert len(result["feedback"]) > 0

    def test_validate_strong_password(self):
        """Test validation of strong password."""
        result = PasswordValidationService.validate_password_strength("StrongP@ssw0rd123!")
        
        assert result["valid"] is True
        assert result["score"] >= 2
        assert len(result["feedback"]) >= 0

    def test_validate_short_password(self):
        """Test validation of password that's too short."""
        result = PasswordValidationService.validate_password_strength("short")
        
        assert result["valid"] is False
        assert any("8 characters" in f for f in result["feedback"])

    def test_validate_common_password(self):
        """Test validation of common password."""
        result = PasswordValidationService.validate_password_strength("password")
        
        assert result["valid"] is False
        assert any("common" in f.lower() for f in result["feedback"])

    def test_calculate_entropy(self):
        """Test entropy calculation."""
        entropy1 = PasswordValidationService.calculate_entropy("password")
        entropy2 = PasswordValidationService.calculate_entropy("StrongP@ssw0rd123!")
        
        assert entropy2 > entropy1
        assert entropy1 > 0
        assert entropy2 > 0

