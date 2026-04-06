locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

module "notification_worker" {
  source = "./modules/notification_worker"

  aws_region                    = var.aws_region
  project_name                  = var.project_name
  environment                   = var.environment
  notification_queue_name       = var.notification_queue_name
  db_host                       = var.db_host
  db_port                       = var.db_port
  db_name                       = var.db_name
  db_user                       = var.db_user
  db_password                   = var.db_password
  sender_email                  = var.sender_email
  notification_worker_image_uri = var.notification_worker_image_uri

  enable_notification_queue_trigger = var.enable_notification_queue_trigger
}