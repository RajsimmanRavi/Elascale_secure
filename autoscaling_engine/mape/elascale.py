from elasticsearch import Elasticsearch
import monitor
import execute
import util
import engine_config as eng

class Elascale:

    config = util.read_config_file(eng.CONFIG_NAME)

    def __init__(self):
        self.ignore_micro = None
        self.ignore_macro = None
        self.micro_config = None
        self.macro_config = None
        self.micro_util = None
        self.macro_util = None
        self.es = None

    def get_elastic_client(self):
        port = int(self.config.get('elasticsearch', 'port'))
        ca_cert = str(self.config.get('elasticsearch', 'ca_cert'))
        self.es = Elasticsearch([{'host': 'elasticsearch', 'port': port}], use_ssl=True, ca_certs=ca_cert)

    def read_config(self):
        self.ignore_micro = eng.IGNORE_MICRO
        self.ignore_macro = eng.IGNORE_MACRO
        self.micro_config = util.read_config_file(eng.MICRO_CONFIG)
        self.macro_config = util.read_config_file(eng.MACRO_CONFIG)

    def get_stats(self):
        self.micro_util = monitor.get_microservices_utilization(self.es)
        self.macro_util = monitor.get_macroservices_utilization(self.es)

    def get_util_info(self, service, curr_util, config):
        """ Fetches the current utilization  along with high and low thresholds defined in config file.

        Args:
            service: name of the service
            curr_util: the current utilization data of all services
            config: config file

        Returns:
            Dictionary of data:
                result = {
                    "service" : xx,
                    "curr_cpu_util" : xx,
                    "curr_mem_util" : xx,
                    "high_cpu_threshold" : xx,
                    "low_cpu_threshold" : xx,
                    "high_mem_threshold" : xx,
                    "low_mem_threshold" : xx
                }
        """
        result = {}

        result["service"] = service
        result["curr_cpu_util"] = "%.3f " % curr_util[service]['cpu'] # Round it to 3 decimal digits
        result["curr_mem_util"] = "%.3f " % curr_util[service]['memory'] # Round it to 3 decimal digits
        result["high_cpu_threshold"] = config.get(service, 'cpu_up_lim') # Ex second argument should be: cpu_up_lim
        result["low_cpu_threshold"] = config.get(service, 'cpu_down_lim') # Ex second argument should be: cpu_low_lim
        result["high_mem_threshold"] = config.get(service, 'memory_up_lim') # Ex second argument should be: cpu_up_lim
        result["low_mem_threshold"] = config.get(service, 'memory_down_lim') # Ex second argument should be: cpu_low_lim

        return result

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

        data = self.get_util_info(service, curr_util, curr_config)
        util.pretty_print(service_type, data)

        # Then check whether the macroservice can handle the load to spin another microservice
        status = util.check_threshold(service, data["high_cpu_threshold"], data["low_cpu_threshold"], data["curr_cpu_util"])

        result = {}
        result["service"] = service
        result["status"] = status

        return result

    def discrete_policy(self, micro_status, macro_status, micro, macro):
        """ Performs discrete policy for autoscaling engine.

        Algorithm:
            if microservice crosses high threshold:
                if macroservice crosses high threshold:
                   scale-up macroservice
                scale-up microservice
            else:
                scale-down microservice

                if macroservice crosses low threshold:
                    scale-down macroservice

         Args:
             micro_status: Keyword 'High', 'Normal', or 'Low' mentioning the status of microservice
             macro_status: Keyword 'High', 'Normal', or 'Low' mentioning the status of macroservice
             micro: name of the microservice
             macro: name of the macroservice
        """
        if micro_status == "High":
            if macro_status == "High":
                execute.scale_macroservice(macro, int(self.macro_config.get(macro, 'up_step')))

            # Finally, scale up the microservice
            execute.scale_microservice(micro, int(self.micro_config.get(micro, 'up_step')))
        else:
            # Which means it's low low_cpu
            # Scale down the microservice first, just to be on the safe side
            execute.scale_microservice(micro, int(self.micro_config.get(micro, 'down_step')))

            # Then check whether the macroservice's cpu_util is too low (so we can remove one)
            if macro_status == "Low":
                execute.scale_macroservice(macro, int(self.macro_config.get(macro, 'down_step')))

    def compare_util(self):
        """ Compares utilization of micro/macroservices and calls discrete autoscaling policy.
            TODO: Currently uses only CPU, need to do for Memory and Network.
            TODO: Use Adaptive policies.
        """
        for micro in self.micro_config.sections():
            micro_status = self.check_status("Micro", micro)

            if micro_status["status"] == "Normal":
                print("Within CPU limit. Nothing to do for service: "+micro+"!\n")
            else:
                macro_status = self.check_status("Macro", micro)
                self.discrete_policy(micro_status["status"], macro_status["status"], micro, macro_status["service"])

def main():

    elascale = Elascale()
    elascale.get_elastic_client()

    while True:
        elascale.read_config()
        elascale.get_stats()
        elascale.compare_util()
        util.progress_bar(eng.MONITORING_INTERVAL)

if __name__=="__main__":
    main()
