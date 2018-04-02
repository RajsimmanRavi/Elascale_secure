# This contains all config type variables so that functions use this (instead of environment variables)
PKEY_PASSWORD = "/home/ubuntu/Elascale_secure/pass_key/pass_key_passphrase.txt"
PKEY_FILE = "/home/ubuntu/Elascale_secure/pass_key/pass_key"
CONFIG_PATH = "/home/ubuntu/Elascale_secure/config"
CONFIG_NAME = CONFIG_PATH + "/config.ini"
MICRO_CONFIG = CONFIG_PATH + "/microservices.ini"
MACRO_CONFIG = CONFIG_PATH + "/macroservices.ini"
# Frequency of monitoring in seconds;
MONITORING_INTERVAL = 60
# List of microservices you want to ignore (in this case, the monitoring components)
IGNORE_MICRO = "EK_monitor,beats,elascale_ui"
# Ignore monitor VM
IGNORE_MACRO = "iot-monitor"
# For monitoring dockbeat and metricbeat stats. We look into last 30 seconds of metric data; the value is an average during 30 seconds
START_TIME = "now-30s"
