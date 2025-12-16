
COMPOSE = docker compose
COMPOSE_FILE = docker-compose.yml
APP_NAME = main
PORT = 8000
CONTAINER = tse-backend

# ---------------- CONTAINERS ---------------- #
build:
	@$(COMPOSE) -f $(COMPOSE_FILE) build --no-cache

up: 
	@$(COMPOSE) -f $(COMPOSE_FILE) up -d

restart: 
	@$(COMPOSE) -f $(COMPOSE_FILE) restart $(CONTAINER)

down:
	@$(COMPOSE) -f $(COMPOSE_FILE) down

logs:
	@$(COMPOSE) -f $(COMPOSE_FILE) logs -f $(CONTAINER)

reset:
	@$(COMPOSE) -f $(COMPOSE_FILE) exec $(CONTAINER) bash -c "make db-reset"

migrate:
	@$(COMPOSE) -f $(COMPOSE_FILE) exec $(CONTAINER) bash -c "make db-migrate"

# ---------------- COMMANDS ---------------- #

run:
	python app/core/main.py

db-migrate:
	python -m alembic revision --autogenerate -m 'migrate' && python -m alembic upgrade head

delete:
	python app/delete_db.py

db-reset:
	python app/scripts/delete_alembic_versions.py && make delete && make db-migrate && make populate-db

populate-db:
	python app/populate_db.py

.PHONY: run migrate delete reset populate-db