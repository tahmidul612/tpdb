"""Input validation for Plex authentication."""

from urllib.parse import urlparse


def validate_and_normalize_url(url: str) -> tuple[bool, str, str]:
    """Validate and normalize a Plex server URL.

    Automatically adds http:// scheme if missing. Validates that the URL
    is properly formatted and uses http or https.

    Args:
        url: The URL to validate and normalize

    Returns:
        Tuple of (is_valid, normalized_url, error_message).
        If valid, error_message is empty string.

    Example:
        >>> validate_and_normalize_url("localhost:32400")
        (True, "http://localhost:32400", "")
        >>> validate_and_normalize_url("invalid url")
        (False, "http://invalid url", "Invalid URL format")
    """
    url = url.strip()

    # Check if URL already has a scheme that's not http/https
    if "://" in url and not url.startswith(("http://", "https://")):
        return False, url, "URL must use http or https"

    # Add scheme if missing
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"

    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return False, url, "URL must use http or https"

        if not parsed.netloc:
            return False, url, "Invalid URL format"

        return True, url, ""

    except Exception as e:
        return False, url, f"Invalid URL: {e}"


def validate_token(token: str) -> tuple[bool, str]:
    """Validate a Plex authentication token.

    Performs basic validation checks on the token format.

    Args:
        token: The token to validate

    Returns:
        Tuple of (is_valid, error_message).
        If valid, error_message is empty string.

    Example:
        >>> validate_token("abc123def456")
        (True, "")
        >>> validate_token("")
        (False, "Token cannot be empty")
    """
    token = token.strip()

    if not token:
        return False, "Token cannot be empty"

    if len(token) < 10:
        return False, "Token seems too short"

    if " " in token:
        return False, "Token should not contain spaces"

    return True, ""
