output "cluster_name" {
  value = kind_cluster.this.name
}

output "kubeconfig_path" {
  value = kind_cluster.this.kubeconfig_path
}

output "namespace" {
  value = kubernetes_namespace.platform.metadata[0].name
}

output "airflow_url" {
  value = "http://localhost:${var.airflow_host_port}"
}

output "airflow_admin_password" {
  value     = random_password.airflow_admin.result
  sensitive = true
}

output "postgres_password" {
  value     = random_password.postgres.result
  sensitive = true
}

output "buckets" {
  value = {
    raw     = aws_s3_bucket.raw.bucket
    curated = aws_s3_bucket.curated.bucket
  }
}
