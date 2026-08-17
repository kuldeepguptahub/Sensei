"""
CLI application for Sensei.

Provides commands for provider setup, course management, and learning.
"""

import json
import typer
import traceback
from typing import Optional

app = typer.Typer()


@app.command()
def help():
    """
    Displays list of available commands and their descriptions.
    """
    typer.echo("Available commands:")
    typer.echo("  connect      - Connect to an LLM provider (OpenCode Zen, OpenAI, etc.)")
    typer.echo("  models       - List available models for connected provider")
    typer.echo("  current      - Show current provider and model")
    typer.echo("  list         - List all available courses and their status")
    typer.echo("  start-new-course - Start a new course (--verbose for details)")
    typer.echo("  resume       - Resume a course from recent checkpoint (--verbose for details)")
    typer.echo("  complete-course - Mark a course as completed")
    typer.echo("  delete-course - Delete an existing course")
    typer.echo("  rename-course - Rename an existing course")


@app.command()
def connect():
    """
    Connect to an LLM provider.

    Interactively select a provider and enter your API key.
    """
    from sensei.gateway.providers import list_providers
    from sensei.gateway.config import save_config

    providers = list_providers()

    typer.echo("\nSelect a provider:\n")
    for i, provider in enumerate(providers, 1):
        typer.echo(f"  {i}. {provider['name']}")

    selection = typer.prompt("\nEnter the number of your provider", type=int)

    if selection < 1 or selection > len(providers):
        typer.echo("Invalid selection.")
        return

    selected_provider = providers[selection - 1]

    # Get API key (skip for Ollama which doesn't need one)
    api_key = ""
    if selected_provider.get("auth_header"):
        api_key = typer.prompt(f"Enter your {selected_provider['name']} API key")

    # Get model selection
    models = selected_provider.get("models", [])

    if not models:
        typer.echo("\nNo predefined models. Enter model ID manually.")
        model_id = typer.prompt("Model ID")
    else:
        typer.echo(f"\nAvailable models for {selected_provider['name']}:\n")
        for i, model in enumerate(models, 1):
            typer.echo(f"  {i}. {model}")

        model_selection = typer.prompt("\nEnter the number of your model", type=int)

        if model_selection < 1 or model_selection > len(models):
            typer.echo("Invalid selection.")
            return

        model_id = models[model_selection - 1]

    # Save configuration
    save_config(
        provider_name=selected_provider["id"],
        api_key=api_key,
        model_id=model_id,
        base_url=selected_provider["base_url"],
        auth_header=selected_provider.get("auth_header"),
        auth_prefix=selected_provider.get("auth_prefix", ""),
        api_type=selected_provider.get("api_type", "openai"),
    )

    typer.echo(f"\n✓ Connected to {selected_provider['name']} ({model_id})")

    # Test connection
    typer.echo("\nTesting connection...")
    try:
        from sensei.gateway.client import generate
        response = generate("Respond with 'OK' to confirm connection.")
        typer.echo(f"✓ Connection successful!")
        typer.echo(f"  Response: {response[:100]}...")
    except Exception as e:
        typer.echo(f"⚠ Connection test failed: {e}")
        typer.echo("  You can try again later with 'sensei connect'")


@app.command()
def models():
    """
    List available models for the connected provider.
    """
    from sensei.gateway.config import load_config, config_exists
    from sensei.gateway.providers import get_provider

    if not config_exists():
        typer.echo("No provider connected. Run 'sensei connect' first.")
        return

    config = load_config()
    provider = get_provider(config.provider_name)

    if provider and provider.get("models"):
        typer.echo(f"\nAvailable models for {provider['name']}:\n")
        for i, model in enumerate(provider["models"], 1):
            marker = " ← current" if model == config.model_id else ""
            typer.echo(f"  {i}. {model}{marker}")
    else:
        typer.echo(f"\nCurrent model: {config.model_id}")
        typer.echo("Provider does not have a predefined model list.")


@app.command()
def current():
    """
    Show current provider and model configuration.
    """
    from sensei.gateway.config import load_config, config_exists
    from sensei.gateway.providers import get_provider

    if not config_exists():
        typer.echo("No provider connected. Run 'sensei connect' first.")
        return

    config = load_config()
    provider = get_provider(config.provider_name)

    typer.echo("\nCurrent configuration:\n")
    typer.echo(f"  Provider:    {provider['name'] if provider else config.provider_name}")
    typer.echo(f"  Model:       {config.model_id}")
    typer.echo(f"  Base URL:    {config.base_url}")
    typer.echo(f"  API Type:    {config.api_type}")


