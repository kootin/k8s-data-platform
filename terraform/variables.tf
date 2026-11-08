variable "cluster_name" {
  description = "Name of the local kind cluster."
  type        = string
  default     = "k8s-data-platform"
}

variable "kubernetes_version" {
  description = "kindest/node image tag, which pins the Kubernetes version."
  type        = string
  default     = "v1.31.0"
}

variable "namespace" {
  description = "Namespace that holds the platform (LocalStack, Postgres, Airflow)."
  type        = string
  default     = "data-platform"
}

variable "localstack_image" {
  description = "LocalStack image. Pinned to 3.x, which runs without an auth token."
  type        = string
  default     = "localstack/localstack:3.8"
}

variable "aws_region" {
  description = "Region the (emulated) AWS resources live in."
  type        = string
  default     = "us-east-1"
}

variable "localstack_host_port" {
  description = "Port on your machine that reaches LocalStack inside the cluster."
  type        = number
  default     = 4566
}

variable "airflow_host_port" {
  description = "Port on your machine for the Airflow web UI."
  type        = number
  default     = 8080
}

variable "postgres_host_port" {
  description = "Port on your machine for the Postgres warehouse."
  type        = number
  default     = 5432
}

variable "raw_retention_days" {
  description = "Days before raw API extracts expire from the raw bucket."
  type        = number
  default     = 30
}
