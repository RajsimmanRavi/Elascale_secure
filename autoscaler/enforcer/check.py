import json
import time
import os
import configparser
from datetime import datetime
#import gevent
from autoscaler.conf import engine_config as eng
from autoscaler import util

from datetime import datetime

inspect_vm = util.run_command("sudo docker-machine inspect iot-edge")
vm_json = json.loads(inspect_vm,'utf-8')
vm_info = {}
vm_name = "iot-edge"

username = vm_json['Driver']['Username']
password = vm_json['Driver']['Password']
auth_url = vm_json['Driver']['AuthUrl']
region = vm_json['Driver']['Region']
tenant = vm_json['Driver']['TenantName']
flavor = vm_json['Driver']['FlavorName']
image = vm_json['Driver']['ImageName']
network_name = vm_json['Driver']['NetworkName']
network_id = vm_json['Driver']['NetworkId']

create_vm_cmd = "sudo docker-machine create --driver openstack \
    --openstack-auth-url "+auth_url+" \
    --openstack-insecure \
    --openstack-flavor-name "+flavor+" --openstack-image-name "+image+" \
    --openstack-tenant-name "+tenant+" --openstack-region "+region+" \
    --openstack-net-name "+network_name+" \
    --openstack-sec-groups savi-iot --openstack-ssh-user ubuntu \
    --openstack-username "+username+" --openstack-password "+password+" "+vm_name

def get_latest_vm(vm_name):
    """ Function to get the latest added vm, given the base name.
        As more macroservices are created (to manage workload), the added vms' names contain a prefix and suffix separated by '.'
        For example, if more macroservices are needed for iot-edge, then the names would be iot-edge.xx
        So, given the base_name: iot-edge, we find the last added vm (based on their created timestamps)

        Input: base vm name of the macroservice (Eg. 'iot-xxxx' of 'iot-xxxx.xx' )
        Returns: vm name that was last added
    """
    curr_vms = util.run_command('sudo docker node ls -f "name='+vm_name+'" --format "{{.Hostname}}"')
    curr_vms = curr_vms.split('\n')

    # Run this loop iteratively, so that you can store the first vm's created timestamp as latest_time.
    # You need this to compare with other vm's timestamps and find the latest vm created
    for i in range(len(curr_vms)):
        # Remove +0000 UTC bs from the string to properly match with string format
        created_at = util.run_command("sudo docker node inspect -f '{{ .CreatedAt }}' "+curr_vms[i])[:-13]
        created_datetime = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S.%f')

        if i == 0:
            latest_time = created_datetime
            latest_vm = curr_vms[i]
        else:
            # If created time of this VM is later than latest_time, then this is the last vm added.
            if created_datetime > latest_time:
                latest_time = created_datetime
                latest_vm = curr_vms[i]

    return latest_vm

#vm_name="iot-edge.20180414131550"
#util.run_command("sudo docker-machine ssh "+vm_name+" mkdir ~/certs")
new_vm_name = util.add_vm(vm_name)  # add
#print(new_vm_name)

#util.remove_vm(vm_name)  # remove
