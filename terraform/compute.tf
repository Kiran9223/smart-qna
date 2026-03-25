# ─────────────────────────────────────────────
# AMI — latest Amazon Linux 2023 x86_64
# ─────────────────────────────────────────────

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ─────────────────────────────────────────────
# Key Pair — for GitHub Actions SSH deploys
# ─────────────────────────────────────────────

resource "aws_key_pair" "deployer" {
  key_name   = "${var.app_name}-deployer"
  public_key = trimspace(file("${path.module}/../smartqna-deployer.pub"))
}

# ─────────────────────────────────────────────
# EC2 User Data — installs Docker on first boot
# ─────────────────────────────────────────────

locals {
  user_data = <<-USERDATA
    #!/bin/bash
    set -e

    # Install Docker
    yum update -y
    yum install -y docker
    systemctl enable docker
    systemctl start docker
    usermod -aG docker ec2-user

    # Install Docker Compose v2 plugin
    COMPOSE_VERSION=$$(curl -s https://api.github.com/repos/docker/compose/releases/latest \
      | grep '"tag_name"' | sed -E 's/.*"([^"]+)".*/\1/')
    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -SL "https://github.com/docker/compose/releases/download/$${COMPOSE_VERSION}/docker-compose-linux-x86_64" \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

    # Create the app directory that CI/CD will deploy into
    mkdir -p /home/ec2-user/smartqna
    chown ec2-user:ec2-user /home/ec2-user/smartqna
  USERDATA
}

# ─────────────────────────────────────────────
# EC2 Instances (×2)
# ─────────────────────────────────────────────

resource "aws_instance" "backend" {
  count = 2

  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.ec2_instance_type
  key_name               = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2.name
  user_data              = local.user_data

  # Assign a public IP so GitHub Actions can SSH in directly
  associate_public_ip_address = true

  tags = {
    Name = "${var.app_name}-backend-${count.index + 1}"
  }
}

# ─────────────────────────────────────────────
# Application Load Balancer
# ─────────────────────────────────────────────

resource "aws_lb" "main" {
  name               = "${var.app_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = data.aws_subnets.default.ids

  enable_deletion_protection = false

  tags = {
    Name = "${var.app_name}-alb"
  }
}

# ─────────────────────────────────────────────
# Target Group — ALB → EC2 instances on port 80
# ─────────────────────────────────────────────

resource "aws_lb_target_group" "backend" {
  name     = "${var.app_name}-targets"
  port     = 80
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id

  health_check {
    path                = "/api/v1/health"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200"
  }

  tags = {
    Name = "${var.app_name}-targets"
  }
}

# Register both EC2 instances with the target group
resource "aws_lb_target_group_attachment" "backend" {
  count            = 2
  target_group_arn = aws_lb_target_group.backend.arn
  target_id        = aws_instance.backend[count.index].id
  port             = 80
}

# ─────────────────────────────────────────────
# ALB Listener — HTTP:80 → target group
# CloudFront handles TLS; ALB only needs HTTP
# ─────────────────────────────────────────────

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}
