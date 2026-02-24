from django.shortcuts import render, get_object_or_404
from .models import Board, Project

def index(request):
    projects = Project.objects.all()
    return render(request, 'kanban_app/project_list.html', {'projects': projects})

def project_board(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Ensure a board exists for this project
    if not hasattr(project, 'board'):
        board = Board.objects.create(project=project, name=f"{project.name} Board")
        from .models import Column
        Column.objects.create(board=board, name="To Do", order=0)
        Column.objects.create(board=board, name="In Progress", order=1)
        Column.objects.create(board=board, name="Done", order=2)
    else:
        board = project.board
        
    return render(request, 'kanban_app/board.html', {'board': board, 'project': project})
