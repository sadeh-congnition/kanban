from ninja import NinjaAPI, Form, Schema
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import Board, Column, Task, Project, Tag, TaskStatusHistory, TaskAssignmentHistory

User = get_user_model()

api = NinjaAPI(title="Kanban API", description="API for HTMX Operations")

# --- Project Endpoints ---


@api.get("/projects/form")
def get_project_form(request):
    """Returns the form modal for creating a new project"""
    return render(request, "kanban_app/partials/project_form.html")


class ProjectFormSchema(Schema):
    name: str


@api.post("/projects")
def create_project(request, data: Form[ProjectFormSchema]):
    """Creates a new project"""
    Project.objects.create(name=data.name)
    response = HttpResponse()
    response['HX-Trigger'] = 'projectListUpdated, closeModal'
    return response


@api.get("/projects/list")
def get_projects_list(request):
    """Returns the updated list of projects"""
    projects = Project.objects.all()
    return render(request,
                  "kanban_app/partials/projects.html",
                  {"projects": projects})


@api.delete("/projects/{project_id}")
def delete_project(request, project_id: int):
    """Deletes a project"""
    project = get_object_or_404(Project, id=project_id)
    project.delete()

    response = HttpResponse()
    # Trigger HTMX to reload the projects list
    response['HX-Trigger'] = 'projectListUpdated'
    return response

# --- Tag Endpoints ---


@api.get("/projects/{project_id}/tags")
def get_project_tags(request, project_id: int):
    """Returns the tags partial for a project"""
    project = get_object_or_404(Project, id=project_id)
    tags = project.tags.all()
    return render(request, "kanban_app/partials/tags.html",
                  {"project": project, "tags": tags})


class TagFormSchema(Schema):
    name: str
    color: str = "#3b82f6"


@api.post("/projects/{project_id}/tags")
def create_tag(request, project_id: int, data: Form[TagFormSchema]):
    """Creates a new tag for the project"""
    project = get_object_or_404(Project, id=project_id)
    Tag.objects.create(project=project, name=data.name, color=data.color)

    response = HttpResponse()
    response['HX-Trigger'] = 'tagsUpdated'
    return response


@api.delete("/tags/{tag_id}")
def delete_tag(request, tag_id: int):
    """Deletes a tag"""
    tag = get_object_or_404(Tag, id=tag_id)
    tag.delete()

    response = HttpResponse()
    response['HX-Trigger'] = 'tagsUpdated, columnUpdated'
    return response

# --- Column Endpoints ---


@api.get("/boards/{board_id}/columns")
def get_columns(request, board_id: int):
    """Returns the HTML for all columns in the board"""
    board = get_object_or_404(Board, id=board_id)
    columns = board.columns.all()
    return render(request,
                  "kanban_app/partials/columns.html",
                  {"columns": columns})


@api.get("/boards/{board_id}/columns/form")
def get_column_form(request, board_id: int):
    """Returns the form modal for creating a new column"""
    return render(request,
                  "kanban_app/partials/column_form.html",
                  {"board_id": board_id})


class ColumnFormSchema(Schema):
    name: str


@api.post("/boards/{board_id}/columns")
def create_column(request, board_id: int, data: Form[ColumnFormSchema]):
    """Creates a new column and triggers fetching columns"""
    board = get_object_or_404(Board, id=board_id)

    # Get highest order
    last_col = board.columns.last()
    order = (last_col.order + 1) if last_col else 0

    Column.objects.create(board=board, name=data.name, order=order)

    response = HttpResponse()
    # Trigger HTMX to reload the body, and close the modal
    response['HX-Trigger'] = 'columnUpdated, closeModal'
    return response


@api.delete("/columns/{column_id}")
def delete_column(request, column_id: int):
    """Deletes a column"""
    column = get_object_or_404(Column, id=column_id)
    column.delete()

    response = HttpResponse()
    # Trigger HTMX to reload the body
    response['HX-Trigger'] = 'columnUpdated'
    return response


class MoveColumnSchema(Schema):
    new_order: int


@api.post("/columns/{column_id}/move")
def move_column(request, column_id: int, data: Form[MoveColumnSchema]):
    """Moves a column to a new order"""
    column = get_object_or_404(Column, id=column_id)
    board = column.board
    new_order = data.new_order

    columns = list(board.columns.exclude(id=column.id))
    # Insert at new position
    columns.insert(new_order, column)

    # Update orders
    for index, col in enumerate(columns):
        col.order = index
        col.save()

    return HttpResponse(status=204)  # No Content, Sortable handles UI

# --- Task Endpoints ---


@api.get("/columns/{column_id}/tasks/form")
def get_task_form(request, column_id: int):
    """Returns the form modal for creating a new task in a specific column"""
    column = get_object_or_404(Column, id=column_id)
    tags = column.board.project.tags.all()
    return render(request, "kanban_app/partials/task_form.html",
                  {"column_id": column_id, "tags": tags})


class TaskFormSchema(Schema):
    title: str
    description: str = ""
    tags: list[int] = []


