"""Rich-based UI prompts (separate from business logic)."""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.status import Status
from rich.table import Table


class PlexAuthUI:
    """Handles all Plex authentication UI.

    Separates presentation logic from business logic, making it easy
    to test business logic without mocking Rich components.

    Attributes:
        console: Rich Console instance for output
    """

    def __init__(self, console: Console):
        """Initialize the UI handler.

        Args:
            console: Rich Console instance to use for output
        """
        self.console = console

    def show_welcome_panel(self) -> None:
        """Display welcome panel for authentication setup."""
        self.console.print()
        self.console.print(
            Panel.fit(
                "[bold cyan]Plex Server Authentication[/bold cyan]\n\n"
                "Configure your Plex server connection.\n"
                "Token help: [link]https://support.plex.tv/articles/204059436/[/link]",
                border_style="cyan",
            )
        )
        self.console.print()

    def show_credentials_needed_panel(self) -> None:
        """Display panel when credentials are not found."""
        self.console.print()
        self.console.print(
            Panel.fit(
                "[bold yellow]Plex credentials not found[/bold yellow]\n\n"
                "Please provide your Plex server details.\n"
                "[dim]Tip: Run [bold]tpdb login[/bold] for a better setup experience[/dim]",
                border_style="yellow",
            )
        )
        self.console.print()

    def prompt_url(self, default: str = "http://localhost:32400") -> str:
        """Prompt for server URL.

        Args:
            default: Default URL to suggest

        Returns:
            The URL entered by the user
        """
        return Prompt.ask("[bold]Plex Server URL[/bold]", default=default)

    def prompt_token(self) -> str:
        """Prompt for auth token with password masking.

        Returns:
            The token entered by the user
        """
        return Prompt.ask("[bold]Plex Authentication Token[/bold]", password=True)

    def show_connecting_status(self) -> Status:
        """Return a status context manager for connection attempts.

        Returns:
            Status context manager that can be used with 'with' statement

        Example:
            >>> with ui.show_connecting_status():
            ...     result = auth.connect(url, token)
        """
        return Status("[bold cyan]Connecting to Plex server...", console=self.console)

    def show_server_info(self, server_info: dict[str, str]) -> None:
        """Display server information table.

        Args:
            server_info: Dictionary with 'name', 'version', and 'platform' keys
        """
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_row("[bold]Server Name:[/bold]", server_info.get("name", "Unknown"))
        table.add_row("[bold]Version:[/bold]", server_info.get("version", "Unknown"))
        table.add_row("[bold]Platform:[/bold]", server_info.get("platform", "Unknown"))
        self.console.print()
        self.console.print(table)

    def show_success(self, message: str) -> None:
        """Display success message with checkmark.

        Args:
            message: The success message to display
        """
        self.console.print(f"\n[bold green]✓[/bold green] {message}")

    def show_error(self, message: str) -> None:
        """Display error message with X mark.

        Args:
            message: The error message to display
        """
        self.console.print(f"\n[bold red]✗[/bold red] {message}")

    def show_warning(self, message: str) -> None:
        """Display warning message.

        Args:
            message: The warning message to display
        """
        self.console.print(f"\n[bold yellow]⚠[/bold yellow] {message}")

    def show_info(self, message: str) -> None:
        """Display info message.

        Args:
            message: The info message to display
        """
        self.console.print(f"[dim]{message}[/dim]")

    def confirm_save(self) -> bool:
        """Ask if user wants to save credentials.

        Returns:
            True if user wants to save, False otherwise
        """
        return Confirm.ask("\n[bold]Save credentials?[/bold]", default=True)
