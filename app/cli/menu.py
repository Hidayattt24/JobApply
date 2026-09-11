"""Interactive main menu: a single looping command for the whole workflow."""

from __future__ import annotations

import typer
from rich.panel import Panel

from app.cli._common import console


def _prompt_path(label: str) -> str:
    return typer.prompt(f"{label} path")


def _menu_text() -> str:
    return (
        "[bold]1[/bold]  Auth Gmail\n"
        "[bold]2[/bold]  Auth status\n"
        "[bold]3[/bold]  Auth logout\n"
        "[bold]4[/bold]  Import CV\n"
        "[bold]5[/bold]  Show profile\n"
        "[bold]6[/bold]  Edit profile\n"
        "[bold]7[/bold]  Add jobs\n"
        "[bold]8[/bold]  Import jobs (CSV)\n"
        "[bold]9[/bold]  List jobs\n"
        "[bold]10[/bold] Analyze jobs\n"
        "[bold]11[/bold] Generate emails\n"
        "[bold]12[/bold] Review & approve\n"
        "[bold]13[/bold] Schedule / send\n"
        "[bold]14[/bold] History\n"
        "[bold]15[/bold] Full workflow (apply)\n"
        "[bold]0[/bold]  Exit"
    )


def _dispatch(choice: str) -> None:
    from app.cli.analyze import analyze_jobs
    from app.cli.auth import auth_gmail, auth_logout, auth_status
    from app.cli.generate import generate_emails
    from app.cli.history import list_history
    from app.cli.jobs import add_jobs, import_jobs, list_jobs
    from app.cli.main import _run_workflow
    from app.cli.profile import edit_profile, import_cv, show_profile
    from app.cli.review import review_emails
    from app.cli.schedule import schedule_emails
    from app.cli.send import send_now

    if choice == "1":
        auth_gmail()
    elif choice == "2":
        auth_status()
    elif choice == "3":
        auth_logout()
    elif choice == "4":
        import_cv(_prompt_path("CV"))
    elif choice == "5":
        show_profile()
    elif choice == "6":
        edit_profile()
    elif choice == "7":
        add_jobs()
    elif choice == "8":
        import_jobs(_prompt_path("Jobs CSV"))
    elif choice == "9":
        list_jobs()
    elif choice == "10":
        analyze_jobs()
    elif choice == "11":
        generate_emails()
    elif choice == "12":
        review_emails(all_flag=False)
    elif choice == "13":
        schedule_emails()
    elif choice == "14":
        list_history()
    elif choice == "15":
        _run_workflow()
    else:
        console.print("[yellow]Unknown option.[/yellow]")


def run_menu() -> None:
    """Run the interactive menu loop until the user exits."""
    console.rule("[bold]JOBAPPLY AI CLI - Main Menu[/bold]")
    while True:
        console.print(Panel(_menu_text(), title="Menu", border_style="cyan"))

        try:
            choice = typer.prompt("Pilih menu", default="0").strip()
        except KeyboardInterrupt:
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if choice == "0":
            console.print("[dim]Goodbye.[/dim]")
            break

        try:
            _dispatch(choice)
        except KeyboardInterrupt:
            console.print("\n[dim]Cancelled.[/dim]")
        except SystemExit:
            pass
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]Error:[/red] {exc}")

        console.print()
