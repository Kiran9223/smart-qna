output "notification_queue_url" {
  value = aws_sqs_queue.events.url
}

output "notification_queue_arn" {
  value = aws_sqs_queue.events.arn
}

output "notification_api_url" {
  value = aws_apigatewayv2_stage.default.invoke_url
}

output "notification_worker_ecr_repository_url" {
  value = aws_ecr_repository.worker.repository_url
}

output "notification_api_ecr_repository_url" {
  value = aws_ecr_repository.api.repository_url
}
