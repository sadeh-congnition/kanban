from ninja import NinjaAPI, Form, Schema
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseNotAllowed
from .models import Board, Column, Task, Project

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
    return render(request, "kanban_app/partials/projects.html", {"projects": projects})

@api.delete("/projects/{project_id}")
def delete_project(request, project_id: int):
    """Deletes a project"""
    project = get_object_or_404(Project, id=project_id)
    project.delete()
    
    response = HttpResponse()
    # Trigger HTMX to reload the projects list
    response['HX-Trigger'] = 'projectListUpdated'
    return response

# --- Column Endpoints ---

@api.get("/boards/{board_id}/columns")
def get_columns(request, board_id: int):
    """Returns the HTML for all columns in the board"""
    board = get_object_or_404(Board, id=board_id)
    columns = board.columns.all()
    return render(request, "kanban_app/partials/columns.html", {"columns": columns})

@api.get("/boards/{board_id}/columns/form")
def get_column_form(request, board_id: int):
    """Returns the form modal for creating a new column"""
    return render(request, "kanban_app/partials/column_form.html", {"board_id": board_id})

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

@api.patch("/columns/{column_id}/move")
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
        
    return HttpResponse(status=204) # No Content, Sortable handles UI

# --- Task Endpoints ---

@api.get("/columns/{column_id}/tasks/form")
def get_task_form(request, column_id: int):
    """Returns the form modal for creating a new task in a specific column"""
    return render(request, "kanban_app/partials/task_form.html", {"column_id": column_id})

class TaskFormSchema(Schema):
    title: str
    description: str = ""

@api.post("/columns/{column_id}/tasks")
def create_task(request, column_id: int, data: Form[TaskFormSchema]):
    """Creates a new task in the given column"""
    column = get_object_or_404(Column, id=column_id)
    
    # Get highest order
    last_task = column.tasks.last()
    order = (last_task.order + 1) if last_task else 0
    
    Task.objects.create(
        column=column, 
        title=data.title, 
        description=data.description, 
        order=order
    )
    
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

class MoveTaskSchema(Schema):
    new_column_id: int
    new_order: int

@api.patch("/tasks/{task_id}/move")
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
        # Change column
        task.column = new_col
        task.save()
        
        # Insert in new column
        tasks = list(new_col.tasks.exclude(id=task.id))
        tasks.insert(new_order, task)
        for idx, t in enumerate(tasks):
            t.order = idx
            t.save()
            
    return HttpResponse(status=204)
