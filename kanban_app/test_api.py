import pytest
from django.test import Client
from model_bakery import baker
from kanban_app.models import Project, Board, Column, Task, Tag, TaskAssignmentHistory
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def api_client():
    return Client()


@pytest.mark.django_db
def test_get_project_form(api_client):
    response = api_client.get("/api/projects/form")
    assert response.status_code == 200


@pytest.mark.django_db
def test_create_project(api_client):
    response = api_client.post("/api/projects", {"name": "New Project"})
    assert response.status_code == 200
    assert response.headers.get(
        "HX-Trigger") == "projectListUpdated, closeModal"
    assert Project.objects.filter(name="New Project").exists()


@pytest.mark.django_db
def test_get_projects_list(api_client):
    baker.make(Project, name="P1")
    baker.make(Project, name="P2")
    response = api_client.get("/api/projects/list")
    assert response.status_code == 200
    assert b"P1" in response.content
    assert b"P2" in response.content


@pytest.mark.django_db
def test_delete_project(api_client):
    project = baker.make(Project)
    response = api_client.delete(f"/api/projects/{project.id}")
    assert response.status_code == 200
    assert response.headers.get("HX-Trigger") == "projectListUpdated"
    project.refresh_from_db()
    assert project.is_deleted is True


@pytest.mark.django_db
def test_get_project_tags(api_client):
    project = baker.make(Project)
    baker.make(Tag, project=project, name="Bug")
    response = api_client.get(f"/api/projects/{project.id}/tags")
    assert response.status_code == 200
    assert b"Bug" in response.content


@pytest.mark.django_db
def test_delete_tag(api_client):
    tag = baker.make(Tag)
    response = api_client.delete(f"/api/tags/{tag.id}")
    assert response.status_code == 200
    assert response.headers.get("HX-Trigger") == "tagsUpdated, columnUpdated"
    assert not Tag.objects.filter(id=tag.id).exists()


@pytest.mark.django_db
def test_get_board_columns(api_client):
    board = baker.make(Board)
    baker.make(Column, board=board, name="To Do")
    response = api_client.get(f"/api/boards/{board.id}/columns")
    assert response.status_code == 200
    assert b"To Do" in response.content


@pytest.mark.django_db
def test_get_board_columns_form(api_client):
    board = baker.make(Board)
    response = api_client.get(f"/api/boards/{board.id}/columns/form")
    assert response.status_code == 200


@pytest.mark.django_db
def test_create_column(api_client):
    board = baker.make(Board)
    response = api_client.post(
        f"/api/boards/{board.id}/columns", {"name": "In Progress"})
    assert response.status_code == 200
    assert response.headers.get("HX-Trigger") == "columnUpdated, closeModal"
    assert Column.objects.filter(board=board, name="In Progress").exists()


@pytest.mark.django_db
def test_delete_column(api_client):
    col = baker.make(Column, order=0)
    response = api_client.delete(f"/api/columns/{col.id}")
    assert response.status_code == 200
    assert response.headers.get("HX-Trigger") == "columnUpdated"
    assert not Column.objects.filter(id=col.id).exists()


@pytest.mark.django_db
def test_move_column(api_client):
    board = baker.make(Board)
    col1 = baker.make(Column, board=board, order=0)
    col2 = baker.make(Column, board=board, order=1)
    col3 = baker.make(Column, board=board, order=2)
    response = api_client.post(
        f"/api/columns/{col3.id}/move", {"new_order": 0})
    if response.status_code != 204:
        print(response.content)
    assert response.status_code == 204
    col1.refresh_from_db()
    col2.refresh_from_db()
    col3.refresh_from_db()
    assert col3.order == 0
    assert col1.order == 1
    assert col2.order == 2


@pytest.mark.django_db
def test_get_column_tasks_form(api_client):
    project = baker.make(Project)
    board = baker.make(Board, project=project)
    col = baker.make(Column, board=board)
    response = api_client.get(f"/api/columns/{col.id}/tasks/form")
    assert response.status_code == 200


@pytest.mark.django_db
def test_delete_task(api_client):
    task = baker.make(Task, order=0)
    response = api_client.delete(f"/api/tasks/{task.id}")
    assert response.status_code == 200
    assert response.headers.get("HX-Trigger") == "columnUpdated"
    assert not Task.objects.filter(id=task.id).exists()


@pytest.mark.django_db
def test_get_task_tags_form(api_client):
    project = baker.make(Project)
    board = baker.make(Board, project=project)
    col = baker.make(Column, board=board)
    task = baker.make(Task, column=col)
    response = api_client.get(f"/api/tasks/{task.id}/tags/form")
    assert response.status_code == 200


@pytest.mark.django_db
def test_update_task_tags(api_client):
    project = baker.make(Project)
    board = baker.make(Board, project=project)
    col = baker.make(Column, board=board, order=0)
    task = baker.make(Task, column=col, order=0)
    tag1 = baker.make(Tag, project=project)
    tag2 = baker.make(Tag, project=project)

    response = api_client.post(
        f"/api/tasks/{task.id}/tags", {"tags": [tag1.id, tag2.id]})
    if response.status_code != 200:
        print(response.content)
    assert response.status_code == 200
    assert response.headers.get("HX-Trigger") == "columnUpdated, closeModal"
    assert task.tags.count() == 2


@pytest.mark.django_db
def test_task_assignment(api_client):
    project = baker.make(Project)
    board = baker.make(Board, project=project)
    col = baker.make(Column, board=board, order=0)
    task = baker.make(Task, column=col, order=0)
    user1 = baker.make(User)
    user2 = baker.make(User)

    # Assign to user1
    response = api_client.post(
        f"/api/tasks/{task.id}/assign", {"user_id": str(user1.id)})
    assert response.status_code == 200
    task.refresh_from_db()
    assert task.assigned_to == user1
    assert TaskAssignmentHistory.objects.filter(task=task, old_assignee=None, new_assignee=user1).exists()

    # Re-assign to user2
    response = api_client.post(
        f"/api/tasks/{task.id}/assign", {"user_id": str(user2.id)})
    assert response.status_code == 200
    task.refresh_from_db()
    assert task.assigned_to == user2
    assert TaskAssignmentHistory.objects.filter(task=task, old_assignee=user1, new_assignee=user2).exists()

    # Unassign
    response = api_client.post(f"/api/tasks/{task.id}/assign", {})
    assert response.status_code == 200
    task.refresh_from_db()
    assert task.assigned_to is None
    assert TaskAssignmentHistory.objects.filter(task=task, old_assignee=user2, new_assignee=None).exists()


@pytest.mark.django_db
def test_get_task_details_form(api_client):
    project = baker.make(Project)
    board = baker.make(Board, project=project)
    col = baker.make(Column, board=board)
    task = baker.make(Task, column=col, title="My Task Details")
    response = api_client.get(f"/api/tasks/{task.id}/details")
    assert response.status_code == 200
    assert b"My Task Details" in response.content


@pytest.mark.django_db
def test_update_task_details(api_client):
    project = baker.make(Project)
    board = baker.make(Board, project=project)
    col = baker.make(Column, board=board)
    task = baker.make(Task, column=col, title="Old Title", description="Old Description")

    response = api_client.post(f"/api/tasks/{task.id}/update_details", {
        "title": "New Title",
        "description": "New Description"
    })

    assert response.status_code == 200
    assert response.headers.get("HX-Trigger") == "columnUpdated"
    task.refresh_from_db()
    assert task.title == "New Title"
    assert task.description == "New Description"
