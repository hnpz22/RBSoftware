.PHONY: lint test backend-lint backend-test frontend-lint frontend-test

lint: backend-lint frontend-lint

test: backend-test frontend-test

backend-lint:
	$(MAKE) -C backend lint

backend-test:
	$(MAKE) -C backend test

frontend-lint:
	cd frontend && npm run lint

frontend-test:
	cd frontend && npm run test
