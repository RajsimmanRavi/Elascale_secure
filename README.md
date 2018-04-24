# Elascale_secure
Elascale is an autoscaling solution for both microservices and VMs on cloud environments. Elascale utilizes Docker Swarm and Docker-machine for managing microservices and VMs respectively. Note that microservices need to be deployed by Docker services (not just containers) in order for functioning properly. For more information, please refer to the following link: https://docs.docker.com/engine/swarm/how-swarm-mode-works/services/#services-tasks-and-containers

All you need is a **m1.medium** flavored VM (based on OpenStack) with **Ubuntu 16-04** image. It may require Ubuntu 14-04 for other nodes (for later deployment).

![alt text](https://github.com/RajsimmanRavi/Elascale_secure/blob/master/elascale_arch.png)

## Changes from the previous Elascale version ##
There has been major improvements since the original prototype (https://github.com/RajsimmanRavi/Elascale_scripts). The following highlights are:

    * Incorporated NGINX for access control and encryption
    * HTTPS-based encrypted channels to prevent eavesdropping/information leakage
    * Basic authentication for Elascale UI and Kibana
    * XSRF protection for Elascale UI 

## Steps for deployment ##

### Deployment in an OpenStack Infrastructure ###

You can deploy Elascale on any OpenStack based infrastructure. You just need to edit the following snippet (located on provision_vm.sh) to your platform. If you have any problems creating VMs, this snippet could be the issue. Make sure the arguments to this command (such as auth-url, sec-groups etc.) work on your platform. 

### Network Monitoring Configuration ### 
There are a couple of things that need to be configured for proper network monitoring:

* Make sure you build the correct graph in setup_topology.py
* Make sure the ports are correctly set in the graph
* Make sure you have the correct MACs and IPs in engine_config.py 

This is not started by default. You can start by running get_netstats.py 

```
sudo docker-machine create --driver openstack \
    --openstack-auth-url "xxxx" \
    --openstack-insecure \
    --openstack-flavor-name xxxx --openstack-image-name "Ubuntu-14-04" \
    --openstack-tenant-name "xxxx" --openstack-region "xxxx" \
    --openstack-sec-groups "xxxx" --openstack-ssh-user "ubuntu" \
    --openstack-username $USERNAME --openstack-password $PASSWORD \
    $VM_NAME
```
In fact, you can deploy on other non-OpenStack based platforms as well, as long it has the docker-machine drivers. 

**Note:** We have not tested on any other platform, aside from SAVI infrastructure (which is based on OpenStack). Just make sure your **vm-name** is prefixed with **iot-** as the autoscaling engine only recognizes those VMs.

### Ports Required ###

The following ports need to be opened in the security-group for Elascale to be working properly. **In SAVI platform, make sure the secgroup (savi-iot) is created for that appropriate tenant/region.**

| IP Protocol   | From Port  | To Port  |  Description     |
| ------------- |:----------:|:--------:| ----------------:|
| tcp           |     22     |    22    |   SSH            |
| tcp           |     2376   |    2377  |   Docker Daemon  |
| tcp           |     9200   |    9200  |   Elasticsearch  |
| tcp           |     5601   |    5601  |   Kibana         |
| tcp           |     2181   |    2181  |   Zookeeper      |
| tcp           |     9092   |    9092  |   Kafka          |
| tcp           |     9042   |    9042  |   Cassandra      |
| tcp           |     8888   |    8888  |   Elascale UI    |
| tcp           |     443    |    443   |   HTTPS          |

## Execute Installation Script

Get the instalation script:

```wget https://raw.githubusercontent.com/RajsimmanRavi/Elascale_secure/master/prepare_master.sh```

Give execution privilege for the script: ```chmod +x prepare_master.sh```

Execute the script: ```sudo ./prepare_master.sh```

This script does the following:
* Installs docker engine
* Installs docker-machine
* Installs elasticdump (and it's prerequisite software such as nodejs and npm)
* Installs htpasswd for basic authentication required for Kibana UI access
* Installs prerequisite tools to create X509 certificates 
* Fetches Elascale_scripts repository and stores at /home/ubuntu/Elascale_secure
* Creates a public-private keypair for Elascale engine container to access the swarm-master (the current host)
  * It stores the keypairs and passphrase at /home/ubuntu/Elascale_secure/pass_key 
  * It also adds the public key to /home/ubuntu/.ssh/authorized_keys 

## Example IoT Application Deployment

This is an example IoT Application developed for a scientific research paper. You can use this application to learn how Elascale works on this environment. The architecture of the application is shown below: 

![alt text](https://github.com/RajsimmanRavi/Elascale_secure/blob/master/Elascale_secure.png)

Deploy the IoT application using the following command: ```sudo /home/ubuntu/Elascale_secure/./deploy_iot_app.sh```

Note: It requires the SAVI username and password for VM deployment on the infrastructure.

This script does the following:
* First it creates and provisions the appropriate nodes (VMs) for the IoT application: iot-core, iot-edge, iot-agg-sensor
  * It deploys using docker-machine, hence it installs docker when provising each of these nodes
  * It adds the nodes as part of the swarm
* Gets appropriate variables (such as IP addresses) to update the docker_compose/iot_app_compose.yml 
  * This is required such that the application services are deployed at the appropriate nodes (eg. Cassandra service on iot-core node)
* Finally, it deploys the IoT application as a docker stack (using iot_app_compose.yml)
You can verify if the services are up and running by using the following command: ```sudo docker service ls```

You can also check whether the application pipeline is working by verifying whether Cassandra database is storing data
```
sudo docker-machine ssh iot-core
sudo docker ps # Get the container_id of the Cassandra database
sudo docker exec -it {container_id} cqlsh
select * from stats.data;
```

## Elascale Deployment

After deploying your (or above) application, you can deploy the Elascale platform.

Deploy the Elascale using the following command: ```sudo /home/ubuntu/Elascale_secure/./deploy_elascale.sh```

Note: It requires the SAVI username and password for VM deployment on the infrastructure

The script does the following:
* Creates a worker node "monitor" 
* Installs Elasticsearch and Kibana on that node
* Installs and provisions Metricbeat and Dockbeat for each node on the swarm
  * This involves changing the IP address on the dockbeat.yml and metricbeat.yml and copying them to each node 
  * The swarm-master will then deploy Metricbeat and Dockbeat service, such that performance metrics are sent to Elasticsearch
* Deploys Elascale UI service on the swarm-master
* Deploys Elascale engine service (responsible for auto-scaling micro and macroservices) on the swarm-master
Once the script is finished, wait for a few minutes until all the services are up and running. You can verify it by using the following command: sudo docker service ls

Once everything is up, you can view the Elascale UI shown on the script output. ```https://{Elascale_UI_host}:8888```

## Clean up Procedure

You can remove the example IoT application and it's related components (eg. worker nodes) using the following script:

```sudo /home/ubuntu/Elascale_secure/./clean_iot_app.sh```

You can remove Elascale and all of it's components (eg. monitor node, beats, Elasticsearch, UI etc.) using the following script:

```sudo /home/ubuntu/Elascale_secure/./clean_elascale.sh```

## Contact

If you have any questions or comments, please email me at: rajsimmanr@savinetwork.ca
