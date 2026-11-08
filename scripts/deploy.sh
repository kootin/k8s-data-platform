#!/usr/bin/env bash
# Deploy Postgres + Airflow with kustomize, pinned to IMAGE_TAG, and wait for rollout.
source "$(dirname "$0")/lib.sh"
require kubectl

kc get secret platform-credentials >/dev/null 2>&1 \
  || die "platform-credentials secret not found. Run 'make infra' (Terraform) first."

log "applying manifests (image $IMAGE_REPO:$IMAGE_TAG)"
kubectl kustomize "$REPO_ROOT/k8s" \
  | sed "s#image: $IMAGE_REPO:local#image: $IMAGE_REPO:$IMAGE_TAG#" \
  | kubectl apply -f -

log "waiting for rollouts"
kc rollout status statefulset/postgres --timeout=180s
kc rollout status deployment/airflow-scheduler --timeout=420s
kc rollout status deployment/airflow-webserver --timeout=420s
log "deployed. Airflow UI: http://localhost:${TF_VAR_airflow_host_port:-8080} (user admin, password: make airflow-password)"
