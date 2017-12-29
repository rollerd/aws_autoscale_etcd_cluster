### USAGE

The required ignition format files are already included here (etcd\_new\_cluster.txt and etcd\_existing\_cluster.txt) but can be modified using the info below:

In order to get our user data into the proper format for CoreOS to use, we must complete a few steps

See [CoreOS provisioning docs](https://coreos.com/os/docs/1618.0.0/provisioning.html) for more info

Basically we:

* Create a Linux Container Config yaml file with the desired info
* Use the CoreOS [config transpiler](https://github.com/coreos/container-linux-config-transpiler) to convert the config file to the [Ignition](https://coreos.com/ignition/docs/latest/what-is-ignition.html) format:
```
ct -platform ec2 -in-file <filename> -out-file <filename2> 
```
* Copy the ignition\_new\_cluster.txt and ignition\_existing\_cluster.txt files to `../terraform_modules/etcd/launch_configs/user_data/` directory


So in our case we run:
```
ct -platform ec2 -in-file ignition_static.yml -out-file ignition_new_cluster.txt
```
The ignition 'new' and 'existing' files have been included here so you can just use those if you'd like

#### NOTES:

This container linux config includes the following services and files:

* etcd\_bootstrap.service that creates a cluster\_data.txt file containing variables we need to bootstrap or join a cluster. It pulls and runs an aws\_cli docker container to gather the required info.
* etcd-member.service drop-in to tell the service to use the variables provided by the etcd\_bootstrap service cluster\_data.txt file.
* networkcheck.service runs the networkcheck.sh script which is a bit of hack for ensuring that the etcd\_bootstrap service wont run before the network can reach the internet. `Requires=network-online.target` doesn't guarantee internet access so the aws\_cli container image that runs in etcd\_bootstrap service wouldnt be able to be pulled and bootstrapping a cluster would fail. 
* The etcd\_bootstrap.sh and networkcheck.sh files 
* The directive for Ignition to configure and start the etcd service (a rkt container)
