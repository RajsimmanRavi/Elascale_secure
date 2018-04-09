# ELASCALE PLATFORM DEPENDENT CONSTANT VARIABLES
PLATFORM_CONFIG_DIR = "/home/ubuntu/Elascale_secure/config"
PLATFORM_CERTS_DIR = "/home/ubuntu/Elascale_secure/certs"

# AUTOSCALER DEPENDENT CONSTANT VARIABLES
CONFIG_PATH = "/home/ubuntu/Elascale_secure/autoscaler/conf"
MICRO_CONFIG = CONFIG_PATH + "/microservices.ini"
MACRO_CONFIG = CONFIG_PATH + "/macroservices.ini"
# Frequency of monitoring in seconds;
MONITORING_INTERVAL = 10
# List of microservices you want to ignore (eg. monitoring components)
IGNORE_MICRO = "EK_monitor,beats,elascale_ui"
# List of macroservices you want to ignore (eg. monitor VM)
IGNORE_MACRO = "iot-monitor"
# For monitoring dockbeat and metricbeat stats. We look into last 30 seconds of metric data; the value is an average during 30 seconds
START_TIME = "now-30s"

## UI DEPENDENT CONSTANT VARIABLES
ELASTIC_IP = "10.6.1.3"
UI_IP = "10.2.1.12"
UI_PORT = "8888"
UI_USERNAME = "savi"
UI_PASSWORD = "savi_elascale"
NGINX_CERT = "/home/ubuntu/Elascale_secure/certs/elasticsearch_certificate.pem"
UI_SELF_CERT = "/home/ubuntu/Elascale_secure/certs/elascale_ui_certificate.pem"
UI_SELF_KEY = "/home/ubuntu/Elascale_secure/certs/elascale_ui_private_key.pem"
