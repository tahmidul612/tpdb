"""Tests for auth/config.py"""

import configparser
from pathlib import Path

import pytest

from tpdb.auth.config import PlexConfigManager, PlexCredentials


class TestPlexCredentials:
    """Tests for PlexCredentials dataclass."""

    def test_credentials_creation(self):
        """Test creating credentials."""
        creds = PlexCredentials(url="http://localhost:32400", token="abc123")
        assert creds.url == "http://localhost:32400"
        assert creds.token == "abc123"


class TestPlexConfigManager:
    """Tests for PlexConfigManager."""

    @pytest.fixture
    def temp_config_path(self, tmp_path):
        """Create a temporary config path for testing."""
        return tmp_path / "test_config.ini"

    @pytest.fixture
    def config_manager(self, temp_config_path):
        """Create a PlexConfigManager with temp path."""
        return PlexConfigManager(config_path=temp_config_path)

    def test_default_config_path(self):
        """Test that default config path is set correctly."""
        manager = PlexConfigManager()
        assert manager.config_path == (
            Path.home() / ".config" / "plexapi" / "config.ini"
        )

    def test_custom_config_path(self, temp_config_path):
        """Test using custom config path."""
        manager = PlexConfigManager(config_path=temp_config_path)
        assert manager.config_path == temp_config_path

    def test_load_nonexistent_config(self, config_manager):
        """Test loading when config file doesn't exist."""
        creds = config_manager.load()
        assert creds is None

    def test_save_and_load_credentials(self, config_manager):
        """Test saving and loading credentials."""
        original_creds = PlexCredentials(
            url="http://localhost:32400", token="test_token_123"
        )

        # Save credentials
        config_manager.save(original_creds)
        assert config_manager.config_path.exists()

        # Load credentials
        loaded_creds = config_manager.load()
        assert loaded_creds is not None
        assert loaded_creds.url == original_creds.url
        assert loaded_creds.token == original_creds.token

    def test_save_creates_parent_directories(self, tmp_path):
        """Test that save() creates parent directories."""
        nested_path = tmp_path / "level1" / "level2" / "config.ini"
        manager = PlexConfigManager(config_path=nested_path)

        creds = PlexCredentials(url="http://localhost:32400", token="token123")
        manager.save(creds)

        assert nested_path.exists()
        assert nested_path.parent.exists()

    def test_save_overwrites_existing_config(self, config_manager):
        """Test that save() overwrites existing config."""
        # Save first credentials
        first_creds = PlexCredentials(url="http://server1:32400", token="token1")
        config_manager.save(first_creds)

        # Save different credentials
        second_creds = PlexCredentials(url="http://server2:32400", token="token2")
        config_manager.save(second_creds)

        # Load and verify it's the second set
        loaded = config_manager.load()
        assert loaded.url == second_creds.url
        assert loaded.token == second_creds.token

    def test_load_empty_url(self, config_manager, temp_config_path):
        """Test loading config with empty URL."""
        # Create config with empty URL
        config = configparser.ConfigParser()
        config["auth"] = {"server_baseurl": "", "server_token": "token123"}
        with open(temp_config_path, "w") as f:
            config.write(f)

        # Should return None because URL is empty
        creds = config_manager.load()
        assert creds is None

    def test_load_empty_token(self, config_manager, temp_config_path):
        """Test loading config with empty token."""
        # Create config with empty token
        config = configparser.ConfigParser()
        config["auth"] = {
            "server_baseurl": "http://localhost:32400",
            "server_token": "",
        }
        with open(temp_config_path, "w") as f:
            config.write(f)

        # Should return None because token is empty
        creds = config_manager.load()
        assert creds is None

    def test_load_malformed_config(self, config_manager, temp_config_path):
        """Test loading malformed config file."""
        # Create malformed config
        with open(temp_config_path, "w") as f:
            f.write("this is not a valid config file\n[[[invalid")

        # Should return None instead of raising exception
        creds = config_manager.load()
        assert creds is None

    def test_load_missing_auth_section(self, config_manager, temp_config_path):
        """Test loading config without auth section."""
        # Create config without auth section
        config = configparser.ConfigParser()
        config["other"] = {"key": "value"}
        with open(temp_config_path, "w") as f:
            config.write(f)

        # Should return None
        creds = config_manager.load()
        assert creds is None

    def test_save_raises_on_permission_error(self, tmp_path):
        """Test that save() raises IOError on permission error."""
        # Create a read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only

        config_path = readonly_dir / "config.ini"
        manager = PlexConfigManager(config_path=config_path)

        creds = PlexCredentials(url="http://localhost:32400", token="token123")

        # Should raise IOError
        with pytest.raises(IOError):
            manager.save(creds)

        # Cleanup: restore permissions
        readonly_dir.chmod(0o755)
