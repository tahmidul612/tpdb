"""Pure Plex authentication logic (no UI)."""

from dataclasses import dataclass

from plexapi.exceptions import BadRequest, Unauthorized
from plexapi.server import PlexServer
from requests.exceptions import ConnectionError, Timeout


@dataclass
class ConnectionResult:
    """Result of a Plex connection attempt.

    Attributes:
        success: Whether the connection was successful
        server: The PlexServer instance if successful, None otherwise
        error_type: Type of error that occurred (if any)
        error_message: Human-readable error message (if any)
    """

    success: bool
    server: PlexServer | None = None
    error_type: str | None = None
    error_message: str | None = None

    @property
    def server_info(self) -> dict[str, str]:
        """Get server information if connected.

        Returns:
            Dictionary with server name, version, and platform.
            Empty dict if not connected.

        Example:
            >>> result = authenticator.connect(url, token)
            >>> if result.success:
            ...     info = result.server_info
            ...     print(f"Connected to {info['name']}")
        """
        if not self.server:
            return {}
        return {
            "name": self.server.friendlyName,
            "version": self.server.version,
            "platform": self.server.platform,
        }


class PlexAuthenticator:
    """Handles Plex server authentication.

    Pure business logic with no UI dependencies - perfect for testing.

    Attributes:
        timeout: Connection timeout in seconds
    """

    def __init__(self, timeout: int = 30):
        """Initialize the authenticator.

        Args:
            timeout: Connection timeout in seconds (default: 30)
        """
        self.timeout = timeout

    def connect(self, url: str, token: str) -> ConnectionResult:
        """Attempt to connect to Plex server.

        This is a pure function with no side effects - it only attempts
        to connect and returns the result. All UI concerns are handled
        by the caller.

        Args:
            url: Plex server URL
            token: Plex authentication token

        Returns:
            ConnectionResult with success status and either server instance
            or error information.

        Example:
            >>> auth = PlexAuthenticator(timeout=30)
            >>> result = auth.connect("http://localhost:32400", "token123")
            >>> if result.success:
            ...     print(f"Connected to {result.server_info['name']}")
            ... else:
            ...     print(f"Error: {result.error_message}")
        """
        try:
            server = PlexServer(url, token, timeout=self.timeout)
            # Test connection by accessing a property
            _ = server.friendlyName
            return ConnectionResult(success=True, server=server)

        except Unauthorized:
            return ConnectionResult(
                success=False,
                error_type="unauthorized",
                error_message="Invalid authentication token",
            )
        except BadRequest as e:
            return ConnectionResult(
                success=False, error_type="bad_request", error_message=str(e)
            )
        except (ConnectionError, Timeout):
            return ConnectionResult(
                success=False,
                error_type="connection_error",
                error_message=f"Could not reach server at {url}",
            )
        except Exception as e:
            return ConnectionResult(
                success=False, error_type="unknown", error_message=str(e)
            )
