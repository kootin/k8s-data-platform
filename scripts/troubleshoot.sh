#!/usr/bin/env bash
# One-shot diagnostics: what's running, what's failing, and recent logs.
# See docs/RUNBOOK.md for what to do with the output.
source "$(dirname "$0")/lib.sh"
set +e
require kubectl

section() { printf '\n\033[1m==== %s ====\033[0m\n' "$*"; }

section "cluster"
kind get clusters 2>/dev/null
kubectl cluster-info 2>&1 | head -2

section "node conditions (memory / disk pressure shows here)"
kubectl get nodes -o wide
kubectl describe nodes | grep -A8 -E '^Conditions:'

section "pods in $NAMESPACE"
kc get pods -o wide

section "pods not Running or Completed"
kc get pods --no-headers | awk '$3 != "Running" && $3 != "Completed" {print}'

section "recent warning events"
kc get events --field-selector type=Warning --sort-by=.lastTimestamp | tail -20

section "persistent volume claims"
kc get pvc

for target in deploy/airflow-scheduler deploy/airflow-webserver statefulset/postgres deploy/localstack; do
  section "last 30 log lines: $target"
  kc logs "$target" --all-containers --tail=30 2>&1
done

section "LocalStack health from this machine"
curl -fsS http://localhost:4566/_localstack/health 2>&1 | head -c 400
echo

section "recent DAG runs"
kc exec deploy/airflow-scheduler -c scheduler -- airflow dags list-runs -d nyc311_daily 2>&1 | head -12
