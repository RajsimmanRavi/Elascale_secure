import json
import util
import time
import os
import configparser
import plan
import engine_config

def prepare_for_beats(vm_name):

    # Read the current config file
    config = util.read_config_file(engine_config.CONFIG_NAME)

    print('\nDeploying beats on the VM: ' + vm_name)

    # Get where the config files are located. This can be found on config.ini file
    elascale_config_dir = config.get('swarm', 'elascale_config_dir')

    # Get where the Elascale root directory are located. This can be found on config.ini file
    elascale_certs_dir = config.get('swarm', 'elascale_certs_dir')

    # Copy the metricbeat.yml on swarm-master to the new node
    result = util.run_command("sudo docker-machine scp "+elascale_config_dir+"metricbeat.yml "+vm_name+":~")

    # Change the hostname on the new metricbeat.yml
    sed_command = "sed -i \"s/name: \".*\"/name: \""+vm_name+"\"/g\" ~/metricbeat.yml"
    result = util.run_command("sudo docker-machine ssh "+vm_name+" "+sed_command)

    # Copy the dockbeat.yml on swarm-master to the new node
    result = util.run_command("sudo docker-machine scp "+elascale_config_dir+"dockbeat.yml "+vm_name+":~")

    # Copy elasticsearch_certificate.yml to the new machine
    result = util.run_command("sudo docker-machine scp "+elascale_certs_dir+"elasticsearch_certificate.pem "+vm_name+":~/certs")

    # Create /volumes/dockbeat-logs dir on the new node (required for dockbeat to work properly)
    result = util.run_command("sudo docker-machine ssh "+vm_name+" sudo mkdir -p /volumes/dockbeat-logs/")

    print('dockbeat and metricbeat yml files have been copied/configured successfully.')


def docker_machine_scale(vm_name, scale_type):
    if scale_type == 'scale-out':  # i.e., scale out

        # get info of the macroservice
        vm_info = plan.inspect_machine(vm_name)

        vm_json = json.loads(vm_info, encoding='utf8')

        user_name       = vm_json['Driver']['Username']
        password        = vm_json['Driver']['Password']

        new_vm_name = vm_name + "." + time.strftime("%Y%m%d%H%M%S", time.localtime())

        print(new_vm_name + ' VM is being provisioned on the cloud ...')

        # Get the label from the base vm
        label_key = plan.get_labels(vm_name)
        for key in label_key:
            label= key
            value = label_key[key]

        # spur is very fidgety when creating VMs. It also does not have timeout flags
        # Hence, we use paramiko client based function
        # Then, we check for any errors.
        # If in error, we remove that useless vm and re-create vm again.
        # If not, we break out of while loop
        while(1):
            create_vm(new_vm_name, user_name, password, label, value)

            # Now, let's check whether it's working fine
            any_err = plan.check_macroservice_status(new_vm_name)

            if any_err:
                print("Caught error! Deleting VM\n")
                delete_vm(new_vm_name)
            else:
                break

            print("Deleted VM! Waiting for clean-up\n")

            util.progress_bar(10)

            print("Re-creating VM!")

        print("Successfully created and provisioned VM!\n")

        try:
            prepare_for_beats(new_vm_name)
        except Exception as e:
            print("Error while preparing VM for deploying beats")
            print(str(e))
            exit(1)
        else:
            print("Finished provisioning VM\n")


    elif scale_type == 'scale-in':  # i.e., scale in

        candidate_name = plan.find_candidate_instance_to_remove(vm_name)

        if candidate_name.__len__() > 0:
            remove_swarm_node(candidate_name)
            delete_vm(candidate_name)
        else:
            print("\nThere is no such a VM name.\n")


def remove_swarm_node(node_name):

    print("\nRemoving the swarm node: " + node_name+"\n")
    result = util.run_command("sudo docker-machine ssh "+node_name+ "sudo docker swarm leave")
    print(node_name + " " + result)
    result = util.run_command("sudo docker node rm --force "+node_name)

    return


#delete a VM using: docker-machine rm -f VM-name
def delete_vm(vm_name):

    print('\nDeprovisioning the instance: ' + vm_name+"\n")
    result = util.run_command("sudo docker-machine rm --force "+vm_name)

    return


def create_vm(new_vm_name, user_name, password, label, value):

    # Read the config file and get the Elascale directory
    config = util.read_config_file(engine_config.CONFIG_NAME)

    elascale_dir = config.get('swarm', 'elascale_root_dir')

    #provision_vm bash script
    prov_vm_file = elascale_dir+"./provision_vm.sh"

    command = "sudo "+prov_vm_file+" "+new_vm_name+" "+user_name+" "+password+" "+label+" "+value
    result = util.run_command(command)


def scale_microservice(service_name, value):

    # Read the current config file
    micro_config = util.read_config_file(engine_config.MICRO_CONFIG)

    print("### Scaling micro_service: "+service_name+" of value: "+str(value))

    current_replica = plan.get_micro_replicas(service_name)
    max_replica = int(micro_config.get(service_name, 'max_replica'))
    min_replica = int(micro_config.get(service_name, 'min_replica'))

    # This represents the total number of services 'after' it has been scaled
    total_replica = current_replica+value

    if total_replica > max_replica:
        print('### Abort micro scaling for microservice: '+service_name+' due to max replica limit: '+str(max_replica)+'.\n')
        return

    elif total_replica < min_replica:
        print('### Abort micro scaling for microservice: '+service_name+' due to min replica limit: '+str(min_replica)+'.\n')
        return

    else:
        print("====> Scaling microservice: " + service_name + " to: " + str(total_replica) +"\n")
        result = util.run_command("sudo docker service scale "+service_name+"="+str(total_replica))
        return


def scale_macroservice(host_name, value):

    # Read the current config file
    macro_config = util.read_config_file(engine_config.MACRO_CONFIG)

    print("### Scaling macro_service: "+host_name+" of value: "+str(value))

    base_name = plan.get_macro_base_name(host_name)

    current_replica = plan.get_macro_replicas(base_name)

    max_replica = int(macro_config.get(base_name, 'max_replica'))
    min_replica = int(macro_config.get(base_name, 'min_replica'))

    # This represents the total number of services 'after' it has been scaled
    # 'value' variable tells whether to scale down ( - value) or scale up ( + value)
    total_replica = current_replica+value

    if total_replica > max_replica:
        print('### Abort macro scaling for '+host_name+' due to max replica limit: '+str(max_replica)+'.\n')
        return

    if total_replica < min_replica:
        print('### Abort macro scaling for '+host_name+' due to min replica limit: '+str(min_replica)+'.\n')
        return

    else:
        if value > 0:
            print("====> Scaling out the macroservice: "+host_name+" by "+str(value)+"\n")
            docker_machine_scale(host_name, 'scale-out')  # scale-out
        else:
            #value < 0
            print("====> Scaling in the macroservice: "+host_name+" by -"+str(value)+"\n")
            docker_machine_scale(host_name, 'scale-in')  # scale-in
