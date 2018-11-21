##### ELASCALE PLATFORM DEPENDENT CONSTANT VARIABLES ####
PLATFORM_DIR = "/home/ubuntu/Elascale_secure"
PLATFORM_CONFIG_DIR = PLATFORM_DIR + "/config"
PLATFORM_CERTS_DIR = PLATFORM_DIR + "/certs"
LOGGING_FILE = '/var/log/elascale/elascale.csv'

#### AUTOSCALER DEPENDENT CONSTANT VARIABLES ####
CONFIG_PATH = PLATFORM_DIR + "/autoscaler/conf"
MICRO_CONFIG = CONFIG_PATH + "/microservices.ini"
MACRO_CONFIG = CONFIG_PATH + "/macroservices.ini"
# Frequency of monitoring in seconds;
MONITORING_INTERVAL = 10 # every x seconds
NETWORK_MONITORING_INTERVAL = 10 # every x seconds
# List of apps you want to ignore (eg. monitoring components)
IGNORE_APP = "EK_monitor,beats"
# List of microservices you want to ignore (eg. monitoring components)
IGNORE_MICRO = "sensor,db"
# List of macroservices you want to ignore (eg. monitor VM)
IGNORE_MACRO = "iot-agg-sensor,iot-core,iot-monitor,iot-master"
# For monitoring dockbeat and metricbeat stats. We look into last 30 seconds of metric data; the value is an average during 30 seconds
#START_TIME = "now-15s" # Testing
STARTUP_TIME = "now-30s"

#### UI DEPENDENT CONSTANT VARIABLES ####
ELASTIC_IP = "10.2.1.17"
UI_IP = "10.2.1.12"
UI_PORT = "8888"
UI_USERNAME = "elascale"
UI_PASSWORD = "savi_elascale"
NGINX_CERT = PLATFORM_DIR + "/certs/elasticsearch_certificate.pem"
UI_SELF_CERT = PLATFORM_DIR + "/certs/elascale_ui_certificate.pem"
UI_SELF_KEY = PLATFORM_DIR + "/certs/elascale_ui_private_key.pem"

#### ADAPTIVE POLICIES CONSTANTS ####
#ALPHA = 0.1
#ALPHA = 0.55
ALPHA = 0.25
#ALPHA = 0.68
BETA = 5
MIN_THRES = 0.15

#### ANOMALY DETECTION MODEL PARAMETERS ####
PROB_WINDOW = 108 # What I had for CNSM and worked fine. Sampling frequency: 6 samples/min (beats data every 10 secs) --> 18 minutes
#PROB_WINDOW = 324 # What I had for CNSM and worked fine. Sampling frequency: 6 samples/min (beats data every 10 secs) --> 18 minutes
MIN_CPU_VAL = 0.0 # Minimum cpu_util value
MAX_CPU_VAL = 2e2 # Maximum cpu_util value
MAX_NET_VAL = 1e10 # Maximum Net_util value
INVESTIGATION_PHASE_LENGTH = 6 # i.e. [0-6]. Hence, 6 consecutive samples shud be non-anomalous to exit inv. period
ANOMALY_THRESHOLD =  1 - 10e-5 # Anomaly threshold

#### QoS PARAMETERS FOR AUTONOMIC NETWORK CONTROL ####
MAX_BW = 3e8 #(300 Mb/s) After this, Elascale will throttle the link to MIN_BW
MIN_BW = 3e6 #(4 Mb/s)

#### SWITCH TOPOLOGY #### [------ THESE HAVE TO BE MANUALLY UPDATED -------]
RYU_CONTROLLER = "10.2.1.11:8090"
SW1_IP = "10.2.1.20"
SW2_IP = "10.2.1.22"
SW3_IP = "10.2.1.21"
H1_IP = "192.168.200.10"
H2_IP = "192.168.200.11"
H3_IP = "192.168.200.12"
H4_IP = "192.168.200.13"
H5_IP = "192.168.200.14"
H6_IP = "192.168.200.15"
H7_IP = "192.168.200.16"

# Mapping of all p0/p1 interfaces (for vxlans going through ovs switches)
MAC_MAPPER = {
    "b6:e1:91:73:0e:dc": "h1",
    "5a:97:d5:1a:ad:61": "h2",
    "82:a6:f6:9f:d6:c2": "h3",
    "7a:fc:77:dc:dc:64": "h4",
    "3a:3d:cf:87:cd:49": "h5",
    "7e:f6:b9:09:c3:62": "h6",
    "92:ed:6b:72:e5:b1": "h7",
}

IP_MAPPER = {
    H1_IP: "h1",
    H2_IP: "h2",
    H3_IP: "h3",
    H4_IP: "h4",
    H5_IP: "h5",
    H6_IP: "h6",
    H7_IP: "h7",
    SW1_IP: "sw_1",
    SW2_IP: "sw_2",
    SW3_IP: "sw_3"
}
