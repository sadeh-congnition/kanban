import django
from django.conf import settings
settings.configure(TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': []}])
django.setup()
from django.template import Template

with open('templates/kanban_app/partials/task_details.html', 'r') as f:
    text = f.read()

try:
    Template(text)
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
