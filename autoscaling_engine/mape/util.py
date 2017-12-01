import os
import spur
import sys
import paramiko
import time
from tqdm import tqdm
import configparser

# I kinda hate doing this. But, I'll change this later
config_path = os.path.realpath('./../config')
config_name = config_path + "/config.ini"

"""
Connect to the IoT controller to setup the cluster.
Arguments:
    IP: IP address of the swarm-master/IoT controller
    user_name: ssh username
    passphrase: the passphrase to unlock the private key
    pkey: the private key itself

This will return a shell connection to the swarm master

Note: This machine (that we are connecting to...) should have Docker, Docker-Machine and Swarm installed
"""
def ssh_to(ip, user_name, passphrase, pkey):
    try:
        shell = spur.SshShell(
            hostname=ip,
            username=user_name,
            password=passphrase,
            private_key_file=pkey,
            missing_host_key=spur.ssh.MissingHostKey.accept
        )
    except Exception as e:
        print(str(e))
        print("Not connected...")
        return e
    else:
        return shell

# This function basically gets a ssh connection to the swarm master
# It gets the required information from the environment variables and config file
def get_shell():

    config = read_config_file(config_name)

    f = open(os.environ['PKEY_PASSWORD'], 'r')
    pkey_password = f.read().replace('\n', '')
    pkey_file = os.environ['PKEY_FILE']
    shell = ssh_to(config.get('swarm', 'master_ip'), config.get('swarm', 'user_name'), pkey_password, pkey_file)
    return shell

# This function basically executes the command on the ssh connection
# Using 'with' allows us to execute the command and close the connection

def run_command(command):

    try:
        # First get the shell from the environment variables and private key files
        shell = get_shell()
        cmd_list = command.split(" ")
        with shell:
            result = shell.run(cmd_list, store_pid="True", allow_error=True, encoding="utf8")

    except Exception as e:
        print(str(e))
        exit(1)

    else:
        return result


# This function is used to provison a vm.
# It uses Paramiko client because spur is very fidgety when deploying a VM.
# This client is more appropriate for this operation
def provision_vm(command):

    config = read_config_file(config_name)

    pkey_file = os.environ['PKEY_FILE']
    f = open(os.environ['PKEY_PASSWORD'], 'r')
    pkey_password = f.read().replace('\n', '')

    host = config.get('swarm', 'master_ip')
    user_name = config.get('swarm', 'user_name')
    try:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        client.connect(host, username=user_name, password=pkey_password, key_filename=pkey_file)

        # Very important is this timeout functionality. There isn't one for spur function :(
        stdin, stdout, stderr = client.exec_command(command, timeout=120)
        for line in stdout:
            print('... ' + line.strip('\n'))
        client.close()
    except paramiko.SSHException as e:
        print(str(e))
        pass

# Read config file
def read_config_file(config_name):
    config = configparser.ConfigParser()
    config.read(config_name)

    return config

# Progress bar for our Time interval waiting
def progress_bar(time_interval):
    for i in tqdm(range(time_interval)):
        time.sleep(1)

def str_to_bool(s):
    if s == 'True':
        return True
    elif s == 'False':
        return False
    else:
        return False
