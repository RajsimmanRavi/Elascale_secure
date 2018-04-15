# ELASCALE PLATFORM DEPENDENT CONSTANT VARIABLE S
PLATFORM_DIR = "/home/ubuntu/Elascale_secure"
PLATFORM_CONFIG_DIR = PLATFORM_DIR + "/config"
PLATFORM_CERTS_DIR = PLATFORM_DIR + "/certs"

# AUTOSCALER DEPENDENT CONSTANT VARIABLES
CONFIG_PATH = PLATFORM_DIR + "/autoscaler/conf"
MICRO_CONFIG = CONFIG_PATH + "/microservices.ini"
MACRO_CONFIG = CONFIG_PATH + "/macroservices.ini"
# Frequency of monitoring in seconds;
MONITORING_INTERVAL = 10
# List of microservices you want to ignore (eg. monitoring components)
IGNORE_MICRO = "EK_monitor,beats,cass,sensor"
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
NGINX_CERT = PLATFORM_DIR + "/certs/elasticsearch_certificate.pem"
UI_SELF_CERT = PLATFORM_DIR + "/certs/elascale_ui_certificate.pem"
UI_SELF_KEY = PLATFORM_DIR + "/certs/elascale_ui_private_key.pem"

## ADAPTIVE POLICIES CONSTANTS
ALPHA = 0.1
BETA = 15
MIN_THRES = 0.1
