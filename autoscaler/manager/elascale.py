import time
from elasticsearch import Elasticsearch
import signal
#import gevent # If you want to use green threads
import autoscaler.conf.engine_config as eng
import autoscaler.conf.config_modifier as modify
import autoscaler.monitor.beats_stats as stats
from autoscaler.policy.discrete import algorithm as alg
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

    def set_stats(self):
        self.micro_util = stats.get_microservices_utilization(self.es)
        self.macro_util = stats.get_macroservices_utilization(self.es)

    def check_status(self, service_type, micro):
        """ Fetches status for a specific macroservice

        Args:
            service_type: Keyword 'Micro' or 'Macro' to mention micro/macroservice
            micro: name of microservice

        Returns:
            Dictionary of data:
                result = {
                    "service": name of the macroservice
                    "status": Keyword 'High', 'Normal' or 'Low' mentioning the status
                }
        """
        if service_type == "Macro":
            # get the macroservice runnning the service
            service = util.get_macroservice(micro)
            curr_util = self.macro_util
            curr_config = self.macro_config
        else:
            service = micro
            curr_util = self.micro_util
            curr_config = self.micro_config

        data = util.get_util_info(service, curr_util, curr_config)
        util.pretty_print(service_type, data)

        # Then check whether the macroservice can handle the load to spin another microservice
        cpu_status = util.check_threshold(service, data["high_cpu_threshold"], data["low_cpu_threshold"], data["curr_cpu_util"])

        # RR: Some services utilize cpu more than memory, hence autoscaler ignores if both are computed. So, I'm turning this off for now
        #mem_status = util.check_threshold(service, data["high_mem_threshold"], data["low_mem_threshold"], data["curr_mem_util"])
        #status = util.compute_trajectory(cpu_status, mem_status)

        status = cpu_status
        print(status)
        result = {}
        result["service"] = service
        result["status"] = status

        return result

    def compare_util(self):
        """ Compares utilization of micro/macroservices and calls discrete autoscaling policy.
            TODO: Currently uses only CPU and Memory. Need to do Network.
            TODO: Use Adaptive policies.
        """
        #threads = []

        for micro in self.micro_config.sections():
            micro_status = self.check_status("Micro", micro)

            if micro_status["status"] == "Normal":
                print("Within CPU limit. Nothing to do for service: "+micro+"!\n")
            else:
                macro_status = self.check_status("Macro", micro)
                alg(micro_status["status"], macro_status["status"], micro, macro_status["service"])

                # You can use gevent threads too, but found to make negligant impact
                # Make sure you run gevent.sleep(0) on execute() function when calling util_run_command('scale up/down')
                #threads.append(gevent.spawn(alg, micro_status["status"], macro_status["status"], micro, macro_status["service"]))

        #gevent.joinall(threads)
