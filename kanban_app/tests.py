from django.test import TestCase, Client
from kanban_app.models import Project, Board, Column, Task

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
