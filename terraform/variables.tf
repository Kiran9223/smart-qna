variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-west-1"
}

variable "notification_region" {
  description = "AWS region for notification microservice resources"
  type        = string
  default     = "us-east-1"
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

variable "cognito_region" {
  description = "AWS region where Cognito user pool exists"
  type        = string
  default     = "us-east-1"
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

variable "notification_service_environment" {
  description = "Environment suffix used for notification service resources"
  type        = string
  default     = "prod"
}

variable "notification_db_host" {
  description = "Notification service Postgres host"
  type        = string
  default     = "placeholder"
}

variable "notification_db_port" {
  description = "Notification service Postgres port"
  type        = number
  default     = 5432
}

variable "notification_db_name" {
  description = "Notification service Postgres database name"
  type        = string
  default     = "smartqna"
}

variable "notification_db_user" {
  description = "Notification service Postgres username"
  type        = string
  default     = "placeholder"
}

variable "notification_db_password" {
  description = "Notification service Postgres password"
  type        = string
  sensitive   = true
  default     = "placeholder"
}

variable "notification_sender_email" {
  description = "Optional SES sender email for notification emails"
  type        = string
  default     = ""
}

variable "notification_worker_image_uri" {
  description = "Notification worker Lambda image URI"
  type        = string
  default     = "placeholder"
}

variable "notification_api_image_uri" {
  description = "Notification API Lambda image URI"
  type        = string
  default     = "placeholder"
}
