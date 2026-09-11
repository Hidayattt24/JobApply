"""Profile CLI commands."""

from __future__ import annotations

import json

import typer
from rich.panel import Panel

from app.ai.parser import parse_cv_to_profile
from app.ai.schemas import Experience
from app.cli._common import console, get_ai_or_exit
from app.profile import repository as profile_repo
from app.profile.parser import ExtractionError

profile_app = typer.Typer(help="Manage the candidate profile.")


def _render_profile(profile) -> str:
    data = profile.model_dump()
    return json.dumps(data, ensure_ascii=False, indent=2)


@profile_app.command("import")
def import_cv(
    cv_path: str = typer.Argument(..., help="Path to CV (PDF/DOCX/TXT)."),
) -> None:
    """Parse a CV into a structured candidate profile."""
    try:
        ai = get_ai_or_exit()
        console.print("Extracting text from CV...")
        profile = parse_cv_to_profile(ai, cv_path)
    except ExtractionError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    console.print("[green]CV parsed.[/green]")
    console.print(Panel(_render_profile(profile), title="Extracted Profile"))

    if typer.confirm("Save this profile as verified?", default=False):
        profile_repo.save_profile(profile, verified=True)
        console.print("[green]Profile saved and marked verified.[/green]")
    else:
        console.print("[yellow]Profile not saved.[/yellow]")


@profile_app.command("review")
def review_profile() -> None:
    """Review the stored profile JSON."""
    if not profile_repo.profile_exists():
        console.print("[red]No profile found. Run 'profile import' first.[/red]")
        raise typer.Exit(1)
    console.print(Panel(_render_profile(profile_repo.load_profile()), title="Profile"))


@profile_app.command("show")
def show_profile() -> None:
    """Show the stored profile as JSON."""
    try:
        profile = profile_repo.load_profile()
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    facts = profile_repo.load_facts()
    console.print(json.dumps(profile.model_dump(), ensure_ascii=False, indent=2))
    console.print(
        f"\n[dim]{len(facts)} verified facts loaded from facts.json[/dim]"
    )


@profile_app.command("edit")
def edit_profile() -> None:
    """Edit the stored profile (personal info, skills, experiences)."""
    try:
        profile = profile_repo.load_profile()
    except FileNotFoundError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    p = profile.personal
    console.rule("Personal info (Enter = keep current)")

    p.name = typer.prompt("Name", default=p.name)
    p.email = typer.prompt("Email", default=p.email)
    p.phone = typer.prompt("Phone", default=p.phone)
    p.github = typer.prompt("GitHub", default=p.github)
    p.linkedin = typer.prompt("LinkedIn", default=p.linkedin)
    p.website = typer.prompt("Website / Portfolio", default=p.website)
    p.location = typer.prompt("Location", default=p.location)

    console.rule("Skills (comma separated)")
    skills_str = typer.prompt("Skills", default=", ".join(profile.skills))
    profile.skills = [s.strip() for s in skills_str.split(",") if s.strip()]

    console.rule("Experiences")
    _edit_experiences(profile)

    profile_repo.save_profile(profile, verified=True)
    console.print("[green]Profile updated and facts re-derived.[/green]")
    console.print(Panel(_render_profile(profile), title="Updated Profile"))


def _edit_experiences(profile) -> None:
    for i, exp in enumerate(profile.experiences, start=1):
        console.print(f"[dim]{i}. {exp.title} @ {exp.company}[/dim]")

    if not typer.confirm("Rewrite experiences?", default=False):
        return

    count = typer.prompt("How many experiences?", type=int, default=0)
    new_experiences: list[Experience] = []
    for i in range(count):
        console.print(f"[bold]Experience {i + 1}[/bold]")
        title = typer.prompt("Title")
        company = typer.prompt("Company")
        start = typer.prompt("Start (optional)", default="")
        end = typer.prompt("End (optional)", default="")
        description = typer.prompt("Description (optional)", default="")
        new_experiences.append(
            Experience(
                title=title,
                company=company,
                start=start,
                end=end,
                description=description,
            )
        )
    profile.experiences = new_experiences
