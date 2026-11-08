#!/usr/bin/env bash
# Terraform: create the kind cluster, namespace, LocalStack, S3 buckets and credentials.
source "$(dirname "$0")/lib.sh"
require docker terraform curl

docker info >/dev/null 2>&1 || die "Docker is not running. Start Docker Desktop first."

cd "$REPO_ROOT/terraform"
log "terraform init"
terraform init -input=false
log "terraform apply"
terraform apply -input=false -auto-approve "$@"
