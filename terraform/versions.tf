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
    # 5.86+ waits for S3 to echo back transition_default_minimum_object_size on
    # lifecycle rules. LocalStack 3.x never does, so the apply would time out.
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.75, < 5.86"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}
