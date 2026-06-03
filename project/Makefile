.PHONY: up down build logs test e2e lint migrate seed seed-regen deploy health backup clean

up:
	docker compose build
	docker compose up -d

down:
	docker compose down

build:
	docker compose build --no-cache

logs:
	docker compose logs -f $(service)

test:
	docker compose exec backend pytest tests/ -xvs

e2e:
	docker compose exec backend pytest tests/e2e/ -xvs

lint:
	docker compose exec backend ruff check . --fix

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec -T postgres psql -U postgres -d hardware_tracker < backend/scripts/seed_data_v2.sql

seed-regen:
	cd backend && uv run python scripts/generate_seed.py

deploy:
	@sh scripts/deploy.sh

health:
	@sh scripts/healthcheck.sh

backup:
	@echo "Backup: Creating database dump..."
	@docker compose exec -T postgres pg_dump -U $$POSTGRES_USER $$POSTGRES_DB > backup-$$(date +%Y%m%d-%H%M%S).sql
	@echo "Backup saved to backup-$$(date +%Y%m%d-%H%M%S).sql"

clean: down
	docker compose down -v
	docker system prune -f
