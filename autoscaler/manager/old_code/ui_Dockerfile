FROM python:2.7-slim

#This is where we edit the ini files. Might as well keep the code here as well
WORKDIR /home/ubuntu/Elascale/ui

ADD . /home/ubuntu/Elascale/ui

RUN pip install -r requirements.txt

ENTRYPOINT [ "python", "./ui.py" ]
