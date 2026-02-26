.PHONY: up down logs migrate test seed

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f backend

migrate:
	docker compose exec backend alembic upgrade head

migrate-create:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

test:
	docker compose exec backend pytest -v

seed:
	docker compose exec backend python -m app.utils.seed
