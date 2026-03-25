# IAM Role — allows EC2 instances to assume this role
resource "aws_iam_role" "ec2" {
  name = "${var.app_name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    Name = "${var.app_name}-ec2-role"
  }
}

# ECR read-only — pull Docker images from the private registry
resource "aws_iam_role_policy_attachment" "ec2_ecr" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

# S3 full access — generate pre-signed URLs for file attachments
resource "aws_iam_role_policy_attachment" "ec2_s3" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# SQS full access — enqueue notification messages
resource "aws_iam_role_policy_attachment" "ec2_sqs" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSQSFullAccess"
}

# Bedrock full access — call Titan Embeddings for AI similarity search
resource "aws_iam_role_policy_attachment" "ec2_bedrock" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
}

# Cognito-idp inline policy — admin group management endpoints
resource "aws_iam_role_policy" "ec2_cognito" {
  name = "${var.app_name}-ec2-cognito"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "cognito-idp:AdminAddUserToGroup",
        "cognito-idp:AdminRemoveUserFromGroup",
        "cognito-idp:ListUsersInGroup",
        "cognito-idp:AdminGetUser",
        "cognito-idp:ListUsers"
      ]
      Resource = "arn:aws:cognito-idp:${var.aws_region}:*:userpool/${var.cognito_user_pool_id}"
    }]
  })
}

# Instance profile — what EC2 uses to pick up the role
resource "aws_iam_instance_profile" "ec2" {
  name = "${var.app_name}-ec2-profile"
  role = aws_iam_role.ec2.name
}
