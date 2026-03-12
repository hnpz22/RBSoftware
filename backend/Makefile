.PHONY: install lint test run alembic-revision alembic-upgrade

install:
	pip install -r requirements-dev.txt

lint:
	ruff check app tests

test:
	pytest

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

alembic-revision:
	alembic revision --autogenerate -m "init"

alembic-upgrade:
	alembic upgrade head