@app.command()
def list():
    """
    Lists all the available courses and their status.
    """
    from sensei.agent.registry import get_skill
    list_courses = get_skill('list_courses')

    courses = list_courses()
    if not courses:
        typer.echo("No courses found.")
    else:
        typer.echo("Available courses:")
        for i, course in enumerate(courses, 1):
            typer.echo(f"{i}. {course['name']}")


@app.command()
def start_new_course(verbose: bool = typer.Option(False, "--verbose", "-v", help="Show tool calls and compression activity")):
    """
    Starts a new course.
    """
    from sensei.agent.session import Session
    from sensei.agent.registry import get_skill
    from sensei.gateway.config import config_exists
    from sensei.validation import validate_course_name

    if not config_exists():
        typer.echo("No provider connected. Run 'sensei connect' first.")
        return

    course_name = typer.prompt("Enter the name of the new course")

    # Validate course name
    try:
        course_name = validate_course_name(course_name)
    except ValueError as e:
        typer.echo(f"Error: {e}")
        return

    # Create workspace using skill
    create_workspace = get_skill('create_workspace')
    try:
        create_workspace(course_name)
        typer.echo(f"Workspace created for course: {course_name}")
    except ValueError as e:
        typer.echo(f"Error: {e}")
        return
    except OSError as e:
        typer.echo(f"Error creating workspace: {e}")
        return

    # Hand control to the agent for planning
    typer.echo("\n" + "=" * 60)
    typer.echo("SENSEI COURSE PLANNING".center(60))
    typer.echo("=" * 60)
    typer.echo("\nSensei will now interview you to understand your goals")
    typer.echo("and create a personalized learning plan.\n")

    # Create session for the planning conversation
    try:
        session = Session(course_name, verbose=verbose)
    except FileNotFoundError as e:
        typer.echo(f"Error loading course: {e}")
        return
    except Exception as e:
        typer.echo(f"Error initializing session: {e}")
        if verbose:
            traceback.print_exc()
        return

    # Start the planning conversation
    planning_prompt = f"""
Create a new course called '{course_name}'.

Follow the planning workflow:
1. Interview me to understand my goals, topic, desired outcomes, current knowledge, and constraints
2. Review any uploaded resources in the uploads/ directory
3. Design a personalized learning roadmap
4. Create the course artifacts (definition.json and planner.md)
5. Present the roadmap for my approval using the exact format specified in the instructions

Ask me questions one at a time and wait for my responses.
"""

    response = session.send(planning_prompt)
    typer.echo(response)

    # Continue the conversation until planning is complete
    while True:
        user_input = typer.prompt("\nYour response (or 'approve' to start, 'adjust' to modify, 'quit' to exit)")

        if user_input.lower() == 'quit':
            typer.echo("Course creation cancelled.")
            return
        elif user_input.lower() == 'approve':
            # Update course status to active
            session.update_state(
                status="active",
                current_module=0,
                current_lesson=0,
                progress=0.0
            )

            typer.echo("\n" + "=" * 60)
            typer.echo("COURSE APPROVED - LET'S BEGIN!".center(60))
            typer.echo("=" * 60)

            # Start the course
            start_prompt = f"""
The course '{course_name}' has been approved and is now active.

1. Load the course artifacts
2. Begin teaching from the first module in the roadmap
3. Follow the teaching philosophy
4. Create a checkpoint after each milestone

Start teaching now.
"""
            teaching_response = session.send(start_prompt)
            typer.echo("\n" + teaching_response)
            break

        elif user_input.lower() == 'adjust':
            # Ask for specific adjustments
            adjust_prompt = f"""
The learner wants to adjust the roadmap for course '{course_name}'.

1. Ask what specific changes they would like to make
2. Update the artifacts accordingly
3. Present the revised roadmap
4. Ask for approval again
"""
            adjust_response = session.send(adjust_prompt)
            typer.echo("\n" + adjust_response)
        else:
            # Continue the planning conversation
            response = session.send(user_input)
            typer.echo("\n" + response)


