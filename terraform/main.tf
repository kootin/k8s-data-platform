# Layer 1: a local Kubernetes cluster (kind = Kubernetes in Docker).
# NodePorts are mapped to ports on your machine so the Airflow UI,
# LocalStack (S3) and Postgres are reachable on localhost.

locals {
  node_ports = {
    airflow    = 30080
    localstack = 30566
    postgres   = 30432
  }
}

resource "kind_cluster" "this" {
  name            = var.cluster_name
  node_image      = "kindest/node:${var.kubernetes_version}"
  wait_for_ready  = true
  kubeconfig_path = pathexpand("~/.kube/kind-${var.cluster_name}")

  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    node {
      role = "control-plane"

      extra_port_mappings {
        container_port = local.node_ports.airflow
        host_port      = var.airflow_host_port
      }
      extra_port_mappings {
        container_port = local.node_ports.localstack
        host_port      = var.localstack_host_port
      }
      extra_port_mappings {
        container_port = local.node_ports.postgres
        host_port      = var.postgres_host_port
      }
    }
  }
}

resource "kubernetes_namespace" "platform" {
  metadata {
    name = var.namespace
    labels = {
      "app.kubernetes.io/part-of" = "k8s-data-platform"
    }
  }
}
