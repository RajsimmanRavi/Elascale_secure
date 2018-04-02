import sys
import paramiko
import time
from tqdm import tqdm
import configparser
import engine_config

# Read config file
def read_config_file(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

# Progress bar for our Time interval waiting to show how much time to wait
def progress_bar(time_interval):
    for i in tqdm(range(time_interval)):
        time.sleep(1)

"""
Connect to the IoT controller to setup the cluster.
Arguments:
    IP: IP address of the swarm-master/IoT controller
    user_name: ssh username
    passphrase: the passphrase to unlock the private key
    pkey: the private key itself

This will return a paramiko client connection to the swarm master
Note: This machine (that we are connecting to...) should have Docker, Docker-Machine and Swarm installed
"""

# This function basically gets a ssh connection to the swarm master
# It gets the required information from the config file
def get_client(config_file, pkey_password_file, pkey_file):

    config = read_config_file(config_file)
    f = open(pkey_password_file, 'r')
    pkey_password = f.read().replace('\n', '')

    host = config.get('swarm', 'master_ip')
    user_name = config.get('swarm', 'user_name')

    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        client.connect(host, username=user_name, password=pkey_password, key_filename=pkey_file)
    except paramiko.SSHException as e:
        print(str(e))

    return client

# This function basically executes the command on the ssh connection
def run_command(command):

    config_file = engine_config.CONFIG_NAME
    pkey_password_file = engine_config.PKEY_PASSWORD
    pkey_file = engine_config.PKEY_FILE

    client = get_client(config_file, pkey_password_file, pkey_file)
    stdin, stdout, stderr = client.exec_command(command, timeout=120)
    exit_status = stdout.channel.recv_exit_status()

    if exit_status == 0:
        result = ""
        # If you are provisioning VM, you want to see the output of command
        if "provision_vm" in command:
            for line in stdout:
                print('... ' + line.strip('\n'))
                result = result + line
        else:
            result = stdout.read()

    client.close()
    return result
