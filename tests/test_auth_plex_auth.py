"""Tests for auth/plex_auth.py"""

from unittest.mock import Mock, patch

import pytest
from plexapi.exceptions import BadRequest, Unauthorized
from requests.exceptions import ConnectionError, Timeout

from tpdb.auth.plex_auth import ConnectionResult, PlexAuthenticator


class TestConnectionResult:
    """Tests for ConnectionResult dataclass."""

    def test_successful_connection_result(self):
        """Test creating a successful connection result."""
        mock_server = Mock()
        result = ConnectionResult(success=True, server=mock_server)
        assert result.success
        assert result.server == mock_server
        assert result.error_type is None
        assert result.error_message is None

    def test_failed_connection_result(self):
        """Test creating a failed connection result."""
        result = ConnectionResult(
            success=False,
            error_type="connection_error",
            error_message="Failed to connect",
        )
        assert not result.success
        assert result.server is None
        assert result.error_type == "connection_error"
        assert result.error_message == "Failed to connect"

    def test_server_info_with_server(self):
        """Test server_info property with connected server."""
        mock_server = Mock()
        mock_server.friendlyName = "Test Server"
        mock_server.version = "1.2.3"
        mock_server.platform = "Linux"

        result = ConnectionResult(success=True, server=mock_server)
        info = result.server_info

        assert info["name"] == "Test Server"
        assert info["version"] == "1.2.3"
        assert info["platform"] == "Linux"

    def test_server_info_without_server(self):
        """Test server_info property when no server is connected."""
        result = ConnectionResult(success=False)
        info = result.server_info
        assert info == {}


class TestPlexAuthenticator:
    """Tests for PlexAuthenticator."""

    @pytest.fixture
    def authenticator(self):
        """Create a PlexAuthenticator instance."""
        return PlexAuthenticator(timeout=30)

    def test_initialization(self, authenticator):
        """Test authenticator initialization."""
        assert authenticator.timeout == 30

    def test_default_timeout(self):
        """Test default timeout is set."""
        auth = PlexAuthenticator()
        assert auth.timeout == 30

    @patch("tpdb.auth.plex_auth.PlexServer")
    def test_successful_connection(self, mock_plex_server, authenticator):
        """Test successful connection to Plex server."""
        # Setup mock
        mock_server = Mock()
        mock_server.friendlyName = "My Plex Server"
        mock_server.version = "1.30.0"
        mock_server.platform = "Linux"
        mock_plex_server.return_value = mock_server

        # Test connection
        result = authenticator.connect("http://localhost:32400", "valid_token")

        # Verify
        assert result.success
        assert result.server == mock_server
        assert result.error_type is None
        assert result.error_message is None
        mock_plex_server.assert_called_once_with(
            "http://localhost:32400", "valid_token", timeout=30
        )

    @patch("tpdb.auth.plex_auth.PlexServer")
    def test_unauthorized_connection(self, mock_plex_server, authenticator):
        """Test connection with invalid token."""
        # Setup mock to raise Unauthorized
        mock_plex_server.side_effect = Unauthorized("Invalid token")

        # Test connection
        result = authenticator.connect("http://localhost:32400", "bad_token")

        # Verify
        assert not result.success
        assert result.server is None
        assert result.error_type == "unauthorized"
        assert "Invalid authentication token" in result.error_message

    @patch("tpdb.auth.plex_auth.PlexServer")
    def test_bad_request_connection(self, mock_plex_server, authenticator):
        """Test connection with bad request."""
        # Setup mock to raise BadRequest
        mock_plex_server.side_effect = BadRequest("Bad request error")

        # Test connection
        result = authenticator.connect("http://localhost:32400", "token")

        # Verify
        assert not result.success
        assert result.server is None
        assert result.error_type == "bad_request"
        assert "Bad request error" in result.error_message

    @patch("tpdb.auth.plex_auth.PlexServer")
    def test_connection_error(self, mock_plex_server, authenticator):
        """Test connection failure due to network issues."""
        # Setup mock to raise ConnectionError
        mock_plex_server.side_effect = ConnectionError("Connection refused")

        # Test connection
        result = authenticator.connect("http://192.168.1.100:32400", "token")

        # Verify
        assert not result.success
        assert result.server is None
        assert result.error_type == "connection_error"
        assert "Could not reach server" in result.error_message
        assert "192.168.1.100:32400" in result.error_message

    @patch("tpdb.auth.plex_auth.PlexServer")
    def test_timeout_error(self, mock_plex_server, authenticator):
        """Test connection timeout."""
        # Setup mock to raise Timeout
        mock_plex_server.side_effect = Timeout("Connection timed out")

        # Test connection
        result = authenticator.connect("http://slow.server:32400", "token")

        # Verify
        assert not result.success
        assert result.server is None
        assert result.error_type == "connection_error"
        assert "Could not reach server" in result.error_message

    @patch("tpdb.auth.plex_auth.PlexServer")
    def test_unknown_exception(self, mock_plex_server, authenticator):
        """Test handling of unknown exceptions."""
        # Setup mock to raise unexpected exception
        mock_plex_server.side_effect = RuntimeError("Unexpected error")

        # Test connection
        result = authenticator.connect("http://localhost:32400", "token")

        # Verify
        assert not result.success
        assert result.server is None
        assert result.error_type == "unknown"
        assert "Unexpected error" in result.error_message

    @patch("tpdb.auth.plex_auth.PlexServer")
    def test_custom_timeout(self, mock_plex_server):
        """Test using custom timeout."""
        # Create authenticator with custom timeout
        auth = PlexAuthenticator(timeout=60)

        # Setup mock
        mock_server = Mock()
        mock_server.friendlyName = "Test"
        mock_plex_server.return_value = mock_server

        # Test connection
        auth.connect("http://localhost:32400", "token")

        # Verify timeout was passed
        mock_plex_server.assert_called_once_with(
            "http://localhost:32400", "token", timeout=60
        )

    @patch("tpdb.auth.plex_auth.PlexServer")
    def test_server_info_populated(self, mock_plex_server, authenticator):
        """Test that server info is correctly populated."""
        # Setup mock
        mock_server = Mock()
        mock_server.friendlyName = "Awesome Server"
        mock_server.version = "1.40.0"
        mock_server.platform = "Windows"
        mock_plex_server.return_value = mock_server

        # Test connection
        result = authenticator.connect("http://localhost:32400", "token")

        # Verify server info
        info = result.server_info
        assert info["name"] == "Awesome Server"
        assert info["version"] == "1.40.0"
        assert info["platform"] == "Windows"
