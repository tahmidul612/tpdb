"""Tests for ui/prompts.py"""

from unittest.mock import Mock, patch

import pytest

from tpdb.ui.prompts import PlexAuthUI


class TestPlexAuthUI:
    """Tests for PlexAuthUI class."""

    @pytest.fixture
    def mock_console(self):
        """Create a mock Console."""
        return Mock()

    @pytest.fixture
    def ui(self, mock_console):
        """Create a PlexAuthUI instance with mock console."""
        return PlexAuthUI(mock_console)

    def test_initialization(self, mock_console, ui):
        """Test PlexAuthUI initialization."""
        assert ui.console == mock_console

    def test_show_welcome_panel(self, ui, mock_console):
        """Test showing welcome panel."""
        ui.show_welcome_panel()

        # Verify console.print was called (empty line, panel, empty line)
        assert mock_console.print.call_count >= 2

    def test_show_credentials_needed_panel(self, ui, mock_console):
        """Test showing credentials needed panel."""
        ui.show_credentials_needed_panel()

        # Verify console.print was called (empty line, panel, empty line)
        assert mock_console.print.call_count >= 2

    @patch("tpdb.ui.prompts.Prompt.ask")
    def test_prompt_url_default(self, mock_ask, ui):
        """Test prompting for URL with default."""
        mock_ask.return_value = "http://localhost:32400"

        result = ui.prompt_url()

        assert result == "http://localhost:32400"
        mock_ask.assert_called_once()
        # Verify default was passed
        call_kwargs = mock_ask.call_args[1]
        assert call_kwargs.get("default") == "http://localhost:32400"

    @patch("tpdb.ui.prompts.Prompt.ask")
    def test_prompt_url_custom_default(self, mock_ask, ui):
        """Test prompting for URL with custom default."""
        mock_ask.return_value = "http://custom:32400"

        result = ui.prompt_url(default="http://custom:32400")

        assert result == "http://custom:32400"
        call_kwargs = mock_ask.call_args[1]
        assert call_kwargs.get("default") == "http://custom:32400"

    @patch("tpdb.ui.prompts.Prompt.ask")
    def test_prompt_token(self, mock_ask, ui):
        """Test prompting for token with password masking."""
        mock_ask.return_value = "secret_token_123"

        result = ui.prompt_token()

        assert result == "secret_token_123"
        mock_ask.assert_called_once()
        # Verify password=True was passed
        call_kwargs = mock_ask.call_args[1]
        assert call_kwargs.get("password") is True

    def test_show_connecting_status(self, ui, mock_console):
        """Test showing connecting status."""
        status = ui.show_connecting_status()

        # Should return a Status object
        assert status is not None

    def test_show_server_info(self, ui, mock_console):
        """Test showing server information."""
        server_info = {"name": "Test Server", "version": "1.30.0", "platform": "Linux"}

        ui.show_server_info(server_info)

        # Verify console.print was called twice (empty line and table)
        assert mock_console.print.call_count == 2

    def test_show_server_info_missing_keys(self, ui, mock_console):
        """Test showing server info with missing keys."""
        server_info = {}  # Empty dict

        ui.show_server_info(server_info)

        # Should handle missing keys gracefully
        assert mock_console.print.call_count == 2

    def test_show_success(self, ui, mock_console):
        """Test showing success message."""
        ui.show_success("Operation completed")

        mock_console.print.assert_called_once()
        call_args = str(mock_console.print.call_args)
        assert "✓" in call_args
        assert "Operation completed" in call_args

    def test_show_error(self, ui, mock_console):
        """Test showing error message."""
        ui.show_error("Something went wrong")

        mock_console.print.assert_called_once()
        call_args = str(mock_console.print.call_args)
        assert "✗" in call_args
        assert "Something went wrong" in call_args

    def test_show_warning(self, ui, mock_console):
        """Test showing warning message."""
        ui.show_warning("This is a warning")

        mock_console.print.assert_called_once()
        call_args = str(mock_console.print.call_args)
        assert "⚠" in call_args
        assert "This is a warning" in call_args

    def test_show_info(self, ui, mock_console):
        """Test showing info message."""
        ui.show_info("This is some information")

        mock_console.print.assert_called_once()
        call_args = str(mock_console.print.call_args)
        assert "This is some information" in call_args

    @patch("tpdb.ui.prompts.Confirm.ask")
    def test_confirm_save_yes(self, mock_confirm, ui):
        """Test confirm save when user says yes."""
        mock_confirm.return_value = True

        result = ui.confirm_save()

        assert result is True
        mock_confirm.assert_called_once()
        # Verify default is True
        call_kwargs = mock_confirm.call_args[1]
        assert call_kwargs.get("default") is True

    @patch("tpdb.ui.prompts.Confirm.ask")
    def test_confirm_save_no(self, mock_confirm, ui):
        """Test confirm save when user says no."""
        mock_confirm.return_value = False

        result = ui.confirm_save()

        assert result is False
