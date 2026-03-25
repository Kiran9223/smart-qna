# After running `terraform apply`, copy these values into GitHub Secrets.
# Run `terraform output` to see all values.

output "alb_dns_name" {
  description = "ALB DNS name → GitHub Secret: ALB_DNS_NAME"
  value       = aws_lb.main.dns_name
}

output "cloudfront_domain" {
  description = "CloudFront domain → share with team as the public app URL"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID → GitHub Secret: CF_DISTRIBUTION_ID"
  value       = aws_cloudfront_distribution.frontend.id
}

output "ecr_repository_uri" {
  description = "ECR repository URI → GitHub Secret: ECR_REPO"
  value       = aws_ecr_repository.backend.repository_url
}

output "s3_frontend_bucket" {
  description = "Frontend S3 bucket name → GitHub Secret: S3_FRONTEND_BUCKET"
  value       = aws_s3_bucket.frontend.id
}

output "s3_attachments_bucket" {
  description = "Attachments S3 bucket name (reference for teammates)"
  value       = aws_s3_bucket.attachments.id
}

output "ec2_instance_1_ip" {
  description = "EC2 instance 1 public IP → GitHub Secret: EC2_HOST_1"
  value       = aws_instance.backend[0].public_ip
}

output "ec2_instance_2_ip" {
  description = "EC2 instance 2 public IP → GitHub Secret: EC2_HOST_2"
  value       = aws_instance.backend[1].public_ip
}
