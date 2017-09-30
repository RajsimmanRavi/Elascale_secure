#!/bin/bash

IP_ADDRS=($(python get_ip_addrs.py))

for i in "${IP_ADDRS[@]}"
do
    if [[ "$i" =~ .*ELASTICSEARCH.* ]];then
        ELASTIC_IP=`echo $i | cut -d ":" -f 2`
        sed -i "s/http:\/\/.*:9200/http:\/\/$ELASTIC_IP:9200/g" /home/nginx.conf
    elif [[ "$i" =~ .*KIBANA.* ]];then
        KIBANA_IP=`echo $i | cut -d ":" -f 2`
        sed -i "s/http:\/\/.*:5601/http:\/\/$KIBANA_IP:5601/g" /home/nginx.conf
    fi
done

echo "Changed shit to nginx.conf" >> /tmp/log.txt

cp /home/nginx.conf /etc/nginx/

nginx -g "daemon off;"
