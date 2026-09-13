COMPOSE := docker compose
SERVER_DIR := server
WEBAPP_DIR := webapp

.PHONY: help setup env up down restart ps build rebuild logs logs-server logs-webapp logs-postgres \
	postgres dev-server dev-web test-smoke evals demo exec-server clean down-volumes

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage: make \033[36m<target>\033[0m\n\nTargets:\n"} \
		/^[a-zA-Z0-9_-]+:.*##/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

setup: env ## Copy .env examples if missing
	@echo "Setup complete. Edit $(SERVER_DIR)/.env (GEMINI_API_KEY) before evals or live mode."

env: ## Ensure server/.env and webapp/.env.local exist
	@test -f $(SERVER_DIR)/.env || (cp $(SERVER_DIR)/.env.example $(SERVER_DIR)/.env && echo "Created $(SERVER_DIR)/.env")
	@test -f $(WEBAPP_DIR)/.env.local || (cp $(WEBAPP_DIR)/.env.example $(WEBAPP_DIR)/.env.local && echo "Created $(WEBAPP_DIR)/.env.local")

up: env ## Build (if needed) and start full stack in background
	$(COMPOSE) up -d --build
	@echo ""
	@echo "Webapp:  http://localhost:3000"
	@echo "API:     http://localhost:8000"
	@echo "Postgres: localhost:5432 (leadtriage / leadtriage)"

down: ## Stop containers (keep volumes)
	$(COMPOSE) down

down-volumes: ## Stop containers and remove postgres volume
	$(COMPOSE) down -v

restart: ## Restart all services
	$(COMPOSE) restart

ps: ## Show compose service status
	$(COMPOSE) ps

build: ## Build server and webapp images
	$(COMPOSE) build

rebuild: ## Rebuild images without cache and restart stack
	$(COMPOSE) build --no-cache
	$(COMPOSE) up -d

logs: ## Tail logs for all services
	$(COMPOSE) logs -f

logs-server: ## Tail server logs
	$(COMPOSE) logs -f server

logs-webapp: ## Tail webapp logs
	$(COMPOSE) logs -f webapp

logs-postgres: ## Tail postgres logs
	$(COMPOSE) logs -f postgres

postgres: env ## Start only Postgres (for local uvicorn / yarn dev)
	$(COMPOSE) up -d postgres
	@echo "DATABASE_URL=postgresql://leadtriage:leadtriage@localhost:5432/leadtriage"

dev-server: postgres ## Run API locally with uvicorn (requires pip install -r server/requirements.txt)
	cd $(SERVER_DIR) && uvicorn server:app --reload --port 8000

dev-web: ## Run Next.js dev server locally (requires yarn in webapp/)
	cd $(WEBAPP_DIR) && yarn dev

test-smoke: ## Orchestration smoke tests (no LLM tokens)
	cd $(SERVER_DIR) && python tests_smoke.py

evals: ## Run eval suite (needs GEMINI_API_KEY in server/.env)
	cd $(SERVER_DIR) && python -m evals.run_evals

demo: ## Demo script with fakes
	cd $(SERVER_DIR) && python demo.py inject

exec-server: ## Shell into running server container
	$(COMPOSE) exec server sh

clean: down-volumes ## Alias: stop stack and delete postgres data
