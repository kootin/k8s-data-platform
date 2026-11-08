#!/usr/bin/env bash
# Build the Airflow image (DAG + pipeline baked in) and load it into the kind node.
source "$(dirname "$0")/lib.sh"
require docker kind

image="$IMAGE_REPO:$IMAGE_TAG"
log "building $image"
docker build -f "$REPO_ROOT/docker/airflow/Dockerfile" -t "$image" "$REPO_ROOT"

log "loading $image into kind cluster $CLUSTER_NAME"
kind load docker-image "$image" --name "$CLUSTER_NAME"
