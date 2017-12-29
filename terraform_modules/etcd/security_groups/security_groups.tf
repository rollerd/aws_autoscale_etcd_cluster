# ---SECURITY GROUP---
resource "aws_security_group" "etcd" {
  name = "etcd security group"
  description = "etcd3 security group"
  vpc_id = "${var.vpc_id}"

  ingress {
    from_port = 2379
    to_port = 2379
    protocol = "tcp"
    cidr_blocks = ["10.100.2.0/24"]
  }

  ingress {
    from_port = 2380
    to_port = 2380
    protocol = "tcp"
    cidr_blocks = ["10.100.2.0/24"]
  }

  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = ["10.100.1.0/24"]
  }

  ingress {
    from_port = 2379
    to_port = 2379
    protocol = "tcp"
    cidr_blocks = ["10.100.1.0/24"]
  }

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
    Name = "${var.etcd_sec_grp_name}"
  }
}

output "etcd_security_group" {
    value = "${aws_security_group.etcd.id}"
}
