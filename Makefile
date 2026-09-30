install:
	uv sync

project:
	uv run database

build:
	uv build

publish:
	uv publish --dry-run

package-install:
	uv pip install dist/*.whl

lint:
	uv run ruff check .
