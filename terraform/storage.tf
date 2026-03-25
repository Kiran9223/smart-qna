# ─────────────────────────────────────────────
# S3 Frontend Bucket  (private — CloudFront OAC is the only accessor)
# ─────────────────────────────────────────────

resource "aws_s3_bucket" "frontend" {
  bucket = "${var.app_name}-frontend"

  tags = {
    Name = "${var.app_name}-frontend"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable static website hosting so index.html is the default and error document
resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

# OAC — Origin Access Control that CloudFront uses to sign S3 requests
resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${var.app_name}-oac"
  description                       = "OAC for SmartQnA frontend S3 bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# Bucket policy — grants CloudFront OAC read access; everything else is blocked
# depends_on ensures the CloudFront distribution ARN is available
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowCloudFrontOAC"
      Effect    = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.frontend.arn}/*"
      Condition = {
        StringEquals = {
          "AWS:SourceArn" = aws_cloudfront_distribution.frontend.arn
        }
      }
    }]
  })

  depends_on = [aws_cloudfront_distribution.frontend]
}

# ─────────────────────────────────────────────
# S3 Attachments Bucket  (private — accessed only via pre-signed URLs)
# ─────────────────────────────────────────────

resource "aws_s3_bucket" "attachments" {
  bucket = "${var.app_name}-attachments"

  tags = {
    Name = "${var.app_name}-attachments"
  }
}

resource "aws_s3_bucket_public_access_block" "attachments" {
  bucket = aws_s3_bucket.attachments.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CORS — allows browsers to upload directly to S3 via pre-signed PUT URLs
resource "aws_s3_bucket_cors_configuration" "attachments" {
  bucket = aws_s3_bucket.attachments.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
    allowed_origins = ["*"]
    max_age_seconds = 3000
  }
}
