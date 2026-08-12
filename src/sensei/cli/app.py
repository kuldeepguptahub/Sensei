import json
import typer
from typing import Optional

app = typer.Typer()

@app.command()
def help():
    """
    Displays list of available commands and their descriptions.
    """
    typer.echo("Available commands:")
    typer.echo("setup - Initializes the setup from scratch")
    typer.echo("list - Lists all available courses and their status.")
    typer.echo("start-new-course - Starts a new course.")
    typer.echo("resume - Resumes a course from recent checkpoint.")
    typer.echo("complete-course - Marks a course as completed.")
    typer.echo("delete-course - Deletes an existing course.")
    typer.echo("rename-course - Renames an existing course.")


@app.command()
def setup():
    """
    Initializes the setup from scratch.
    """
    typer.echo("Enter the provider and model details for setup:")
    endpoint_url = typer.prompt("Endpoint URL: ")
    api_key = typer.prompt("API Key: ")
    model_name = typer.prompt("Model Name: ")

    from sensei.gateway.config import save_config
    save_config(endpoint_url, api_key, model_name)


@app.command()
def list():
    """
    Lists all the available courses and their status.
    """
    from sensei.agent import list_skills
    list_courses = list_skills()['list_courses']

    courses = list_courses()
    if not courses:
        typer.echo("No courses found.")
    else:
        typer.echo("Available courses:")
        for i, course in enumerate(courses, 1):
            typer.echo(f"{i}. {course['name']}")


@app.command()
def start_new_course():
    """
    Starts a new course.
    """
    from sensei.agent import run
    from sensei.agent.registry import get_skill

    course_name = typer.prompt("Enter the name of the new course")

    # Create workspace using skill
    create_workspace = get_skill('create_workspace')
    try:
        create_workspace(course_name)
        typer.echo(f"Workspace created for course: {course_name}")
    except Exception as e:
        typer.echo(f"Error creating workspace: {e}")
        return

    # Hand control to the agent for planning
    typer.echo("\n" + "=" * 60)
    typer.echo("SENSEI COURSE PLANNING".center(60))
    typer.echo("=" * 60)
    typer.echo("\nSensei will now interview you to understand your goals")
    typer.echo("and create a personalized learning plan.\n")

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

    response = run(planning_prompt)
    typer.echo(response)

    # Continue the conversation until planning is complete
    while True:
        user_input = typer.prompt("\nYour response (or 'approve' to start, 'adjust' to modify, 'quit' to exit)")

        if user_input.lower() == 'quit':
            typer.echo("Course creation cancelled.")
            return
        elif user_input.lower() == 'approve':
            # Update course status to active
            from sensei.agent.registry import get_skill
            write_artifact = get_skill('write_artifact')

            # Read current state
            read_artifact = get_skill('read_artifact')
            state_content = read_artifact(course_name, 'state.json')
            state = json.loads(state_content)

            # Update status and save
            state['status'] = "active"
            state['current_module'] = 0
            state['current_lesson'] = 0
            state['progress'] = 0.0

            write_artifact(course_name, 'state.json', json.dumps(state, indent=2))

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
            teaching_response = run(start_prompt)
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
            adjust_response = run(adjust_prompt)
            typer.echo("\n" + adjust_response)
        else:
            # Continue the planning conversation
            response = run(user_input)
            typer.echo("\n" + response)


@app.command()
def resume(course_name: str = typer.Argument(None, help="Name of the course to resume."),
           course_id: int = typer.Option(None, "--id", help="ID of the course to resume")):
    """
    Resumes the specified course from recent checkpoint.
    """
    from sensei.agent import run
    from sensei.persistence.database import get_course

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

    # Hand control to the agent for resuming
    typer.echo(f"\nResuming course: {course_name}")
    response = run(f"Resume the course '{course_name}'. Load the current state and continue teaching from where we left off.")
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

    rename_skill = get_skill('rename_course')
    try:
        rename_skill(old_name, new_name)
        typer.echo(f"Course renamed from '{old_name}' to '{new_name}'.")
    except ValueError as e:
        typer.echo(f"Error: {e}")


if __name__ == "__main__":
    app()