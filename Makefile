IMAGE_NAME=opencorporates
BUILD_NAME=latest

.PHONY: build
build:
	docker compose build

.PHONY: run
run:
	docker compose up -d

.PHONY: build-run
dbuild: build run

.PHONY: stop
stop:
	docker compose down

.PHONY: clean
clean:
	docker system prune -f