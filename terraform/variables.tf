variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-southeast-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "trainee-portal"
}

variable "glue_role_arn" {
  description = "ARN of an existing IAM role for Glue (must have S3 + Glue permissions)"
  type        = string
}
