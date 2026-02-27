import djclick as click
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, IntPrompt
from kanban_app.models import Project, Board, Task
import sys

console = Console()


def display_projects():
    projects = Project.objects.all()
    if not projects.exists():
        console.print("[yellow]No projects found.[/yellow]")
        return None

    table = Table(title="Available Projects")
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")

    for project in projects:
        table.add_row(str(project.id), project.name)

    console.print(table)
    return projects


def select_project():
    projects = display_projects()
    if not projects:
        return None

    while True:
        project_id = IntPrompt.ask("Enter the Project ID to select")
        try:
            return Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            console.print(
                f"[red]Project with ID {project_id} does not exist. "
                "Please try again.[/red]"
            )


def display_board(project: Project):
    try:
        board = project.board
    except Board.DoesNotExist:
        console.print(
            f"[yellow]No board found for project '{project.name}'.[/yellow]"
        )
        return None

    if not board:
        console.print(
            f"[yellow]No board found for project '{project.name}'.[/yellow]"
        )
        return None

    table = Table(title=f"Board: {board.name}")
    columns = list(board.columns.all())

    if not columns:
        console.print(
            f"[yellow]No columns found in board '{board.name}'.[/yellow]"
        )
        return board

    for column in columns:
        table.add_column(column.name)

    # We need to render tasks row by row
    # Determine the maximum number of tasks in any column
    max_tasks = 0
    column_tasks = []
    for column in columns:
        tasks = list(column.tasks.all())
        column_tasks.append(tasks)
        max_tasks = max(max_tasks, len(tasks))

    for row_idx in range(max_tasks):
        row_data = []
        for col_idx in range(len(columns)):
            tasks = column_tasks[col_idx]
            if row_idx < len(tasks):
                task = tasks[row_idx]
                tag_names = ", ".join(t.name for t in task.tags.all())
                tags_str = f" [[yellow]{tag_names}[/yellow]]" if tag_names else ""
                task_str = (
                    f"[cyan]#{task.project_task_id}[/cyan]: {task.title}{tags_str}"
                )
                row_data.append(task_str)
            else:
                row_data.append("")
        table.add_row(*row_data)

    console.print(table)
    return board


def create_task(board: Board, project: Project):
    columns = list(board.columns.all())
    if not columns:
        console.print(
            "[red]Cannot create a task because there are no columns.[/red]"
        )
        return

    title = Prompt.ask("Enter task title")
    description = Prompt.ask("Enter task description (optional)", default="")

    tags = list(project.tags.all())
    selected_tags = []
    if tags:
        console.print("Available Tags:")
        for idx, tag in enumerate(tags, start=1):
            console.print(f"{idx}. {tag.name}")

        tag_choices = Prompt.ask(
            "Enter tag numbers to assign (comma-separated), or leave blank",
            default="")
        if tag_choices:
            for part in tag_choices.split(","):
                part = part.strip()
                if part.isdigit():
                    t_idx = int(part)
                    if 1 <= t_idx <= len(tags):
                        selected_tags.append(tags[t_idx - 1])

    console.print("Available Columns:")
    for idx, col in enumerate(columns, start=1):
        console.print(f"{idx}. {col.name}")

    while True:
        col_choice = IntPrompt.ask("Select column number")
        if 1 <= col_choice <= len(columns):
            selected_column = columns[col_choice - 1]
            break
        console.print("[red]Invalid selection.[/red]")

    # Assuming project provides project_task_id
    project_task_id = project.next_task_id
    project.next_task_id += 1
    project.save(update_fields=["next_task_id"])

    task = Task.objects.create(
        column=selected_column,
        title=title,
        description=description,
        project_task_id=project_task_id,
        # Put it at the end of the column
        order=selected_column.tasks.count(),
    )
    if selected_tags:
        task.tags.set(selected_tags)

    console.print(f"[green]Task '{title}' created successfully![/green]")


def change_task_status(board: Board):
    columns = list(board.columns.all())
    if not columns:
        console.print("[red]No columns available.[/red]")
        return

    project_task_id = IntPrompt.ask(
        "Enter the Task ID (project local ID) to move"
    )

    try:
        # Need to find the task by project_task_id within this board's columns
        task = Task.objects.get(
            column__board=board, project_task_id=project_task_id
        )
    except Task.DoesNotExist:
        console.print(
            f"[red]Task #{project_task_id} not found on this board.[/red]"
        )
        return

    console.print(
        f"Moving Task: [cyan]#{task.project_task_id}[/cyan]: {task.title}"
    )
    console.print(f"Current Column: [magenta]{task.column.name}[/magenta]")

    console.print("Available Columns:")
    for idx, col in enumerate(columns, start=1):
        console.print(f"{idx}. {col.name}")

    while True:
        col_choice = IntPrompt.ask("Select new column number")
        if 1 <= col_choice <= len(columns):
            new_column = columns[col_choice - 1]
            break
        console.print("[red]Invalid selection.[/red]")

    if task.column == new_column:
        console.print("[yellow]Task is already in that column.[/yellow]")
        return

    task.column = new_column
    task.order = new_column.tasks.count()  # append to the end
    task.save()
    console.print("[green]Task moved successfully![/green]")


@click.command()
def command():
    """Manage Kanban boards using a rich interactive CLI."""
    console.print("[bold cyan]Welcome to the Kanban CLI[/bold cyan] 📋")

    project = select_project()
    if not project:
        sys.exit(0)

    while True:
        board = display_board(project)
        if not board:
            console.print("[red]Board missing. Exiting...[/red]")
            sys.exit(1)

        console.print("\n[bold]Options:[/bold]")
        console.print("1. Create Task")
        console.print("2. Move Task (Change Status)")
        console.print("3. Switch Project")
        console.print("4. Quit")

        choice = Prompt.ask(
            "Choose an action",
            choices=["1", "2", "3", "4"],
            show_choices=False,
        )

        console.print("\n")

        if choice == "1":
            create_task(board, project)
        elif choice == "2":
            change_task_status(board)
        elif choice == "3":
            project = select_project()
            if not project:
                sys.exit(0)
        elif choice == "4":
            console.print("Goodbye! 👋")
            sys.exit(0)
