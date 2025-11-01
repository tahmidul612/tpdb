"""Plex configuration management."""

import configparser
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PlexCredentials:
    """Plex server credentials.

    Attributes:
        url: Plex server base URL (e.g., http://localhost:32400)
        token: Plex authentication token
    """

    url: str
    token: str


class PlexConfigManager:
    """Manages Plex configuration persistence.

    Handles loading and saving Plex server credentials to a config file
    following the plexapi config format.

    Attributes:
        config_path: Path to the configuration file
    """

    DEFAULT_CONFIG_DIR = Path.home() / ".config" / "plexapi"
    DEFAULT_CONFIG_FILE = "config.ini"

    def __init__(self, config_path: Path | None = None):
        """Initialize the config manager.

        Args:
            config_path: Custom path to config file. If None, uses default location.
        """
        self.config_path = config_path or (
            self.DEFAULT_CONFIG_DIR / self.DEFAULT_CONFIG_FILE
        )

    def load(self) -> PlexCredentials | None:
        """Load credentials from config file.

        Returns:
            PlexCredentials if config exists and is valid, None otherwise.

        Example:
            >>> manager = PlexConfigManager()
            >>> creds = manager.load()
            >>> if creds:
            ...     print(f"Server: {creds.url}")
        """
        if not self.config_path.exists():
            return None

        config = configparser.ConfigParser()
        try:
            config.read(self.config_path)
            url = config.get("auth", "server_baseurl", fallback="")
            token = config.get("auth", "server_token", fallback="")

            # Return None if either value is empty
            if not url or not token:
                return None

            return PlexCredentials(url=url, token=token)
        except (configparser.Error, KeyError):
            return None

    def save(self, credentials: PlexCredentials) -> None:
        """Save credentials to config file.

        Creates parent directories if they don't exist.

        Args:
            credentials: The credentials to save

        Raises:
            IOError: If the config file cannot be written

        Example:
            >>> manager = PlexConfigManager()
            >>> creds = PlexCredentials(url="http://localhost:32400", token="abc123")
            >>> manager.save(creds)
        """
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        config = configparser.ConfigParser()
        config["auth"] = {
            "server_baseurl": credentials.url,
            "server_token": credentials.token,
        }

        try:
            with open(self.config_path, "w") as f:
                config.write(f)
        except OSError as e:
            raise IOError(f"Failed to save config to {self.config_path}: {e}") from e
