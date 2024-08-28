resource "null_resource" "create_layer" {
  triggers = {
    shell_hash = "${sha256(file("${path.module}/../requirements.txt"))}"
    always_run = "${timestamp()}"
  }

  provisioner "local-exec" {
    command = "${path.module}/../infra/scripts/install.sh"
  }
}

module "lambda_layer_local" {
  source = "terraform-aws-modules/lambda/aws"

  create_layer = true

  layer_name               = "my-lambda-layer"
  description              = "My amazing lambda layer (deployed from local)"
  architectures            = ["x86_64"]
  compatible_architectures = ["x86_64"]

  source_path = "${path.module}/../infra/layers/"
  depends_on  = [
    aws_default_vpc.default,
    null_resource.create_layer
  ]
}

module "lambda_function" {
  source = "terraform-aws-modules/lambda/aws"

  function_name            = "my_awesome_api"
  description              = "My awesome api lambda function"
  handler                  = "main.handler"
  architectures            = ["x86_64"]
  compatible_architectures = ["x86_64"]
  runtime                  = "python3.12"
  compatible_runtimes      = ["python3.12"]
  timeout                  = 30
  memory_size              = 512
  publish                  = true

  source_path = "${path.module}/../my_awesome_api"

  vpc_subnet_ids         = data.aws_subnets.default.ids
  vpc_security_group_ids = [aws_security_group.lambda_sg.id]

  environment_variables = jsondecode(data.local_file.env_vars.content)
  layers = [
    module.lambda_layer_local.lambda_layer_arn,
  ]

  allowed_triggers = {
    AllowExecutionFromAPIGateway = {
      service    = "apigateway"
      source_arn = "${module.api_gateway.api_execution_arn}/*/*/*"
    }
  }

  depends_on = [
    module.lambda_layer_local,
    aws_db_proxy.my_awesome_rds_proxy,
    aws_secretsmanager_secret.db_credentials
  ]
}

resource "aws_iam_role_policy_attachment" "AWSLambdaVPCAccessExecutionRole" {
  role       = module.lambda_function.lambda_role_name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "null_resource" "clean_up" {
  triggers = {
    lambda_function_version = module.lambda_function.lambda_function_version
    layer_hash              = module.lambda_layer_local.lambda_function_source_code_hash
  }
  depends_on = [module.lambda_function]
  provisioner "local-exec" {
    command = "${path.module}/../infra/scripts/clean.sh"
  }
}

resource "aws_lambda_alias" "live" {
  name             = "live"
  function_name    = module.lambda_function.lambda_function_name
  function_version = "$LATEST"
  depends_on       = [module.lambda_function]
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_alias.live.arn
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${module.api_gateway.api_execution_arn}}/*/*/*"
  depends_on    = [
    aws_lambda_alias.live,
    module.api_gateway.api_execution_arn
  ]
}