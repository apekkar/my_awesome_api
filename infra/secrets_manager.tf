resource "random_password" "rds_password" {
  length  = 16
  special = true
}

resource "aws_secretsmanager_secret" "db_credentials" {
  name = lookup(local.envs, "AWS_SECRET_NAME")
  depends_on = [ 
    aws_default_vpc.default,
    null_resource.load_env
  ]
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = lookup(local.envs, "DATABASE_USERNAME")
    password = random_password.rds_password.result
  })
  depends_on = [ 
    aws_secretsmanager_secret.db_credentials
  ]
}

data "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  depends_on = [aws_secretsmanager_secret_version.db_credentials]
}

resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = aws_default_vpc.default.id
  service_name        = "com.amazonaws.eu-west-1.secretsmanager"
  vpc_endpoint_type   = "Interface"
  security_group_ids  = [aws_security_group.vpc_endpoint_sg.id]
  subnet_ids          = data.aws_subnets.default.ids
  private_dns_enabled = true
}

resource "aws_iam_policy" "lambda_secretsmanager_policy" {
  name        = "lambda-secretsmanager-policy"
  description = "IAM policy for Lambda to access Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ],
        Effect   = "Allow",
        Resource = aws_secretsmanager_secret.db_credentials.arn
      },
    ],
  })
}

resource "aws_iam_role_policy_attachment" "attach_lambda_secretsmanager_policy" {
  role       = module.lambda_function.lambda_role_name
  policy_arn = aws_iam_policy.lambda_secretsmanager_policy.arn
}
