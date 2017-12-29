#  ---VPC---
resource "aws_vpc" "main" {
  cidr_block = "${var.vpc_cidr_block}"
  enable_dns_support = "${var.vpc_enable_dns_support}"
  enable_dns_hostnames = "${var.vpc_enable_dns_hostnames}"

  tags {
    Name = "${var.vpc_tag_name}"
  }
}

# ---SUBNETS---
resource "aws_subnet" "public_subnet" {
  vpc_id = "${aws_vpc.main.id}"
  availability_zone = "${var.aws_avail_zone}"
  cidr_block = "${var.public_subnet_cidr}"

  tags {
    Name = "${var.public_subnet_name}"
  }
}

resource "aws_subnet" "private_subnet" {
  vpc_id = "${aws_vpc.main.id}"
  availability_zone = "${var.aws_avail_zone}"
  cidr_block = "${var.private_subnet_cidr}"

  tags {
    Name = "${var.private_subnet_name}"
  }
}

# ---INTERNET GATEWAYS---
resource "aws_internet_gateway" "gw" {
  vpc_id = "${aws_vpc.main.id}"

  tags {
    Name = "${var.internet_gw_name}"
  }
}

# ---ROUTE TABLES---
resource "aws_route_table" "pub_route_table" {
  vpc_id = "${aws_vpc.main.id}"

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = "${aws_internet_gateway.gw.id}"
  }

  tags {
    Name = "${var.public_route_table_name}"
  }
}

resource "aws_route_table" "priv_route_table" {
  vpc_id = "${aws_vpc.main.id}"

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = "${aws_nat_gateway.nat_gw.id}"
  }

  tags {
    Name = "${var.private_route_table_name}"
  }
}

resource "aws_route_table_association" "priv_route_assoc" {
  subnet_id = "${aws_subnet.private_subnet.id}"
  route_table_id = "${aws_route_table.priv_route_table.id}"
}

resource "aws_route_table_association" "pub_route_assoc" {
  subnet_id = "${aws_subnet.public_subnet.id}"
  route_table_id = "${aws_route_table.pub_route_table.id}"
}

# ---ELASTIC IP---
resource "aws_eip" "etcd_elastic_ip" {
  vpc = true
}

# ---NAT GATEWAY---
resource "aws_nat_gateway" "nat_gw" {
  allocation_id = "${aws_eip.etcd_elastic_ip.id}"
  subnet_id = "${aws_subnet.public_subnet.id}"

  depends_on = ["aws_internet_gateway.gw"]
}

# --- OUTPUTS ---
output "public_subnet" {
  value = "${aws_subnet.public_subnet.id}"
}

output "private_subnet" {
  value = "${aws_subnet.private_subnet.id}"
}

output "vpc_id" {
  value = "${aws_vpc.main.id}"
}
