
run:
	python app/core/main.py

migrate:
	python -m alembic revision --autogenerate -m 'migrate' && python -m alembic upgrade head

delete:
	python app/delete_db.py

reset:
	python app/scripts/delete_alembic_versions.py && make delete && make migrate && make populate-db

populate-db:
	python app/populate_db.py

.PHONY: run migrate delete reset populate-db