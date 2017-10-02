import docker
import time

# read from /var/run/docker.sock
client = docker.from_env()

# This is to check whether both Elasticsearch and Kibana are up and running
net_list = []

# This is to get their internal IP addrs
ip_dict = {}

# Run forever, waiting for Elasticsearch and kibana to be up and running
while 1:

    for net in client.networks.list():
        # Network must contain the keyword 'monitor'
        if "monitor" in client.networks.get(net.id).name:

            for cont in client.containers.list():

                cont_id = cont.id

                if "elasticsearch" in client.containers.get(cont_id).name and "elasticsearch" not in ip_dict:
                    ip_dict["elasticsearch"] = client.containers.get(cont_id).attrs['NetworkSettings']['Networks'][net.name]['IPAMConfig']['IPv4Address']

                if "kibana" in client.containers.get(cont_id).name and "kibana" not in ip_dict:
                    ip_dict["kibana"] = client.containers.get(cont_id).attrs['NetworkSettings']['Networks'][net.name]['IPAMConfig']['IPv4Address']

    if len(ip_dict) == 2:
        break
    else:
        time.sleep(5)

print "ELASTICSEARCH:"+str(ip_dict["elasticsearch"])
print "KIBANA:"+str(ip_dict["kibana"])
