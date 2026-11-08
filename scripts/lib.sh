#!/usr/bin/env bash
# Shared settings and helpers for the scripts in this folder.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLUSTER_NAME="${CLUSTER_NAME:-k8s-data-platform}"
NAMESPACE="${NAMESPACE:-data-platform}"
IMAGE_REPO="${IMAGE_REPO:-k8s-data-platform/airflow}"
IMAGE_TAG="${IMAGE_TAG:-local}"
export KUBECONFIG="${KUBECONFIG:-$HOME/.kube/kind-$CLUSTER_NAME}"

log()  { printf '\033[1;34m[%s]\033[0m %s\n' "$(date +%H:%M:%S)" "$*"; }
warn() { printf '\033[1;33m[%s] WARN:\033[0m %s\n' "$(date +%H:%M:%S)" "$*" >&2; }
die()  { printf '\033[1;31m[%s] ERROR:\033[0m %s\n' "$(date +%H:%M:%S)" "$*" >&2; exit 1; }

require() {
  local missing=()
  for cmd in "$@"; do command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd"); done
  ((${#missing[@]} == 0)) || die "missing tools: ${missing[*]} (see README > Prerequisites)"
}

kc() { kubectl -n "$NAMESPACE" "$@"; }
