import ConfigParser
import sys

#This file basically updates the IP addresses of the host (where it is deployed) and Elasticsearch in the config.ini file
#Really wish I could have done it in shell script, but can't handle with sed
#It's easier with the ConfigParser library (need to make sure it is installed on the new swarm-master VM)

#This file takes 2 arguments: Host IP and Elasticsearch IP

CONFIG_DIR="/home/ubuntu/Elascale_secure/config"
HOST_IP=sys.argv[1]
ELASTIC_IP=sys.argv[2]

#Open Config file to read
Config = ConfigParser.ConfigParser()
Config.read(CONFIG_DIR+"/config.ini")
cfgfile = open(CONFIG_DIR+"/config.ini", 'w')

#Set the appropriate values on the respective config sections
Config.set('swarm', 'master_ip', HOST_IP)
Config.set('docker-machine', 'ip', HOST_IP)
Config.set('elasticsearch', 'ip', ELASTIC_IP)

#Write and close the file
Config.write(cfgfile)
cfgfile.close()
