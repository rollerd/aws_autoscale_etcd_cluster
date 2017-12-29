# ---ETCD AUTOSCALING---
resource "aws_launch_configuration" "etcd_new_cluster" {
  name = "etcd_new_cluster_launch_config"
  image_id = "${var.ami_id}"
  instance_type = "${var.instance_type}"
  iam_instance_profile = "${var.aws_iam_instance_profile}"
  key_name = "${var.key_pair}"
  security_groups = ["${var.etcd_security_group}"]
  associate_public_ip_address = false
  user_data = "${file("${path.module}/user_data/ignition_new_cluster.txt")}"
}

resource "aws_launch_configuration" "etcd_existing_cluster" {
  name = "etcd_existing_cluster_launch_config"
  image_id = "${var.ami_id}"
  instance_type = "${var.instance_type}"
  iam_instance_profile = "${var.aws_iam_instance_profile}"
  key_name = "${var.key_pair}"
  security_groups = ["${var.etcd_security_group}"]
  associate_public_ip_address = false
  user_data = "${file("${path.module}/user_data/ignition_existing_cluster.txt")}"
}

# --- OUTPUTS ---
output "etcd_launch_config_new" {
  value = "${aws_launch_configuration.etcd_new_cluster.id}"
}

output "etcd_launch_config_existing" {
  value = "${aws_launch_configuration.etcd_existing_cluster.id}"
}
