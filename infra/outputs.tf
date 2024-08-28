output "envs" {
  value     = local.envs
  sensitive = true # this is required if the sensitive function was used when loading .env file (more secure way)
}

output "my_lambda_layer_version" {
  value = module.lambda_layer_local.lambda_function_version
}

output "my_awesome_api_fastapi_lambda_arn" {
  value = module.lambda_function.lambda_function_arn
}

output "my_awesome_api_apigw_arn" {
  value = module.api_gateway.api_arn
}

output "my_awesome_api_apigw_execution_arn" {
  value = module.api_gateway.api_execution_arn
}

output "aws_default_vpc_default" {
  value = aws_default_vpc.default
}

output "secret_value" {
  value     = data.aws_secretsmanager_secret_version.db_credentials.secret_string
  sensitive = true
}

output "database_endpoint" {
  value = aws_rds_cluster.postgresql.endpoint
}

output "rds_proxy_endpoint" {
  value = aws_db_proxy.my_awesome_rds_proxy.endpoint
}

output "apigw_endpoint_url" {
  value = module.api_gateway.api_endpoint
}