resource "aws_security_group" "bastion" {
  name = "bastion host security group"
  description = "bastion host security group"
  vpc_id = "${var.vpc_id}"

  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags {
    Name = "${var.bastion_sec_grp_name}"
  }
}

resource "aws_instance" "bastion" {
  ami = "ami-8ca83fec"
  instance_type = "t2.micro"
  key_name = "${var.key_name}"
  vpc_security_group_ids = ["${aws_security_group.bastion.id}"]
  associate_public_ip_address = true
  subnet_id = "${var.subnet_id}"

  tags {
    Name = "bastion"
  }

  depends_on = ["aws_security_group.bastion"]
}

# --- OUTPUTS ---
output "bastion_sec_grp" {
  value = "${aws_security_group.bastion.id}"
}
