from django.contrib import admin
from .models import Board, Column, Task, Project, Tag


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'updated_at')
    search_fields = ('name',)


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'name', 'created_at', 'updated_at')
    search_fields = ('name',)
    list_filter = ('project',)


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'board', 'order', 'created_at', 'updated_at')
    list_filter = ('board',)
    search_fields = ('name',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'column',
        'order',
        'get_tags',
        'created_at',
        'updated_at')
    list_filter = ('column__board', 'column')
    search_fields = ('title', 'description')

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('tags')

    @admin.display(description='Tags')
    def get_tags(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'project')
    list_filter = ('project',)
    search_fields = ('name',)
