"""Gmail authentication commands."""

from __future__ import annotations

import typer

from app.cli._common import console
from app.email import auth as gmail_auth
from app.email.auth import GmailAuthError
from app.logging_config import get_logger

logger = get_logger(__name__)

auth_app = typer.Typer(help="Manage Gmail OAuth authentication.")


@auth_app.command("gmail")
def auth_gmail() -> None:
    """Authenticate with Google via OAuth 2.0 and store the token locally."""
    console.print("\nStarting Gmail authentication...\n")

    if not gmail_auth.is_configured():
        console.print("[red]Gmail OAuth is not configured.[/red]")
        console.print("[dim]Please set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in .env[/dim]")
        raise typer.Exit(1)

    console.print("[dim]Opening browser for Google authorization...[/dim]\n")
    try:
        email = gmail_auth.authenticate()
    except GmailAuthError as exc:
        console.print(f"[red]Authentication failed:[/red] {exc}")
        raise typer.Exit(1)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Gmail authentication failed")
        console.print(f"[red]Authentication failed:[/red] {exc}")
        raise typer.Exit(1)

    console.print("[green]Google authentication successful[/green]")
    console.print("[green]Gmail account authenticated[/green]")
    console.print("[green]Refresh token saved securely[/green]")
    if email:
        console.print(f"\nAuthenticated Gmail:\n[bold]{email}[/bold]")


@auth_app.command("status")
def auth_status() -> None:
    """Show the current Gmail authentication status."""
    state = gmail_auth.status()

    console.print("\nGmail Authentication\n")
    console.print("Provider: Gmail API")
    console.print("OAuth: 2.0")

    if state["authenticated"]:
        console.print("[green]Status: Authenticated[/green]")
        if state["email"]:
            console.print(f"Account: {state['email']}")
    else:
        console.print("[red]Status: Not authenticated[/red]")
        if not state["configured"]:
            console.print("[dim]OAuth is not configured. Set GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET.[/dim]")
        console.print("\nRun:\n\njobapply auth gmail")


@auth_app.command("logout")
def auth_logout() -> None:
    """Remove the locally stored Gmail token (does not revoke Google access)."""
    gmail_auth.logout()
    console.print("[green]Local Gmail token removed.[/green]")
    console.print(
        "[dim]Note: this does not revoke access in your Google account "
        "(Google Cloud project untouched).[/dim]"
    )
