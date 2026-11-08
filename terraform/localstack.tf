# LocalStack emulates AWS S3 inside the cluster.

resource "kubernetes_deployment" "localstack" {
  metadata {
    name      = "localstack"
    namespace = kubernetes_namespace.platform.metadata[0].name
    labels    = { app = "localstack" }
  }

  spec {
    replicas = 1
    selector {
      match_labels = { app = "localstack" }
    }

    template {
      metadata {
        labels = { app = "localstack" }
      }

      spec {
        container {
          name  = "localstack"
          image = var.localstack_image

          env {
            name  = "SERVICES"
            value = "s3"
          }
          env {
            name  = "AWS_DEFAULT_REGION"
            value = var.aws_region
          }

          port {
            container_port = 4566
          }

          resources {
            requests = { cpu = "100m", memory = "256Mi" }
            limits   = { cpu = "1", memory = "1Gi" }
          }

          readiness_probe {
            http_get {
              path = "/_localstack/health"
              port = 4566
            }
            initial_delay_seconds = 5
            period_seconds        = 5
          }

          liveness_probe {
            http_get {
              path = "/_localstack/health"
              port = 4566
            }
            initial_delay_seconds = 30
            period_seconds        = 20
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "localstack" {
  metadata {
    name      = "localstack"
    namespace = kubernetes_namespace.platform.metadata[0].name
  }

  spec {
    type     = "NodePort"
    selector = { app = "localstack" }

    port {
      port        = 4566
      target_port = 4566
      node_port   = local.node_ports.localstack
    }
  }
}

# The S3 resources below call LocalStack through the host port, so wait until
# that path answers before creating them.
resource "terraform_data" "wait_for_localstack" {
  triggers_replace = [kubernetes_deployment.localstack.id, kubernetes_service.localstack.id]

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]
    command     = "${path.module}/../scripts/wait-for-http.sh http://localhost:${var.localstack_host_port}/_localstack/health 120"
  }
}
