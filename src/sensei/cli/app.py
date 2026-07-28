import typer

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
    from sensei.persistence.database import list_courses, initialize_database
    initialize_database()
    courses = list_courses()
    if not courses:
        typer.echo("No courses found.")
    else:
        typer.echo("Available courses:")
        for course in courses:
            typer.echo(f"ID: {course[0]}, Name: {course[1]}, Status: {course[2]}, Created At: {course[3]}, Last Accessed at: {course[4]}")


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
def start_new_course():
    """
    Starts a new course.
    """
    from sensei.courses import create_new_course

    course_name = typer.prompt("Enter the name of the new course")

    try:
        course_id = create_new_course(course_name)
        typer.echo(f"Course '{course_name}' created successfully with ID: {course_id}")
    except ValueError as e:
        typer.echo(f"Error: {e}")

@app.command()
def resume(course_name: str = typer.Argument(None, help="Name of the course to resume. Use list command to see available courses. If not specified, resumes the last course from recent checkpoint."),
           course_id: int = typer.Option(None, "--id", help="ID of the course to resume")):
    """
    Resumes the specified course from recent checkpoint.
    """
    from sensei.courses import resume_course

    try:
        if course_id:
            course_info = resume_course(course_id=course_id)
        elif course_name:
            course_info = resume_course(course_name=course_name)
        else:
            # Resume the most recently accessed course
            from sensei.persistence.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id, name FROM courses ORDER BY last_accessed DESC LIMIT 1')
            recent_course = cursor.fetchone()

            if recent_course:
                course_info = resume_course(course_id=recent_course[0])
            else:
                typer.echo("No courses found to resume.")
                return

        typer.echo(f"Resumed course: {course_info['name']} (ID: {course_info['id']})")
    except ValueError as e:
        typer.echo(f"Error: {e}")
    
    
if __name__ == "__main__":
    app()

