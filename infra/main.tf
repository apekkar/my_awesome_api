terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.37.0"
    }
  }

  required_version = ">= 1.2.0"
}

provider "aws" {
  region  = local.envs["MY_AWS_REGION"]
  profile = local.envs["MY_AWS_PROFILE"]
}

resource "aws_default_vpc" "default" {
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
    Name = "Default VPC"
  }
}

data "aws_security_group" "default" {
  vpc_id = aws_default_vpc.default.id
  filter {
    name   = "group-name"
    values = ["default"]
  }
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [aws_default_vpc.default.id]
  }
}

resource "null_resource" "load_env" {
  provisioner "local-exec" {
    command = "python3 -c 'import os, json; print(json.dumps({k: v for k, v in (line.split(\"=\") for line in open(\"./../.env\") if line.strip() and not line.startswith(\"#\"))}))' > ${path.module}/../infra/env_vars.json"
  }
  triggers = {
    always_run = "${timestamp()}"
  }
}

data "local_file" "env_vars" {
  depends_on = [null_resource.load_env]
  filename   = "${path.module}/../infra/env_vars.json"
}


