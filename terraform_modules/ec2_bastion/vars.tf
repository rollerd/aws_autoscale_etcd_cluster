variable "vpc_id" {
  description = "VPC ID"
}

variable "bastion_sec_grp_name" {
  default = "bastion_sec_grp"
}

variable "key_name" {
  description = "key pair name"
}

variable "subnet_id" {
  description = "public subnet id"
}
