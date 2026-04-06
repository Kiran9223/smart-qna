output "notification_worker_lambda_function_name" {
  value = module.notification_worker.lambda_function_name
}

output "notification_worker_lambda_role_name" {
  value = module.notification_worker.lambda_role_name
}

output "notification_worker_queue_arn" {
  value = module.notification_worker.notification_queue_arn
}

output "notification_worker_ecr_repository_url" {
  value = module.notification_worker.notification_worker_ecr_repository_url
}