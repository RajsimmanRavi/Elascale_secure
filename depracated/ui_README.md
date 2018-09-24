# Elascale_UI
This contains the latest code of the Elascale UI created for the Elascale project 

I created a container for hosting the UI. It's perplexedgamer/ui

In run the webserver (for example testing purposes), use the following command:
```
python ui.py --host_ip="x.x.x.x" \
--elastic_ip="x.x.x.x" \
--micro="/path/to/microservices.ini" \
--macro="/path/to/macroservices.ini \
```
To run this as a docker service, use the followin command:/path/to/macroservices.ini 
```
sudo docker service create -p 8888:8888 \ 
--detach=true --name ui \ 
--constraint node.hostname==$HOSTNAME_OF_WHERE_IT_IS_BEING_DEPLOYED \ 
--mount=type=bind,src=/path/to/conf/files,dst=/path/to/conf/files \ 
--mount=type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock \
perplexedgamer/ui:v2 --host_ip=x.x.x.x --elastic_ip=x.x.x.x \ 
--micro=/path/to/microservices.ini --macro=/path/to/macroservices.ini
```
