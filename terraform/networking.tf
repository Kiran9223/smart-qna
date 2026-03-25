# Use the default VPC — no custom networking needed
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ALB Security Group — accepts HTTP/HTTPS traffic from the internet
resource "aws_security_group" "alb" {
  name        = "${var.app_name}-alb-sg"
  description = "Allow HTTP and HTTPS inbound to the Application Load Balancer"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP from internet (CloudFront uses HTTP to reach ALB)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.app_name}-alb-sg"
  }
}

# EC2 Security Group — accepts HTTP only from ALB; SSH from anywhere for CI/CD deploys
resource "aws_security_group" "ec2" {
  name        = "${var.app_name}-ec2-sg"
  description = "Allow HTTP from ALB only; SSH for GitHub Actions deploys"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description     = "HTTP from ALB security group only"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    description = "SSH for GitHub Actions CI/CD deploy steps"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.app_name}-ec2-sg"
  }
}
