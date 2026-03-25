locals {
  s3_origin_id  = "S3-${var.app_name}-frontend"
  alb_origin_id = "ALB-${var.app_name}"
}

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  comment             = "SmartQnA — serves React SPA from S3 and proxies /api/v1 to ALB"

  # ── Origin 1: S3 frontend bucket (static assets) ──────────────────────────
  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = local.s3_origin_id
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  # ── Origin 2: Application Load Balancer (API calls) ───────────────────────
  origin {
    domain_name = aws_lb.main.dns_name
    origin_id   = local.alb_origin_id

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  # ── Default cache behaviour: serve React SPA from S3 ──────────────────────
  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = local.s3_origin_id
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
    compress    = true
  }

  # ── API behaviour: forward /api/v1/* to ALB without caching ───────────────
  ordered_cache_behavior {
    path_pattern           = "/api/v1/*"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = local.alb_origin_id
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Content-Type", "Accept", "Origin", "Host"]
      cookies {
        forward = "all"
      }
    }

    # TTL = 0 ensures API responses are never cached
    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
    compress    = true
  }

  # ── SPA routing: map S3 403/404 → index.html so React Router works ────────
  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # Use the default CloudFront certificate (*.cloudfront.net domain)
  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "${var.app_name}-distribution"
  }
}
