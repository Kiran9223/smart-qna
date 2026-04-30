variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "db_host" {
  type = string
}

variable "db_port" {
  type    = number
  default = 5432
}

variable "db_name" {
  type = string
}

variable "db_user" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "sender_email" {
  type    = string
  default = ""
}

variable "notification_worker_image_uri" {
  type = string
}

variable "notification_api_image_uri" {
  type = string
}

variable "cognito_region" {
  type = string
}

variable "cognito_user_pool_id" {
  type = string
}

variable "cognito_app_client_id" {
  type = string
}

variable "allowed_origins" {
  type    = list(string)
  default = ["http://localhost:5173"]
}
