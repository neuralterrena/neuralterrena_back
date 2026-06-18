# Repository Guidelines

## Project Structure & Module Organization
`neuralterrena/` contains the Django app code, including `users/`, reusable `contrib/` modules, `templates/`, and `static/`. Project configuration lives in `config/`, with environment-specific settings under `config/settings/{local,test,production}.py`. Tests are split between top-level checks in `tests/` and app-local suites such as `neuralterrena/users/tests/`. Deployment and local container scripts live in `compose/`, and Sphinx docs live in `docs/`.

## Build, Test, and Development Commands
Use `uv` for local Python workflows.

- `uv sync --dev`: install runtime and development dependencies into the local environment.
- `uv run python manage.py runserver`: start the Django dev server.
- `uv run pytest`: run the full test suite with `config.settings.test`.
- `uv run coverage run -m pytest && uv run coverage html`: generate a coverage report in `htmlcov/`.
- `uv run mypy neuralterrena`: run static type checks.
- `uv run ruff check .`: lint Python code.
- `uv run djlint neuralterrena/templates --check`: lint Django templates.

## Coding Style & Naming Conventions
Follow `.editorconfig`: 4 spaces for Python, 2 spaces for HTML/CSS/JSON/YAML/TOML, LF line endings, and UTF-8. Keep Python modules and functions `snake_case`, classes `PascalCase`, and Django apps lowercase. Ruff enforces import ordering with single-line imports; avoid manual formatting that fights the linter. For templates, use `djlint` formatting rules and keep lines within the configured 119-character limit where practical.

## Testing Guidelines
Write tests with `pytest` and `pytest-django`. Name files `test_*.py` or `tests.py`, matching the existing pattern in `neuralterrena/users/tests/` and `tests/`. Prefer app-local tests for model, view, and API behavior, and keep shared or project-wide checks in top-level `tests/`. Run `uv run pytest --reuse-db` for normal development and generate coverage before larger changes.

## Commit & Pull Request Guidelines
Recent history uses Conventional Commit style such as `chore: ...`; keep that format (`feat:`, `fix:`, `chore:`) with short, imperative summaries. Pull requests should describe the user-visible or operational change, note any settings, schema, or background-worker impact, and include test results. Add screenshots when templates or UI pages change, and link the relevant issue or task when one exists.

## Security & Configuration Tips
Do not commit secrets from `.env` files or production settings. Check changes to `config/settings/production.py`, `compose/production/`, and Celery entrypoints carefully, since they affect deployment behavior and background processing.
