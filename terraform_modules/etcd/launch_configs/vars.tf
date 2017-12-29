variable "ami_id" {
  description = "ami id for etcd autoscaling instances"
  default = "ami-c167bdb9"
}

variable "instance_type" {
  description = "aws instance type (t2.micro, m4.large, etc)"
  default = "t2.micro"
}

variable "aws_iam_instance_profile" {
  description = "etcd instance iam profile"
}

variable "key_pair" {
  description = "key pair for logging into instances"
}

variable "etcd_security_group" {
  description = "etcd security group"
}
