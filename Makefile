.PHONY: help build up down restart logs shell db-shell migrate makemigrations test clean format lint

# Default target
help:
	@echo "Available commands:"
	@echo "  make build          - Build Docker images"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs"
	@echo "  make shell          - Access app container shell"
	@echo "  make db-shell       - Access PostgreSQL shell"
	@echo "  make migrate        - Run database migrations"
	@echo "  make makemigrations - Create new migration"
	@echo "  make test           - Run tests"
	@echo "  make test-iiko      - Test iiko API connection"
	@echo "  make clean          - Remove containers and volumes"
	@echo "  make format         - Format code with black"
	@echo "  make lint           - Run linters"

# Build Docker images
build:
	docker-compose build

# Start services
up:
	docker-compose up -d
	@echo "Services started. API available at http://localhost:8000"
	@echo "API docs available at http://localhost:8000/docs"

# Stop services
down:
	docker-compose down

# Restart services
restart:
	docker-compose restart

# View logs
logs:
	docker-compose logs -f

# Access app container shell
shell:
	docker-compose exec app /bin/bash

# Access PostgreSQL shell
db-shell:
	docker-compose exec db psql -U postgres -d iiko_db

# Run database migrations
migrate:
	docker compose exec app alembic upgrade head

# Create new migration
migrations:
	@read -p "Enter migration message: " msg; \
	docker compose exec app alembic revision --autogenerate -m "$$msg"

# Run tests
test:
	docker-compose exec app pytest -v

# Test iiko API connection
test-iiko:
	docker-compose exec app python -m app.scripts.test_iiko

# Clean up
clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Format code
format:
	docker-compose exec app black app/
	docker-compose exec app black alembic/

# Run linters
lint:
	docker-compose exec app flake8 app/
	docker-compose exec app mypy app/

# Initialize project (first time setup)
init:
	cp .env.example .env
	@echo "Created .env file. Please update with your settings."
	make build
	make up
	sleep 5
	make migrate
	@echo "Project initialized successfully!"
