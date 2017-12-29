# ----- AWS LAMBDA FUNCTIONS -----
resource "aws_lambda_function" "etcd" {
  filename = "${path.module}/files/etcdlambda.zip"
  function_name = "etcd_lambda"
  role = "${var.etcd_lambda_role_arn}"
  handler = "etcd_lambda.kickoff" 
  runtime = "python3.6"
  timeout = "30"
  publish = true
  description = "lambda function for adding/removing etcd cluster nodes during autoscale"
  vpc_config {
    subnet_ids = ["${var.subnet_ids}"]
    security_group_ids = ["${var.security_group_ids}"]
  }
}

resource "aws_lambda_alias" "etcd" {
  name = "etcd_lambda_alias"
  description = "alias for lambda SNS autoscaling notification function"
  function_name = "${aws_lambda_function.etcd.arn}"
  function_version = "$LATEST"
}

resource "aws_lambda_permission" "allow_sns" {
  statement_id = "AllowExecutionFromSNS"
  action = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.etcd.function_name}"
  principal = "sns.amazonaws.com"
  source_arn = "${var.sns_topic_arn}"
  qualifier = "${aws_lambda_alias.etcd.name}"
}

# --- OUTPUTS ---
output "etcd_lambda_arn" {
  value = "${aws_lambda_function.etcd.qualified_arn}"
}

output "etcd_lambda_alias_arn" {
  value = "${aws_lambda_alias.etcd.arn}"
}
