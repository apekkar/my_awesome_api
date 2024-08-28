module "api_gateway" {
  source = "terraform-aws-modules/apigateway-v2/aws"

  name          = "my-awesome-apigw"
  description   = "My awesome HTTP API Gateway"
  protocol_type = "HTTP"

  cors_configuration = {
    allow_headers = ["content-type", "x-amz-date", "authorization", "x-api-key", "x-amz-security-token", "x-amz-user-agent"]
    allow_methods = ["*"]
    allow_origins = ["*"]
  }

  create_domain_name = false # Disable custom domain creation if not needed

  # Access logs
  stage_access_log_settings = {
    create_log_group            = true
    log_group_retention_in_days = 7
    format = jsonencode({
      context = {
        integrationErrorMessage = "$context.integrationErrorMessage"
        protocol                = "$context.protocol"
        requestId               = "$context.requestId"
        requestTime             = "$context.requestTime"
        responseLength          = "$context.responseLength"
        routeKey                = "$context.routeKey"
        stage                   = "$context.stage"
        status                  = "$context.status"
        error = {
          message      = "$context.error.message"
          responseType = "$context.error.responseType"
        }
        identity = {
          sourceIP = "$context.identity.sourceIp"
        }
        integration = {
          error             = "$context.integration.error"
          integrationStatus = "$context.integration.integrationStatus"
        }
      }
    })
  }

  # Routes & Integration(s)
  routes = {
    "ANY /{proxy+}" = {
      integration = {
        type = "AWS_PROXY"
        uri  = module.lambda_function.lambda_function_arn
      }
    }
  }

  vpc_links = {
    default = {
      name               = aws_default_vpc.default.id
      security_group_ids = [data.aws_security_group.default.id]
      subnet_ids         = data.aws_subnets.default.ids
    }
  }
  depends_on = [ 
    aws_default_vpc.default
  ]
}