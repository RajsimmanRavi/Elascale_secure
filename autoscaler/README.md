# Elascale_v2
Updated version of Elascale auto-scaling engine

## Docker container ##
The container for this engine is: `perplexedgamer/elascale_v2:v2.1`

## Deployment ##
You can either deploy it as a container (docker service) or locally.

### Container ###

You can deploy it as a docker service (or stack) if you use a (similar) docker-compose yaml:

```
version: '3.1'

services:
   v2:
     image: perplexedgamer/elascale_v2:v2.1
     volumes:
       - /home/ubuntu/Elascale/config:/Elascale/conf
     environment:
       PYTHONUNBUFFERED :   "1"
       PKEY_PASSWORD    : /run/secrets/pkey_password
       PKEY_FILE        : /run/secrets/pkey_file
     secrets:
       - pkey_password
       - pkey_file

secrets:
   pkey_password:
     file: /home/ubuntu/Elascale/pass_key/pass_key_passphrase.txt
   pkey_file:
     file: /home/ubuntu/Elascale/pass_key/pass_key
```

#### NOTE: ####
Make sure you have the appropriate pass_key_passphrase.txt (password to private key) and pass_key (private key). 
The engine will use ssh to connect to the swarm-master (information on conf/config.ini file). 
Also, you need to edit conf/config.ini file to modify the IP addresses of swarm-master and elasticsearch host. 

### Local host ###

You can simply fetch the source code from the repository and modify the conf/config.ini file to modify the IP addresses of swarm-master and elasticsearch host.
You should also uncomment the following code on mape/analyze.py (in the bottom) to initialize the OS ENV variables:

```
os.environ["PYTHONUFFERED"] = "0"
os.environ["PKEY_PASSWORD"] = "/home/ubuntu/Elascale/pass_key/pass_key_passphrase.txt"
os.environ["PKEY_FILE"] = "/home/ubuntu/Elascale/pass_key/pass_key"
```

#### NOTE ####

Make sure the pass_key_passphrase.txt (password to the private key) and pass_key (private key) are correct for Elascale engine to log into the localhost as ssh user (ubuntu).
