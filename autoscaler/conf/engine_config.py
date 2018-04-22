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
START_TIME = "now-15s"
#STARTUP_TIME = "now-30s"

## UI DEPENDENT CONSTANT VARIABLES
ELASTIC_IP = "10.6.1.7"
UI_IP = "10.6.1.6"
UI_PORT = "8888"
UI_USERNAME = "elascale"
UI_PASSWORD = "savi_elascale"
NGINX_CERT = PLATFORM_DIR + "/certs/elasticsearch_certificate.pem"
UI_SELF_CERT = PLATFORM_DIR + "/certs/elascale_ui_certificate.pem"
UI_SELF_KEY = PLATFORM_DIR + "/certs/elascale_ui_private_key.pem"

## ADAPTIVE POLICIES CONSTANTS
ALPHA = 0.1
BETA = 15
MIN_THRES = 0.1

## SWITCH TOPOLOGY
RYU_CONTROLLER = "10.2.1.23:8090"
SW1_IP = "10.6.1.8"
SW2_IP = "10.6.1.10"
SW3_IP = "10.6.1.9"
H1_IP = "192.168.200.10"
H2_IP = "192.168.200.11"
H3_IP = "192.168.200.12"
H4_IP = "192.168.200.13"

# Mapping of all p0/p1 interfaces (for vxlans going through ovs switches)
MAC_MAPPER = {
    "c2:08:8b:5d:6f:74": "h1",
    "f6:08:21:b0:83:f3": "h2",
    "7e:2c:36:e8:99:13": "h3",
    "fe:56:a9:ce:96:a5": "h4"
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

PORT_MAPPER = {
    "sw_1" : "pair_h2_1",
    "sw_2" : "pair_h3_1",
    "sw_3" : "pair_h1_1",
}
