resource "aws_sns_topic" "etcd" {
  name = "etcd_lifecycle_update"
}

resource "aws_sns_topic_subscription" "lambda" {
  topic_arn = "${aws_sns_topic.etcd.arn}"
  protocol = "lambda"
  endpoint = "${var.lambda_sns_arn}"
}

# --- OUTPUTS ---
output "etcd_sns_topic_arn" {
  value = "${aws_sns_topic.etcd.arn}"
}
