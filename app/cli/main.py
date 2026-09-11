"""Main Typer application."""

from __future__ import annotations

import typer

from app import __version__
from app.cli.analyze import analyze_jobs
from app.cli.auth import auth_app
from app.cli.generate import generate_emails
from app.cli.history import history_app
from app.cli.jobs import jobs_app
from app.cli.profile import profile_app
from app.cli.review import review_app
from app.cli.schedule import schedule_app
from app.cli.send import send_app
from app.cli._common import console, load_profile_or_exit
from app.config import ensure_dirs, get_settings
from app.database.database import init_db

app = typer.Typer(
    name="jobapply",
    help="AI job application email automation CLI.",
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def _main_callback(ctx: typer.Context) -> None:
    """Open the interactive menu when no subcommand is given."""
    if ctx.invoked_subcommand is None:
        from app.cli.menu import run_menu

        run_menu()

app.add_typer(profile_app, name="profile")
app.add_typer(jobs_app, name="job")
app.add_typer(review_app, name="review")
app.add_typer(send_app, name="send")
app.add_typer(schedule_app, name="schedule")
app.add_typer(history_app, name="history")
app.add_typer(auth_app, name="auth")


@app.command("analyze")
def analyze(
    jobs: str = typer.Option(None, "--jobs", help="Comma-separated job IDs to analyze."),
    all_flag: bool = typer.Option(False, "--all", help="Analyze all jobs."),
) -> None:
    """Analyze selected job descriptions via AI."""
    analyze_jobs(job_ids=jobs, all_flag=all_flag)


@app.command("generate")
def generate(
    jobs: str = typer.Option(None, "--jobs", help="Comma-separated job IDs to generate."),
    all_flag: bool = typer.Option(False, "--all", help="Generate all jobs."),
) -> None:
    """Generate personalized emails for selected jobs via AI."""
    generate_emails(job_ids=jobs, all_flag=all_flag)


@app.command("init")
def init() -> None:
    """Initialize directories, database, and check configuration."""
    ensure_dirs()
    init_db()
    settings = get_settings()

    console.print("[green]Project initialized.[/green]")
    if not settings.ai_api_key:
        console.print("[yellow]Warning: AI_API_KEY is not set in .env.[/yellow]")
    if settings.ai_provider.lower() != "gemini":
        console.print(
            f"[yellow]Warning: only 'gemini' provider is implemented "
            f"(configured: {settings.ai_provider}).[/yellow]"
        )
    if settings.email_dry_run:
        console.print("[yellow]EMAIL_DRY_RUN is enabled.[/yellow]")
    console.print("[green]Database ready.[/green]")


@app.command("run")
def run() -> None:
    """Run the end-to-end workflow interactively (alias: apply)."""
    _run_workflow()


@app.command("apply")
def apply() -> None:
    """Run the end-to-end workflow interactively."""
    _run_workflow()


@app.command("menu")
def menu() -> None:
    """Open the interactive main menu."""
    from app.cli.menu import run_menu

    run_menu()


def _run_workflow() -> None:
    from app.cli.jobs import add_jobs
    from app.cli.generate import generate_emails
    from app.cli.review import review_emails
    from app.cli.schedule import schedule_emails

    console.rule("[bold]JOBAPPLY AI CLI[/bold]")
    load_profile_or_exit()
    console.print("[green]Profile loaded and verified.[/green]")

    add_jobs()
    generate_emails()
    review_emails(all_flag=False)
    schedule_emails()
    console.print("[bold green]Workflow complete.[/bold green]")


@app.command("scheduler-run")
def scheduler_run(
    interval: int = typer.Option(30, help="Polling interval in seconds."),
) -> None:
    """Run the scheduler daemon to send due scheduled emails."""
    from app.scheduler.service import start_daemon

    start_daemon(interval_seconds=interval)


@app.command("version")
def version() -> None:
    """Show version."""
    console.print(f"JobApply AI CLI v{__version__}")


if __name__ == "__main__":
    app()
