# ----- AWS CLI POLICY ------
resource "aws_iam_role" "aws_cli_role" {
  name = "aws_cli_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "aws_cli_role_policy" {
  name = "aws_cli_policy"
  role = "${aws_iam_role.aws_cli_role.id}"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": ["ec2:Describe*"], "Resource": ["*"]},
    {"Effect": "Allow", "Action": "elasticloadbalancing:Describe*", "Resource": "*"},
    {"Effect": "Allow", "Action": ["cloudwatch:ListMetrics", "cloudwatch:GetMetricStatistics", "cloudwatch:Describe*"], "Resource": "*"},
    {"Effect": "Allow", "Action": "autoscaling:Describe*", "Resource": "*"}
  ]
}
EOF
}

# ----- ETCD AUTOSCALE SNS ROLE POLICY -----
resource "aws_iam_role" "etcd_autoscale_role" {
  name = "etcd_autoscale_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "autoscaling.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "etcd_autoscale_role_policy" {
  name = "etcd_autoscale_role_policy"
  role = "${aws_iam_role.etcd_autoscale_role.id}"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": ["sqs:SendMessage", "sqs:GetQueueUrl", "sns:Publish"], "Resource": "*"}
  ]
}
EOF
}

# ----- LAMBDA AUTOSCALE SNS AND AUTOSCALE POLICY -----
resource "aws_iam_role" "lambda" {
  name = "lambda_etcd_autoscale_role"
  
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "lambda" {
  name = "lambda_etcd_autoscale_policy"
  role = "${aws_iam_role.lambda.id}"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect": "Allow", "Action": ["logs:CreateLogStream", "logs:PutLogEvents", "logs:CreateLogGroup"], "Resource": "*"},
    {"Effect": "Allow", "Action": "autoscaling:*", "Resource": "*"},
    {"Effect": "Allow", "Action": ["sns:GetTopicAttributes", "sns:List*"], "Resource": "*"},
    {"Effect": "Allow", "Action": ["lambda:List*", "lambda:Get*", "lambda:Invoke","lambda:InvokeFunction"], "Resource": "arn:aws:lambda:*:*:function:*"},
    {"Effect": "Allow", "Action": ["ec2:DeleteNetworkInterface", "ec2:CreateNetworkInterface", "ec2:DescribeNetworkInterfaces", "ec2:DescribeInstances"], "Resource": "*"}
  ]
}
EOF
}

# This will show as an error in the IDE, but the warning is for a deprecated argument
resource "aws_iam_instance_profile" "aws_cli_profile" {
  name = "aws_cli_profile"
  role = "${aws_iam_role.aws_cli_role.id}"
}

# ---INSTANCE KEYPAIR---
resource "aws_key_pair" "ec2_keypair" {
  key_name   = "ec2_key"
  public_key = "${var.ec2_public_key}" 
}

# --- OUTPUTS ---
output "aws_iam_instance_profile" {
  value = "${aws_iam_instance_profile.aws_cli_profile.id}"
}

output "key_name" {
  value = "${aws_key_pair.ec2_keypair.id}"
}

output "etcd_iam_role_arn" {
  value = "${aws_iam_role.etcd_autoscale_role.arn}"
}

output "lambda_etcd_role_arn" {
  value = "${aws_iam_role.lambda.arn}"
}
