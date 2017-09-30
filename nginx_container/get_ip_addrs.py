import docker
import time

# read from /var/run/docker.sock
client = docker.from_env()

# This is to check whether both Elasticsearch and Kibana are up and running
service_list = []

# This is to get their internal IP addrs
ip_list = []

# Run forever, waiting for Elasticsearch and kibana to be up and running
while 1:

    for srv in client.services.list():
        service_list.append(client.services.get(srv.id).name)

    if any("elasticsearch" in s for s in service_list) and any("kibana" in s for s in service_list):
        break
    else:
        print "Both services not up and running...Wait for 5 seconds to recheck..."
        print str(service_list)

    time.sleep(5)

print "Both are up and running!"

# When both are running, get their IP addresses
for srv in client.services.list():

    # Get hostname of service
    name = client.services.get(srv.id).name

    ip = client.services.get(srv.id).attrs['Endpoint']['VirtualIPs'][0]['Addr'].split("/")[0]

    if "elasticsearch" in name:
        ip_list.append("ELASTICSEARCH:"+str(ip))
    elif "kibana" in name:
        ip_list.append("KIBANA:"+str(ip))

# It doesn't which order it prints, I grep it using the keywords (i.e ELASTICSEARCH AND KIBANA)
print ip_list[0]
print ip_list[1]
