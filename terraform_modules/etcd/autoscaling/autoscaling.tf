resource "aws_autoscaling_group" "etcd" {
  name = "etcd_autoscaling_group"
  max_size = "${var.max_size}"
  min_size = "${var.min_size}"
  launch_configuration = "${var.etcd_launch_config}"
  vpc_zone_identifier = ["${var.private_subnet_id}"]

  lifecycle {
    ignore_changes = ["launch_configuration"]
  }

  tag {
    key = "Name"
    value = "etcd"
    propagate_at_launch = true
  }
}

resource "aws_autoscaling_lifecycle_hook" "etcd_terminate" {
  name = "etcd_hook_instance_terminate"
  autoscaling_group_name = "${aws_autoscaling_group.etcd.name}"
  default_result = "ABANDON"
  heartbeat_timeout = 3600
  lifecycle_transition = "autoscaling:EC2_INSTANCE_TERMINATING"
  notification_target_arn = "${var.etcd_sns_target_arn}"
  role_arn = "${var.hook_role_arn}"
  notification_metadata = <<EOF
{
  "transition": "TERMINATING"
}
EOF
}

resource "aws_autoscaling_lifecycle_hook" "etcd_launch" {
  name = "etcd_hook_instance_launch"
  autoscaling_group_name = "${aws_autoscaling_group.etcd.name}"
  default_result = "ABANDON"
  heartbeat_timeout = 3600
  lifecycle_transition = "autoscaling:EC2_INSTANCE_LAUNCHING"
  notification_target_arn = "${var.etcd_sns_target_arn}"
  role_arn = "${var.hook_role_arn}"
  notification_metadata = <<EOF
{
  "transition": "LAUNCHING"
}
EOF
}


# --- OUTPUTS ---
output "etcd_autoscaling_group_name" {
  value = "${aws_autoscaling_group.etcd.name}"
}

