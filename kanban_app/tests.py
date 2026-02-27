from django.test import TestCase, Client
from kanban_app.models import Project, Board, Column, Task, Tag

class TaskMoveTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Test Project")
        self.board = Board.objects.create(project=self.project, name="Test Board")
        self.col1 = Column.objects.create(board=self.board, name="To Do", order=0)
        self.col2 = Column.objects.create(board=self.board, name="In Progress", order=1)
        self.task1 = Task.objects.create(column=self.col1, title="Task 1", order=0)

    def test_move_task_different_column(self):
        c = Client()
        # Simulate HTMX POST request
        response = c.post(f"/api/tasks/{self.task1.id}/move", {"new_column_id": self.col2.id, "new_order": 0})
        if response.status_code != 204:
            print("Validation error:", response.content)
        self.assertEqual(response.status_code, 204)
        
        # Verify db update
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.column_id, self.col2.id)

    def test_project_task_id_assignment(self):
        c = Client()
        # Create first task for project
        response = c.post(f"/api/columns/{self.col1.id}/tasks", {"title": "Task 1", "description": "test"})
        self.assertEqual(response.status_code, 200)
        
        # Create second task for project
        response = c.post(f"/api/columns/{self.col1.id}/tasks", {"title": "Task 2", "description": "test"})
        self.assertEqual(response.status_code, 200)
        
        # Create another project to check isolation
        p2 = Project.objects.create(name="Project 2")
        b2 = Board.objects.create(project=p2, name="Board 2")
        c2 = Column.objects.create(board=b2, name="To Do", order=0)
        
        response = c.post(f"/api/columns/{c2.id}/tasks", {"title": "Task 1 for P2", "description": "test"})
        self.assertEqual(response.status_code, 200)

        tasks_p1 = Task.objects.filter(column__board__project=self.project).order_by('id')
        self.assertEqual(tasks_p1.count(), 3) # self.task1 + two new
        
        # Note: self.task1 doesn't have a project_task_id yet because it was created via ORM without setting it
        new_task_1 = tasks_p1[1]
        new_task_2 = tasks_p1[2]
        self.assertEqual(new_task_1.project_task_id, 1)
        self.assertEqual(new_task_2.project_task_id, 2)
        
        task_p2 = Task.objects.get(column__board__project=p2)
        self.assertEqual(task_p2.project_task_id, 1)

class TagTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Tag Project")
        self.board = Board.objects.create(project=self.project, name="Tag Board")
        self.col = Column.objects.create(board=self.board, name="To Do", order=0)

    def test_tag_creation_and_assignment(self):
        tag1 = Tag.objects.create(project=self.project, name="Bug", color="#ff0000")
        tag2 = Tag.objects.create(project=self.project, name="Feature", color="#00ff00")
        
        task = Task.objects.create(column=self.col, title="Fix login", order=0, project_task_id=1)
        task.tags.set([tag1, tag2])
        
        task.refresh_from_db()
        self.assertEqual(task.tags.count(), 2)
        self.assertIn(tag1, task.tags.all())
        self.assertIn(tag2, task.tags.all())

    def test_api_create_tag(self):
        c = Client()
        response = c.post(f"/api/projects/{self.project.id}/tags", {"name": "Urgent", "color": "#ff0000"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Tag.objects.filter(project=self.project).count(), 1)
        tag = Tag.objects.get(project=self.project)
        self.assertEqual(tag.name, "Urgent")
        
    def test_api_create_task_with_tags(self):
        tag = Tag.objects.create(project=self.project, name="Backend")
        c = Client()
        response = c.post(f"/api/columns/{self.col.id}/tasks", {"title": "API rework", "description": "", "tags": tag.id})
        self.assertEqual(response.status_code, 200)
        task = Task.objects.get(title="API rework")
        self.assertEqual(task.tags.count(), 1)
        self.assertEqual(task.tags.first(), tag)
