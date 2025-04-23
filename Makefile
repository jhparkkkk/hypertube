up:
	docker-compose up --build -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

backend-restart:
	docker-compose restart backend

backend-logs:
	docker-compose logs -f backend

backend-migrate:
	docker-compose exec backend python manage.py migrate

backend-makemigrations:
	docker-compose exec backend python manage.py makemigrations

backend-db:
	docker-compose exec db psql -U hypertube_user -d hypertube_db

backend-clean-movies:
	docker-compose exec db psql -U hypertube_user -d hypertube_db -c "TRUNCATE TABLE streaming_moviefile CASCADE;"
	docker-compose exec backend bash -c "rm -rf /app/downloads/* /app/downloads/.* 2>/dev/null || true"
	docker-compose exec backend bash -c "rm -rf /app/conversions/* /app/conversions/.* 2>/dev/null || true"

backend-shell:
	docker-compose exec backend bash

frontend-up:
	docker-compose up --build -d frontend

frontend-restart:
	docker-compose restart frontend

frontend-logs:
	docker-compose logs -f frontend

frontend-shell:
	docker-compose exec frontend bash

frontend-npm:
	docker-compose exec frontend npm install

clean: backend-clean-movies
	docker-compose down --volumes --remove-orphans
	docker system prune -af
