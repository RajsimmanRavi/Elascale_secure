# Elascale_scripts #

Note: I've stopped working on this repo as I created a more updated version of Elascale: https://github.com/RajsimmanRavi/Elascale_secure/

However, you can still use this or the new one as it fits your needs

This repo contains all the scripts required for Elascale deployment including a sample IoT application

All you need is a **m1.medium** flavored VM (based on OpenStack) with **Ubuntu 16-04** image. It may require Ubuntu 14-04 for other nodes (for later deployment).

![alt text](https://github.com/RajsimmanRavi/Elascale_scripts/blob/master/Elascale_diagram.png)

## Steps for deployment ##

### Deployment in an OpenStack Infrastructure ###

You can deploy Elascale on any OpenStack based infrastructure. You just need to edit the following snippet (located on provision_vm.sh) to your platform. **You don't need to edit anything if it's going to be deployed on SAVI platform.**

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

**Note:** We have not tested on any other platform, aside from SAVI infrastructure (which is based on OpenStack)

### Ports Required ###

The following ports need to be opened in the security-group for Elascale to be working properly. **The security group has been created on SAVI platform already.**

| IP Protocol   | From Port  | To Port  |  Description     |
| ------------- |:----------:|:--------:| ----------------:|
| tcp           |     22     |    22    |      SSH         |
| tcp           |     2376   |    2377  |   Docker Daemon  |
| tcp           |     9200   |    9200  |   Elasticsearch  |
| tcp           |     5601   |    5601  |     Kibana       |
| tcp           |     2181   |    2181  |      Zookeeper   |
| tcp           |     9092   |    9092  |      Kafka       |
| tcp           |     9042   |    9042  |      Cassandra   |

### Execute Installation Script ###

1. Get the instalation script: 

```wget https://raw.githubusercontent.com/RajsimmanRavi/Elascale_scripts/master/install_docker_script.sh```

2. Give execution privilege for the script: ```chmod +x install_docker_script.sh```

3. Execute the script: ```sudo ./install_docker_script.sh```

```
This script does the following:
* Installs docker engine
* Installs docker-machine
* Fetches Elascale_scripts repository and stores at /home/ubuntu/Elascale
* Installs elasticdump (and it's prerequisite software such as nodejs and npm)
* Creates a public-private keypair for Elascale engine container to access the swarm-master (the current host)
  * It stores the keypairs and passphrase at /home/ubuntu/Elascale/pass_key 
  * It also adds the public key to /home/ubuntu/.ssh/authorized_keys 
```

### IoT Application Deployment ###

Deploy the IoT application using the following command: ```sudo /home/ubuntu/Elascale/./deploy_iot_app.sh```

**Note:** It requires the SAVI username and password for VM deployment on the infrastructure. 

```
This script does the following:
* First it creates and provisions the appropriate nodes (VMs) for the IoT application: iot-core, iot-edge, iot-agg-sensor
  * It deploys using docker-machine, hence it installs docker when provising each of these nodes
  * It adds the nodes as part of the swarm
* Gets appropriate variables (such as IP addresses) to update the docker_compose/iot_app_compose.yml 
  * This is required such that the application services are deployed at the appropriate nodes (eg. Cassandra service on iot-core node)
* Finally, it deploys the IoT application as a docker stack (using iot_app_compose.yml)
```

You can verify if the services are up and running by using the following command: ```sudo docker service ls```

You can also check whether the application pipeline is working by verifying whether Cassandra database is storing data
```
sudo docker-machine ssh iot-core
sudo docker ps # Get the container_id of the Cassandra database
sudo docker exec -it {container_id} cqlsh
select * from stats.data;
```
### Elascale Deployment ###

Deploy the Elascale using the following command: ```sudo /home/ubuntu/Elascale/./deploy_elascale.sh```

**Note:** It requires the SAVI username and password for VM deployment on the infrastructure

```
The script does the following:
* Creates a worker node "monitor" 
* Installs Elasticsearch and Kibana on that node
* Installs and provisions Metricbeat and Dockbeat for each node on the swarm
  * This involves changing the IP address on the dockbeat.yml and metricbeat.yml and copying them to each node 
  * The swarm-master will then deploy Metricbeat and Dockbeat service, such that performance metrics are sent to Elasticsearch
* Deploys Elascale UI service on the swarm-master
* Deploys Elascale engine service (responsible for auto-scaling micro and macroservices) on the swarm-master
```

Once the script is finished, wait for a few minutes until all the services are up and running. 
You can verify it by using the following command: ```sudo docker service ls ```

Once everything is up, you can view the Elascale UI shown on the script output. ```http://{Elascale_UI_host}:8888```

### Clean up Procedure ###

You can remove the IoT application and it's related components (eg. worker nodes) using the following script:

```sudo /home/ubuntu/Elascale/./clean_iot_app.sh```

You can remove Elascale and all of it's components (eg. monitor node, beats, Elasticsearch, UI etc.) using the following script:

```sudo /home/ubuntu/Elascale/./clean_elascale.sh```

## Contact ##

If you have any questions or comments, please email me at: rajsimmanr@savinetwork.ca













