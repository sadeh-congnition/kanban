# Kanban App

This is an app to replace the Github project/board features because they're hard and confusing to use. My goal is to use this app for tracking projects in Sadeh Cognition.

All the tasks are tracked using Kanban which is hosted [here](https://github.com/sadeh-congnition/kanban).
To see the board follow the instructions below. In short, you'll need to clone the repo and run it locally. The database is included in the repo and I'm keeping it up to date.

## Prerequisites

- [uv](https://github.com/astral-sh/uv) must be installed for managing Python environment and dependencies.
- Python >= 3.14 (managed by `uv`).

## Setup Instructions

1. **Clone the repository** (if you haven't already) and navigate to the project directory:

   ```bash
   cd kanban
   ```

2. **Install dependencies** using `uv`. This will automatically create a virtual environment in the `.venv` directory and install required packages:

   ```bash
   uv sync
   ```

3. **Run database migrations**. Django requires a database to store models (using SQLite by default):

   ```bash
   uv run python manage.py migrate
   ```

4. **Create a superuser** (Optional, to access the Django Admin at `/admin/`):

   ```bash
   uv run python manage.py createsuperuser
   ```

5. **Start the development server**:

   ```bash
   uv run python manage.py runserver
   ```

   The application will be accessible at: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Running Tests

To run the test suite (using `pytest` and `pytest-django`), use the following command:

```bash
uv run pytest
```

## Technologies Used

- **Django**: Backend web framework
- **django-ninja**: Building the HTTP API
- **HTMX**: Frontend interactivity and network calls
- **SQLite**: Local database
- **uv**: Package and environment management