@api.post("/columns/{column_id}/tasks")
def create_task(request, column_id: int, data: Form[TaskFormSchema]):
    """Creates a new task in the given column"""
    column = get_object_or_404(Column, id=column_id)

    # Wrap in transaction to safely generate sequential ID
    with transaction.atomic():
        # Get the project for this column's board, locking the row to prevent
        # race conditions
        project = Project.objects.select_for_update().get(board=column.board)

        # Get highest order
        last_task = column.tasks.last()
        order = (last_task.order + 1) if last_task else 0

        # Determine the project-specific ID
        task_id = project.next_task_id

        task = Task.objects.create(
            column=column,
            title=data.title,
            description=data.description,
            order=order,
            project_task_id=task_id
        )

        TaskStatusHistory.objects.create(
            task=task,
            new_column=column
        )

        if data.tags:
            task.tags.set(data.tags)

        # Increment project counter
        project.next_task_id += 1
        project.save()

    response = HttpResponse()
    # Trigger HTMX to reload the board
    response['HX-Trigger'] = 'columnUpdated, closeModal'
    return response


@api.delete("/tasks/{task_id}")
def delete_task(request, task_id: int):
    """Deletes a task"""
    task = get_object_or_404(Task, id=task_id)
    task.delete()

    response = HttpResponse()
    response['HX-Trigger'] = 'columnUpdated'
    return response


@api.get("/tasks/{task_id}/tags/form")
def get_task_tags_form(request, task_id: int):
    """Returns the form modal for managing tags for a specific task"""
    task = get_object_or_404(Task, id=task_id)
    project = task.column.board.project
    tags = project.tags.all()
    # We need to pass the IDs of the currently assigned tags
    task_tag_ids = list(task.tags.values_list('id', flat=True))
    return render(request, "kanban_app/partials/task_tags_form.html", {
        "task": task,
        "tags": tags,
        "task_tag_ids": task_tag_ids
    })


class TaskTagsFormSchema(Schema):
    tags: list[int] = []


@api.post("/tasks/{task_id}/tags")
def update_task_tags(request, task_id: int, data: Form[TaskTagsFormSchema]):
    """Updates the tags for a task"""
    task = get_object_or_404(Task, id=task_id)
    task.tags.set(data.tags)

    response = HttpResponse()
    # Trigger HTMX to reload the board and close the modal
    response['HX-Trigger'] = 'columnUpdated, closeModal'
    return response


class MoveTaskSchema(Schema):
    new_column_id: int
    new_order: int


@api.post("/tasks/{task_id}/move")
def move_task(request, task_id: int, data: Form[MoveTaskSchema]):
    """Moves a task between columns or to a new order"""
    task = get_object_or_404(Task, id=task_id)
    new_col = get_object_or_404(Column, id=data.new_column_id)
    new_order = data.new_order

    # Same column movement
    if task.column_id == new_col.id:
        tasks = list(new_col.tasks.exclude(id=task.id))
        tasks.insert(new_order, task)
        for idx, t in enumerate(tasks):
            t.order = idx
            t.save()
    else:
        old_col = task.column
        # Change column
        if task.assigned_to_id is None:
            return HttpResponse("Unassigned tasks cannot change status.", status=400)

        task.column = new_col
        task.save()

        TaskStatusHistory.objects.create(
            task=task,
            old_column=old_col,
            new_column=new_col
        )

        # Insert in new column
        tasks = list(new_col.tasks.exclude(id=task.id))
        tasks.insert(new_order, task)
        for idx, t in enumerate(tasks):
            t.order = idx
            t.save()

    return HttpResponse(status=204)


@api.get("/tasks/{task_id}/details")
def get_task_details(request, task_id: int):
    """Returns the details view for a task."""
    task = get_object_or_404(Task, id=task_id)
    project = task.column.board.project
    tags = project.tags.all()
    # We need to pass the IDs of the currently assigned tags
    task_tag_ids = list(task.tags.values_list('id', flat=True))
    users = User.objects.all()

    return render(request, "kanban_app/partials/task_details.html", {
        "task": task,
        "tags": tags,
        "task_tag_ids": task_tag_ids,
        "users": users
    })


class TaskUpdateDetailsSchema(Schema):
    title: str
    description: str = ""


@api.post("/tasks/{task_id}/update_details")
def update_task_details(request, task_id: int, data: Form[TaskUpdateDetailsSchema]):
    """Updates the details for a task"""
    task = get_object_or_404(Task, id=task_id)
    task.title = data.title
    task.description = data.description
    task.save()

    response = HttpResponse()
    # Trigger HTMX to reload the board
    response['HX-Trigger'] = 'columnUpdated'
    return response

# --- Assignment Endpoints ---


@api.get("/tasks/{task_id}/assign/form")
def get_task_assign_form(request, task_id: int):
    """Returns the form modal for assigning a user to a task"""
    task = get_object_or_404(Task, id=task_id)
    users = User.objects.all()
    return render(request, "kanban_app/partials/task_assign_form.html", {
        "task": task,
        "users": users
    })


class TaskAssignFormSchema(Schema):
    user_id: str | None = None


@api.post("/tasks/{task_id}/assign")
def assign_task(request, task_id: int, data: Form[TaskAssignFormSchema]):
    """Assigns a task to a user"""
    task = get_object_or_404(Task, id=task_id)

    old_assignee_id = task.assigned_to_id
    new_assignee_id = int(data.user_id) if data.user_id else None

    if old_assignee_id != new_assignee_id:
        task.assigned_to_id = new_assignee_id
        task.save()

        TaskAssignmentHistory.objects.create(
            task=task,
            old_assignee_id=old_assignee_id,
            new_assignee_id=new_assignee_id
        )

    response = HttpResponse()
    # Trigger HTMX to reload the board and close the modal
    response['HX-Trigger'] = 'columnUpdated, closeModal'
    return response
