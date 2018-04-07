import autoscaler.enforcer.execute as execute
import autoscaler.conf.engine_config as eng
from autoscaler import util

def algorithm(micro_status, macro_status, micro, macro):
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
    """

    # Getting the necessary configs defined by files in engine_config.py
    micro_config = util.read_config_file(eng.MICRO_CONFIG)
    macro_config = util.read_config_file(eng.MACRO_CONFIG)

    if micro_status == "High":
        if macro_status == "High":
            execute.scale_macroservice(macro, int(macro_config.get(macro, 'up_step')))

        # Finally, scale up the microservice
        execute.scale_microservice(micro, int(micro_config.get(micro, 'up_step')))
    else:
        # Which means it's low low_cpu
        # Scale down the microservice first, just to be on the safe side
        execute.scale_microservice(micro, int(micro_config.get(micro, 'down_step')))

        # Then check whether the macroservice's cpu_util is too low (so we can remove one)
        if macro_status == "Low":
            execute.scale_macroservice(macro, int(macro_config.get(macro, 'down_step')))