@app.command()
def resume(course_name: str = typer.Argument(None, help="Name of the course to resume."),
           course_id: int = typer.Option(None, "--id", help="ID of the course to resume"),
           verbose: bool = typer.Option(False, "--verbose", "-v", help="Show tool calls and compression activity")):
    """
    Resumes the specified course from recent checkpoint.
    """
    from sensei.agent.session import Session
    from sensei.persistence.database import get_course
    from sensei.gateway.config import config_exists
    from sensei.validation import validate_course_name

    if not config_exists():
        typer.echo("No provider connected. Run 'sensei connect' first.")
        return

    if course_id:
        # Get course name from ID
        course = get_course(course_id=course_id)
        if not course:
            typer.echo(f"Error: Course with ID {course_id} not found")
            return
        course_name = course['name']
    elif not course_name:
        # Interactive mode: list courses and ask user to select one
        from sensei.agent.registry import get_skill
        list_courses = get_skill('list_courses')
        courses = list_courses()
        if not courses:
            typer.echo("No courses found to resume.")
            return

        typer.echo("Available courses:")
        for i, course in enumerate(courses, 1):
            typer.echo(f"{i}. {course['name']}")

        selection = typer.prompt("Enter the number of the course to resume")
        try:
            selection = int(selection) - 1
            if 0 <= selection < len(courses):
                course_name = courses[selection]['name']
            else:
                typer.echo("Invalid selection.")
                return
        except ValueError:
            typer.echo("Invalid number.")
            return
    else:
        # Validate course name if provided directly
        try:
            course_name = validate_course_name(course_name)
        except ValueError as e:
            typer.echo(f"Error: {e}")
            return

    # Create session and resume teaching
    typer.echo(f"\nResuming course: {course_name}")
    try:
        session = Session(course_name, verbose=verbose)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}")
        typer.echo("Make sure the course workspace exists. Use 'sensei list' to see available courses.")
        return
    except Exception as e:
        typer.echo(f"Error loading course: {e}")
        if verbose:
            traceback.print_exc()
        return

    resume_prompt = f"""
The course '{course_name}' is being resumed.

1. Load the current state and continue from where we left off
2. Review what was covered in the previous session
3. Continue teaching from the current module and lesson

Start teaching now.
"""
    response = session.send(resume_prompt)
    typer.echo("\n" + response)


@app.command()
def complete_course(course_id: int = typer.Argument(..., help="ID of the course to complete")):
    """
    Marks a course as completed.
    """
    from sensei.courses import complete_course

    try:
        course_info = complete_course(course_id)
        typer.echo(f"Course '{course_info['name']}' (ID: {course_info['id']}) marked as completed")
    except ValueError as e:
        typer.echo(f"Error: {e}")


@app.command()
def delete_course(course_name: str = typer.Argument(..., help="Name of the course to delete")):
    """
    Deletes an existing course and its workspace.
    """
    from sensei.agent.registry import get_skill
    from sensei.validation import validate_course_name

    try:
        course_name = validate_course_name(course_name)
    except ValueError as e:
        typer.echo(f"Error: {e}")
        return

    delete_skill = get_skill('delete_course')
    try:
        delete_skill(course_name)
        typer.echo(f"Course '{course_name}' deleted successfully.")
    except ValueError as e:
        typer.echo(f"Error: {e}")


@app.command()
def rename_course(
    old_name: str = typer.Argument(..., help="Current name of the course"),
    new_name: str = typer.Argument(..., help="New name for the course")
):
    """
    Renames an existing course.
    """
    from sensei.agent.registry import get_skill
    from sensei.validation import validate_course_name

    try:
        old_name = validate_course_name(old_name)
        new_name = validate_course_name(new_name)
    except ValueError as e:
        typer.echo(f"Error: {e}")
        return

    rename_skill = get_skill('rename_course')
    try:
        rename_skill(old_name, new_name)
        typer.echo(f"Course renamed from '{old_name}' to '{new_name}'.")
    except ValueError as e:
        typer.echo(f"Error: {e}")


@app.command("setup")
def setup_legacy():
    """
    Legacy setup command - use 'connect' instead.

    Initializes the setup from scratch.
    """
    typer.echo("Note: 'setup' is deprecated. Use 'connect' instead.\n")
    connect()


if __name__ == "__main__":
    app()
