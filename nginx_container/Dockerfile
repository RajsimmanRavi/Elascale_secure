FROM perplexedgamer/savi-nginx:v2 

WORKDIR /home

ADD . /home

RUN pip install docker

ENTRYPOINT ["bash", "change_nginx_conf.sh"]

#CMD ["nginx", "-g", "daemon off;"]
