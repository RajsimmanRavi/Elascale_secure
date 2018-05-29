import time
from elasticsearch import Elasticsearch
import signal
#import gevent # If you want to use green threads
import autoscaler.conf.engine_config as eng
import autoscaler.conf.config_modifier as modify
import autoscaler.monitor.beats_stats as stats
from autoscaler import util

class Elascale:

    def __init__(self):
        self.ignore_micro = None
        self.ignore_macro = None
        self.micro_config = None
        self.macro_config = None
        self.micro_util = None
        self.macro_util = None
        self.es = None

    def set_elastic_client(self):
        self.es = Elasticsearch([{'host': 'elasticsearch', 'port': 9200}], use_ssl=True, ca_certs=eng.NGINX_CERT)

    def set_config(self):
        self.ignore_micro = eng.IGNORE_MICRO
        self.ignore_macro = eng.IGNORE_MACRO

        # Change micro and macroservices config.
        # This will filter out ignored services and add new services or remove exited services
        modify.update_config()

        self.micro_config = util.read_config_file(eng.MICRO_CONFIG)
        self.macro_config = util.read_config_file(eng.MACRO_CONFIG)
