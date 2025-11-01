"""Tests for auth/validators.py"""

import pytest

from tpdb.auth.validators import validate_and_normalize_url, validate_token


class TestValidateAndNormalizeUrl:
    """Tests for URL validation and normalization."""

    @pytest.mark.parametrize(
        "url,expected_valid,expected_url",
        [
            # Valid URLs
            ("http://localhost:32400", True, "http://localhost:32400"),
            ("https://plex.example.com:32400", True, "https://plex.example.com:32400"),
            ("http://192.168.1.100:32400", True, "http://192.168.1.100:32400"),
            # URLs without scheme (should be normalized)
            ("localhost:32400", True, "http://localhost:32400"),
            ("192.168.1.100:32400", True, "http://192.168.1.100:32400"),
            ("plex.example.com", True, "http://plex.example.com"),
            # URLs with extra whitespace
            ("  http://localhost:32400  ", True, "http://localhost:32400"),
            # Invalid URLs
            ("ftp://localhost:32400", False, "ftp://localhost:32400"),
            ("", False, "http://"),
            ("   ", False, "http://"),
        ],
    )
    def test_validate_and_normalize_url(self, url, expected_valid, expected_url):
        """Test URL validation with various inputs."""
        is_valid, normalized_url, error = validate_and_normalize_url(url)
        assert is_valid == expected_valid
        if expected_valid:
            assert normalized_url == expected_url
            assert error == ""
        else:
            assert error != ""

    def test_url_without_scheme_adds_http(self):
        """Test that URLs without scheme get http:// added."""
        is_valid, url, error = validate_and_normalize_url("localhost:32400")
        assert is_valid
        assert url.startswith("http://")

    def test_https_url_preserved(self):
        """Test that HTTPS URLs are not changed to HTTP."""
        is_valid, url, error = validate_and_normalize_url("https://secure.server:32400")
        assert is_valid
        assert url.startswith("https://")


class TestValidateToken:
    """Tests for token validation."""

    @pytest.mark.parametrize(
        "token,expected_valid",
        [
            # Valid tokens
            ("abc123def456", True),
            ("a" * 20, True),  # Long token
            ("1234567890", True),  # Exactly 10 chars
            ("token-with-hyphens", True),
            # Invalid tokens
            ("", False),  # Empty
            ("   ", False),  # Whitespace only
            ("short", False),  # Too short
            ("has space in it", False),  # Contains space
            ("a" * 9, False),  # Just under minimum
        ],
    )
    def test_validate_token(self, token, expected_valid):
        """Test token validation with various inputs."""
        is_valid, error = validate_token(token)
        assert is_valid == expected_valid
        if expected_valid:
            assert error == ""
        else:
            assert error != ""

    def test_token_with_leading_trailing_whitespace(self):
        """Test that tokens are trimmed before validation."""
        is_valid, error = validate_token("  valid_token_123  ")
        assert is_valid
        assert error == ""

    def test_empty_token_error_message(self):
        """Test that empty token has appropriate error."""
        is_valid, error = validate_token("")
        assert not is_valid
        assert "empty" in error.lower()

    def test_short_token_error_message(self):
        """Test that short token has appropriate error."""
        is_valid, error = validate_token("short")
        assert not is_valid
        assert "short" in error.lower()

    def test_token_with_spaces_error_message(self):
        """Test that token with spaces has appropriate error."""
        is_valid, error = validate_token("has spaces")
        assert not is_valid
        assert "space" in error.lower()
