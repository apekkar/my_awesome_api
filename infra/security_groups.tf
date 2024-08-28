resource "aws_security_group" "lambda_sg" {
  name        = "lambda-security-group"
  description = "Security group for Lambda function"
  vpc_id      = aws_default_vpc.default.id

  egress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow outbound to any IP (can be more restrictive if needed)
    description = "Allow Lambda to access RDS on port 5432 (PostgreSQL)"
  }

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow outbound to any IP (can be more restrictive if needed)
    description = "Allow Lambda to access Secrets Manager on port 443"
  }
}

resource "aws_security_group" "rds_sg" {
  name        = "rds-security-group"
  description = "Security group for RDS"
  vpc_id      = aws_default_vpc.default.id

  ingress {
    from_port = 5432
    to_port   = 5432
    protocol  = "tcp"
    security_groups = [
      aws_security_group.lambda_sg.id,
      aws_security_group.rds_proxy_sg.id
    ]
    description = "Allow Lambda function & RDS Proxy to connect to RDS"
  }
}

resource "aws_security_group" "rds_proxy_sg" {
  name        = "rds-proxy-sg"
  description = "Security group for RDS Proxy"
  vpc_id      = aws_default_vpc.default.id

  # Allow incoming traffic from Lambda
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda_sg.id] # Allow only from Lambda security group
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "vpc_endpoint_sg" {
  name        = "vpc-endpoint-sg"
  description = "Security group for VPC endpoint"
  vpc_id      = aws_default_vpc.default.id

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda_sg.id] # Allow traffic from Lambda security group
  }

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow outbound traffic to any IP
  }
}

resource "aws_security_group" "rds_access_from_my_ip" {
  name        = "rds-access-from-my-ip"
  description = "Allow access to RDS from my IP"
  vpc_id      = aws_default_vpc.default.id

  ingress {
    from_port   = 5432 # Port for PostgreSQL (modify if using a different database)
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["${local.envs["MY_IP"]}/32"] # Replace with your IP address
  }
}