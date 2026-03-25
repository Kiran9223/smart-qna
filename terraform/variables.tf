variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-west-1"
}

variable "app_name" {
  description = "Application name prefix used for all resource names"
  type        = string
  default     = "smartqna"
}

variable "ec2_instance_type" {
  description = "EC2 instance type for backend servers"
  type        = string
  default     = "t3.micro"
}

# Cognito — already provisioned by teammate; just reference the IDs here
variable "cognito_user_pool_id" {
  description = "Existing Cognito User Pool ID"
  type        = string
  default     = "us-east-1_FYVTuevQ9"
}

variable "cognito_app_client_id" {
  description = "Existing Cognito App Client ID"
  type        = string
  default     = "7r4nc65f89pg5adl442fufrig8"
}

# App secrets — set in terraform.tfvars (gitignored)
variable "secret_key" {
  description = "FastAPI application secret key (long random string)"
  type        = string
  sensitive   = true
}

# Provided by the teammate who sets up RDS
variable "db_url" {
  description = "PostgreSQL asyncpg connection URL from teammate's RDS setup"
  type        = string
  sensitive   = true
  default     = "postgresql+asyncpg://placeholder:placeholder@placeholder:5432/smartqna"
}

# Provided by the teammate who sets up SQS
variable "sqs_queue_url" {
  description = "SQS notification queue URL from teammate's SQS setup"
  type        = string
  default     = ""
}
