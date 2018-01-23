# AWS etcd autoscaling cluster running CoreOS container Linux
---
This repo contains the Terraform and Ansible scripts to bring up an etcd cluster backed by an AWS autoscaling group using CoreOS instances. 

#### What does this do?

Unmodified, this setup with bring up the following AWS services/pieces:

* VPC
  * private subnet (no public IPs)
  * public subnet 
  * public and private route tables
  * internet gateway
  * NAT gateway
* IAM resources
  * AWS_CLI role allowing etcd ec2 instances to access aws_cli during cluster creation
  * etcd autoscaling role allowing publishing lifecycle hook actions to SNS
  * etcd lambda role allowing lambda function to react to SNS notifications
* Autoscaling group
  * etcd instances running on CoreOS container linux (bootstraps 3 nodes by default)
  * security group for etcd autoscaling instances
  * SNS pieces for publishing and subscribing to autoscaling lifecycle hooks
  * launch configs for cluster bootstrap and cluster member addition/deletion
  * lambda function (Python3.6) triggered by SNS autoscaling notifications that does the work of removing/adding etcd members
  * bastion host that lives in the public subnet and is used to connect to etcd instances for troubleshooting/manual intervention

#### How does it work?

The cluster is bootstrapped via some simple bash scripts and systemd services defined in the `./ignition_files/ignition_static.yml` file. When an instance triggers a lifecycle hook, the hook publishes to an SNS topic. A Python Lambda function is subscribed to this topic and can react based on whether it is a TERMINATE or LAUNCH message. The lambda function has the ability to remove the terminated member from the etcd cluster and add the new member. 

Currently, by pointing the autoscaling group to the existing member launch config after intial bootstrapping will cause any new instances created to be able to join the existing etcd cluster. 

Looking around, others have moved the decision of bootstrapping or joining a cluster to the scripts in the user data that run at the time the instance comes up. It's something to consider but adds complexity and doesn't feel as simple and straightforward to read as a new launch config with just the ETCD_INITIAL_CLUSTER variable changed from 'new' to 'existing'. The complexity in this solution resides in the Python Lambda function but is easier to read/more flexible in how it can be made to handle autoscaling events. ¯\\_(ツ)_/¯

#### Requirements

* Terraform==0.11.1+
* Python==3+
* AWS account

#### Usage

1) Setup the variables that Terraform expects. You can add them directly to the main.tf file or export the following as environment variables with ```export TF_VAR_name_of_variable=<VALUE>```
    * `aws_access_key` (example: `export TF_VAR_aws_access_key=mYrAnDoMkEy`)
    * `aws_secret_key`
    * `aws_region` (us-west-2, us-east-1, etc)
    * `aws_avail_zone` (us-west-2a, us-east-1d, etc)
    * `ec2_public_key` (the public key that will be used for access to your instances)
    
2) In the `./etcd_lambda_zip` directory, you will need to have pip install the requests module:
    * You will want to use a pip version for Python3.6
    * From inside the `etcd_lambda_zip` dir, run: ```pip install requests -t ./```
    * Before zipping the contents of this directory, you can make any changes you'd like to the lambda function. In particular, you can change the `logger.setLevel(logging.INFO)` to `logger.setLevel(logging.DEBUG)` to troubleshoot issues with the Lambda function in CloudWatch
    * zip the contents of the `etcd_lambda_zip` dir into a file called etcdlambda.zip: `zip -r etcdlambda ./*`
    * Copy the `etcdlambda.zip` file to `../terraform_modules/etcd/launch_configs/user_data/`
    
3) Run ```terraform init``` from the root directory of the project (where the main.tf file is)

4) Run ```terraform plan``` and check for any potential issues

5) Run ```terraform apply``` to create the actual resources

Thats it. If all went well, you should be able to terminate one of the etcd instances in the EC2 console and in a short time, have another instance spin up and replace it in the cluster.

You can check the health of the cluster by logging into one of the nodes (through the bastion host) and running `etcdctl cluster-health`

You can also now point your application or Kubernetes master at the cluster as long as they have access to the private subnet.

:warning:
If you see that new instances are coming up but not joined to the cluster, you may need to manually change the autoscaling group:

Once everything is up, go into the AWS console GUI and go to EC2 -> Autoscaling Groups -> Edit the autoscaling group to point to the `etcd_existing_cluster_launch_config`

---

##### Notes

There are definitely improvements that could be made to this setup and Ill hopefully have more time to work on sorting out bugs and more in-depth options, but for now its an easy way to get one of the more annoying pieces of something like a manually built Kubernetes cluster going.

###### TODO
- Fix/make the returns in the inner functions more robust/actually mean something to the calling function

- Add some alerting to let users know if the lambda script fails
