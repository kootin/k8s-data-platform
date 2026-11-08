# Data lake buckets: raw API extracts and cleaned Parquet.

resource "aws_s3_bucket" "raw" {
  bucket        = "nyc311-raw"
  force_destroy = true
  depends_on    = [terraform_data.wait_for_localstack]
}

resource "aws_s3_bucket" "curated" {
  bucket        = "nyc311-curated"
  force_destroy = true
  depends_on    = [terraform_data.wait_for_localstack]
}

# Keep every version of raw extracts so a bad re-pull can be rolled back.
resource "aws_s3_bucket_versioning" "raw" {
  bucket = aws_s3_bucket.raw.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "raw" {
  bucket     = aws_s3_bucket.raw.id
  depends_on = [aws_s3_bucket_versioning.raw]

  rule {
    id     = "expire-raw-extracts"
    status = "Enabled"

    filter {
      prefix = "nyc311/"
    }

    expiration {
      days = var.raw_retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lake" {
  for_each = {
    raw     = aws_s3_bucket.raw.id
    curated = aws_s3_bucket.curated.id
  }

  bucket = each.value
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "lake" {
  for_each = {
    raw     = aws_s3_bucket.raw.id
    curated = aws_s3_bucket.curated.id
  }

  bucket                  = each.value
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
