resource "aws_db_subnet_group" "default" {
  name       = "my-rds-subnet-group"
  subnet_ids = data.aws_subnets.default.ids
}

resource "aws_rds_cluster" "postgresql" {
  cluster_identifier        = "my-aurora-cluster"
  engine                    = "aurora-postgresql"
  availability_zones        = ["eu-west-1a", "eu-west-1b", "eu-west-1c"]
  database_name             = lookup(local.envs, "DATABASE_NAME")
  master_username           = jsondecode(data.aws_secretsmanager_secret_version.db_credentials.secret_string)["username"]
  master_password           = jsondecode(data.aws_secretsmanager_secret_version.db_credentials.secret_string)["password"]

  final_snapshot_identifier = "my-cluster-final-snapshot"
  skip_final_snapshot       = true
  vpc_security_group_ids = [
    aws_security_group.rds_sg.id,
    aws_security_group.rds_access_from_my_ip.id
  ]
  db_subnet_group_name      = aws_db_subnet_group.default.name  # Use the new subnet group

  depends_on                = [
    null_resource.load_env,
    aws_default_vpc.default,
    aws_secretsmanager_secret_version.db_credentials
  ]
}

resource "aws_rds_cluster_instance" "default-instance" {
  count                = 2
  cluster_identifier   = aws_rds_cluster.postgresql.cluster_identifier
  instance_class       = lookup(local.envs, "DATABASE_INSTANCE_SIZE", "db.r5.large")
  db_subnet_group_name = aws_rds_cluster.postgresql.db_subnet_group_name
  engine               = aws_rds_cluster.postgresql.engine
  engine_version       = aws_rds_cluster.postgresql.engine_version
  publicly_accessible  = true

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_iam_role" "rds_proxy_role" {
  name = "RDSProxyRole"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "rds.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role_policy" "rds_proxy_role_policy" {
  name = "RDSProxyRolePolicy"
  role = aws_iam_role.rds_proxy_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue",
        ]
        Effect   = "Allow"
        Resource = "${aws_secretsmanager_secret.db_credentials.arn}"
      },
    ]
  })
}

resource "aws_db_proxy" "my_awesome_rds_proxy" {
  name                   = "my-awesome-rds-proxy"
  debug_logging          = true
  engine_family          = "POSTGRESQL"
  idle_client_timeout    = 60
  require_tls            = false
  role_arn               = aws_iam_role.rds_proxy_role.arn
  vpc_security_group_ids = [aws_security_group.rds_proxy_sg.id]
  vpc_subnet_ids         = data.aws_subnets.default.ids

  auth {
    auth_scheme = "SECRETS"
    description = "my-awesome-rds-proxy"
    iam_auth    = "DISABLED"
    secret_arn  = aws_secretsmanager_secret.db_credentials.arn
  }

  depends_on = [
    aws_rds_cluster.postgresql
  ]
}

resource "aws_db_proxy_default_target_group" "my_rds_proxy_target_group" {
  db_proxy_name = aws_db_proxy.my_awesome_rds_proxy.name

  connection_pool_config {
    connection_borrow_timeout    = 60
    max_connections_percent      = 100
    init_query                   = "" # Postgres do not support this
    max_idle_connections_percent = 50
    session_pinning_filters      = ["EXCLUDE_VARIABLE_SETS"]
  }
}

resource "aws_db_proxy_target" "my_proxy_target" {
  db_cluster_identifier = aws_rds_cluster.postgresql.id
  db_proxy_name         = aws_db_proxy.my_awesome_rds_proxy.name
  target_group_name     = aws_db_proxy_default_target_group.my_rds_proxy_target_group.name
}