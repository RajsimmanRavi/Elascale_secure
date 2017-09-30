#!/bin/bash

# This script creates X509 certificates for Elasticsearch (called nginx because of reverse proxy), Kibana (for UI HTTPS), and UI (for HTTPS)
# It requires 2 arguments: IP address of the node that contains Elasticsearch and the IP address of the node that contains UI

# Check if arguments given
if [[ $# -ne 2 ]] ; then
    echo "Error: you need to provide the IP address of the node running Elasticsearch and UI"
    exit 1
fi

SCRIPTS_DIR="/home/ubuntu/Elascale_secure"
CERTS_DIR="$SCRIPTS_DIR/certs"
ELASTIC_IP="$1"
UI_IP="$2"

# remove all contents inside folder
sudo rm -f $CERTS_DIR/*

## declare an array variable
declare -a array=("elasticsearch" "kibana" "elascale_ui")

# get length of an array
arraylength=${#array[@]}

# use for loop to read all values and indexes
for (( i=1; i<${arraylength}+1; i++ ));
do
  
  sudo openssl genrsa -out $CERTS_DIR/${array[$i-1]}_private_key.pem 2048
  
  if [ "${array[$i-1]}" != "elascale_ui" ]
  then 
    sudo openssl req -nodes -new -sha256 -key $CERTS_DIR/${array[$i-1]}_private_key.pem -out $CERTS_DIR/${array[$i-1]}.csr -subj "/C=CA/ST=Ontario/L=Toronto/O=SAVI Testbed/CN=${array[$i-1]}/subjectAltName=$ELASTIC_IP"
  else
    sudo openssl req -nodes -new -sha256 -key $CERTS_DIR/${array[$i-1]}_private_key.pem -out $CERTS_DIR/${array[$i-1]}.csr -subj "/C=CA/ST=Ontario/L=Toronto/O=SAVI Testbed/CN=${array[$i-1]}/subjectAltName=$UI_IP"
  fi
  sudo openssl req -x509 -sha256 -days 365 -key $CERTS_DIR/${array[$i-1]}_private_key.pem -in $CERTS_DIR/${array[$i-1]}.csr -out $CERTS_DIR/${array[$i-1]}_certificate.pem
  
done
