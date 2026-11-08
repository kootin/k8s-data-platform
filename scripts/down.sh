#!/usr/bin/env bash
# Tear everything down (cluster, buckets, data). Terraform destroys what it created.
source "$(dirname "$0")/lib.sh"
require terraform

cd "$REPO_ROOT/terraform"
terraform destroy -input=false -auto-approve || {
  warn "terraform destroy failed; deleting the kind cluster directly"
  kind delete cluster --name "$CLUSTER_NAME"
}
