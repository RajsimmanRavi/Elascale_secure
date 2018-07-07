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
#IGNORE_MICRO = "EK_monitor,beats,cass,sensor,kafka,zookeeper"
IGNORE_MICRO = "EK_monitor,beats"
# List of macroservices you want to ignore (eg. monitor VM)
IGNORE_MACRO = "iot-monitor"
# For monitoring dockbeat and metricbeat stats. We look into last 30 seconds of metric data; the value is an average during 30 seconds
START_TIME = "now-15s"
#STARTUP_TIME = "now-30s"

## UI DEPENDENT CONSTANT VARIABLES
ELASTIC_IP = "10.2.1.16"
UI_IP = "10.2.1.11"
UI_PORT = "8888"
UI_USERNAME = "elascale"
UI_PASSWORD = "savi_elascale"
NGINX_CERT = PLATFORM_DIR + "/certs/elasticsearch_certificate.pem"
UI_SELF_CERT = PLATFORM_DIR + "/certs/elascale_ui_certificate.pem"
UI_SELF_KEY = PLATFORM_DIR + "/certs/elascale_ui_private_key.pem"

## ADAPTIVE POLICIES CONSTANTS
#ALPHA = 0.1
ALPHA = 0.5
BETA = 5
MIN_THRES = 0.2

## SWITCH TOPOLOGY
RYU_CONTROLLER = "10.2.1.23:8090"
SW1_IP = "10.2.0.36"
SW2_IP = "10.2.0.41"
SW3_IP = "10.2.0.39"
H1_IP = "192.168.200.10"
H2_IP = "192.168.200.11"
H3_IP = "192.168.200.12"
H4_IP = "192.168.200.13"

# Mapping of all p0/p1 interfaces (for vxlans going through ovs switches)
MAC_MAPPER = {
    "06:81:62:7a:57:a0": "h1",
    "a6:d9:2d:6d:df:09": "h2",
    "de:2a:c4:4c:a4:16": "h3",
    "e2:3a:b0:74:35:ba": "h4"
}

IP_MAPPER = {
    H1_IP: "h1",
    H2_IP: "h2",
    H3_IP: "h3",
    H4_IP: "h4",
    SW1_IP: "sw_1",
    SW2_IP: "sw_2",
    SW3_IP: "sw_3"
}
