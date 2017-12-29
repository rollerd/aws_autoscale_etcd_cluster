variable "etcd_lambda_role_arn" {
  description = "arn for the etcd lambda role"
}

variable "subnet_ids" {
  description = "List of subnet ids associated with the lambda function"
}

variable "security_group_ids" {
  description = "List of security groups associated with the lambda function"
}

variable "sns_topic_arn" {
  description = "arn for etcd SNS topic"
}
