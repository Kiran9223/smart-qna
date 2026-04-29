terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state — create the S3 bucket and DynamoDB table manually once
  # before running `terraform init`:
  #   aws s3 mb s3://smartqna-tfstate --region us-east-1
  #   aws dynamodb create-table \
  #     --table-name smartqna-tfstate-lock \
  #     --attribute-definitions AttributeName=LockID,AttributeType=S \
  #     --key-schema AttributeName=LockID,KeyType=HASH \
  #     --billing-mode PAY_PER_REQUEST \
  #     --region us-east-1
  backend "s3" {
    bucket       = "smartqna-tfstate"
    key          = "smartqna/terraform.tfstate"
    region       = "us-west-1"
    use_lockfile = true
    encrypt      = true
  }
}

provider "aws" {
  region = var.aws_region
}

provider "aws" {
  alias  = "notification"
  region = var.notification_region
}

module "notification_service" {
  source = "./modules/notification_service"
  providers = {
    aws = aws.notification
  }

  project_name = var.app_name
  environment  = var.notification_service_environment

  db_host     = var.notification_db_host
  db_port     = var.notification_db_port
  db_name     = var.notification_db_name
  db_user     = var.notification_db_user
  db_password = var.notification_db_password

  sender_email = var.notification_sender_email

  notification_worker_image_uri = var.notification_worker_image_uri
  notification_api_image_uri    = var.notification_api_image_uri

  cognito_region        = var.cognito_region
  cognito_user_pool_id  = var.cognito_user_pool_id
  cognito_app_client_id = var.cognito_app_client_id
}
