output "lambda_function_name" {
  value = local.lambda_function_name
}

output "lambda_role_name" {
  value = aws_iam_role.lambda_role.name
}

output "notification_queue_arn" {
  value = data.aws_sqs_queue.notification.arn
}

output "notification_worker_ecr_repository_url" {
  value = aws_ecr_repository.notification_worker.repository_url
}