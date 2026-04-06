resource "aws_lambda_event_source_mapping" "notification_queue_trigger" {
  count = var.enable_notification_queue_trigger ? 1 : 0

  event_source_arn = data.aws_sqs_queue.notification.arn
  function_name    = aws_lambda_function.notification_worker.arn
  batch_size       = 10
  enabled          = true
}