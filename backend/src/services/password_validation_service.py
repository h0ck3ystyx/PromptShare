"""Password strength validation service."""

import re
from typing import Dict, List


class PasswordValidationService:
    """Service for validating password strength."""

    # Common weak passwords (should be expanded with breach list in production)
    COMMON_PASSWORDS = {
        "password",
        "123456",
        "12345678",
        "qwerty",
        "abc123",
        "password1",
        "admin",
        "letmein",
        "welcome",
        "monkey",
    }

    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, any]:
        """
        Validate password strength and return feedback.

        Args:
            password: Password to validate

        Returns:
            dict: Validation result with 'valid' (bool), 'score' (int 0-4), and 'feedback' (list of strings)
        """
        feedback: List[str] = []
        score = 0

        # Length check
        if len(password) < 8:
            feedback.append("Password must be at least 8 characters long")
        elif len(password) >= 12:
            score += 1
        else:
            score += 0.5

        # Check for common passwords
        if password.lower() in PasswordValidationService.COMMON_PASSWORDS:
            feedback.append("Password is too common. Please choose a more unique password.")
        else:
            score += 1

        # Check for uppercase letters
        if re.search(r"[A-Z]", password):
            score += 0.5
        else:
            feedback.append("Consider adding uppercase letters")

        # Check for lowercase letters
        if re.search(r"[a-z]", password):
            score += 0.5
        else:
            feedback.append("Consider adding lowercase letters")

        # Check for numbers
        if re.search(r"\d", password):
            score += 0.5
        else:
            feedback.append("Consider adding numbers")

        # Check for special characters
        if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            score += 0.5
        else:
            feedback.append("Consider adding special characters (!@#$%^&*)")

        # Entropy check (simple)
        unique_chars = len(set(password))
        if unique_chars < len(password) * 0.5:
            feedback.append("Password has low character diversity")

        # Final score (0-4 scale)
        final_score = min(4, int(score))

        # Determine if valid (at least score 2 and no critical issues)
        valid = final_score >= 2 and len(password) >= 8 and password.lower() not in PasswordValidationService.COMMON_PASSWORDS

        if valid and not feedback:
            feedback.append("Password strength: Good")

        return {
            "valid": valid,
            "score": final_score,
            "feedback": feedback,
        }

    @staticmethod
    def calculate_entropy(password: str) -> float:
        """
        Calculate password entropy (simplified).

        Args:
            password: Password to analyze

        Returns:
            float: Entropy value (higher is better)
        """
        if not password:
            return 0.0

        # Count character types
        has_lower = bool(re.search(r"[a-z]", password))
        has_upper = bool(re.search(r"[A-Z]", password))
        has_digit = bool(re.search(r"\d", password))
        has_special = bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))

        # Calculate character set size
        charset_size = 0
        if has_lower:
            charset_size += 26
        if has_upper:
            charset_size += 26
        if has_digit:
            charset_size += 10
        if has_special:
            charset_size += 20  # Approximate

        if charset_size == 0:
            return 0.0

        # Entropy = log2(charset_size^length)
        import math
        entropy = len(password) * math.log2(charset_size)
        return entropy

