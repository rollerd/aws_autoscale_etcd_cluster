variable "access_key" {}
variable "secret_key" {}
variable "aws_region" {}
variable "ec2_public_key" {}
variable "aws_avail_zone" {}

# Configure our provider (AWS in this case)
provider "aws" {
  access_key = "${var.access_key}"
  secret_key = "${var.secret_key}"
  region     = "${var.aws_region}"
  version    = "~> 1.1"
}

module "vpc" {
  source = "./terraform_modules/vpc"
  aws_avail_zone = "${var.aws_avail_zone}"
}

module "iam" {
  source = "./terraform_modules/iam"
  ec2_public_key = "${var.ec2_public_key}"
}

module "etcd_security_groups" {
  source = "./terraform_modules/etcd/security_groups"
  vpc_id = "${module.vpc.vpc_id}"
}

module "etcd_launch_configs" {
  source = "./terraform_modules/etcd/launch_configs"
  aws_iam_instance_profile = "${module.iam.aws_iam_instance_profile}"
  etcd_security_group = "${module.etcd_security_groups.etcd_security_group}"
  key_pair = "${module.iam.key_name}"
}

module "etcd_lambda" {
  source = "./terraform_modules/etcd/lambda"
  etcd_lambda_role_arn = "${module.iam.lambda_etcd_role_arn}"
  subnet_ids = "${module.vpc.private_subnet}"
  security_group_ids = "${module.etcd_security_groups.etcd_security_group}"
  sns_topic_arn = "${module.etcd_sns.etcd_sns_topic_arn}"
}

module "etcd_sns" {
  source = "./terraform_modules/etcd/sns"
  lambda_sns_arn = "${module.etcd_lambda.etcd_lambda_alias_arn}"
}

module "etcd_autoscaling" {
  source = "./terraform_modules/etcd/autoscaling"
  private_subnet_id = "${module.vpc.private_subnet}"
  etcd_launch_config = "${module.etcd_launch_configs.etcd_launch_config_new}"
  hook_role_arn = "${module.iam.etcd_iam_role_arn}"
  etcd_sns_target_arn = "${module.etcd_sns.etcd_sns_topic_arn}"
}

module "bastion" {
  source = "./terraform_modules/ec2_bastion"
  key_name = "${module.iam.key_name}"
  vpc_id = "${module.vpc.vpc_id}"
  subnet_id = "${module.vpc.public_subnet}"
}
