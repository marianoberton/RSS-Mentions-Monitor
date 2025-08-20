venv:
	python -m venv venv

run:
	. venv/bin/activate && python main.py

test:
	. venv/bin/activate && pytest

docker-build:
	docker build -t rss-mentions-monitor .

docker-run:
	docker-compose up -d