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
        for courses in courses:
            typer.echo(f"ID: {courses[0]}, Name: {courses[1]}, Status: {courses[2]}, Created At: {courses[3]}, Last Accessed at: {courses[4]}")
            
    

@app.command()
def start_new_course():
    """
    Starts a new course.
    """
    typer.echo("Not yet implemented")

@app.command()
def resume(course_name: str = typer.Argument(None, help="Name of the course to resume. Use list command to see available courses. If not specified, resumes the last course from recent checkpoint.")):
    """
    Resumes the specified course from recent checkpoint.
    """
    typer.echo("Not yet implemented")
    
    
if __name__ == "__main__":
    app()

