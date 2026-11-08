terraform {
  required_version = ">= 1.6"

  required_providers {
    kind = {
      source  = "tehcyx/kind"
      version = "~> 0.6"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.33"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.75"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}
