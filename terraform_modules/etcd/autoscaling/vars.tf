variable "max_size" {
  description = "max size for autoscaling group (# instances)"
  default = 3
}

variable "min_size" {
  description = "min size for autoscaling group (# instances)"
  default = 3
}

variable "etcd_launch_config" {
  description = "launch config to use for etcd autoscaling group"
}

variable "private_subnet_id" {
  description = "The ID of the private subnet"
}

variable "etcd_sns_target_arn" {
  description = "arn of the etcd sns target"
}

variable "hook_role_arn" {
  description = "ARN of role allowing autoscaling group to publish to specified SNS/SQS target"
}
