SHELL := /bin/bash
IMAGE_TAG ?= local
export IMAGE_TAG
KUBECONFIG ?= $(HOME)/.kube/kind-k8s-data-platform
export KUBECONFIG

.PHONY: help up infra image deploy smoke test lint troubleshoot airflow-password psql down jenkins

help: ## List targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-18s %s\n", $$1, $$2}'

up: infra image deploy ## Everything: cluster + S3 + Postgres + Airflow
	@echo "Airflow: $$(terraform -chdir=terraform output -raw airflow_url)  user: admin  password: $$(terraform -chdir=terraform output -raw airflow_admin_password)"

infra: ## Terraform: kind cluster, LocalStack, S3 buckets, credentials
	scripts/infra-up.sh

image: ## Build the Airflow image and load it into the cluster
	scripts/build-image.sh

deploy: ## Deploy Postgres + Airflow to Kubernetes
	scripts/deploy.sh

smoke: ## Run the DAG for one day (DAY=YYYY-MM-DD) and check the warehouse
	scripts/smoke-test.sh $(DAY)

test: ## Unit tests
	python3 -m pytest -q

lint: ## Lint Python, Terraform and Kubernetes manifests
	ruff check . && ruff format --check .
	terraform -chdir=terraform fmt -check -recursive
	kubectl kustomize k8s > /dev/null

troubleshoot: ## Pod status, events and recent logs
	scripts/troubleshoot.sh

airflow-password: ## Print the Airflow admin password
	@terraform -chdir=terraform output -raw airflow_admin_password; echo

psql: ## Open psql on the warehouse database
	kubectl -n data-platform exec -it statefulset/postgres -- sh -c 'psql -U "$$POSTGRES_USER" -d warehouse'

down: ## Destroy the cluster and everything in it
	scripts/down.sh

jenkins: ## Start the local Jenkins server (http://localhost:8081)
	docker compose -f jenkins/docker-compose.yml up -d --build
