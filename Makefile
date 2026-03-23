.PHONY: setup run stop clean test lint help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: ## One-time setup: install Ollama, models, Python deps, Node deps
	./scripts/setup.sh

run: ## Start everything (Ollama + backend + frontend)
	./scripts/start.sh

backend: ## Start only the backend
	cd backend && source .venv/bin/activate && python -m cli.main serve

frontend: ## Start only the frontend
	cd frontend && npm run dev

clean: ## Remove virtual env, node_modules, and cached data
	rm -rf backend/.venv
	rm -rf frontend/node_modules
	rm -rf frontend/.next

test: ## Run Python tests
	cd backend && source .venv/bin/activate && pytest

lint: ## Run linter
	cd backend && source .venv/bin/activate && ruff check .
