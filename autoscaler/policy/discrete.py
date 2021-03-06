import autoscaler.enforcer.execute as execute
import autoscaler.conf.engine_config as eng
from autoscaler import util

def up_scale(service, es, service_type):
    curr_info = util.get_cpu_util(service,es, service_type, "high")
    curr,thres = curr_info["util"], curr_info["thres"]

    print("In UP_SCALE for service: %s" % service)
    print("CURR: %s" % str(curr))
    print("THRESHOLD: %s" % str(curr_info["thres"]))

    if curr >= thres:
        return True
    else:
        return False

def down_scale(service, es, service_type):

    curr_info = util.get_cpu_util(service,es, service_type, "low")
    curr, thres = curr_info["util"], curr_info["thres"]

    print("In Down_SCALE for service: %s" % service)
    print("CURR: %s" % str(curr))
    print("THRESHOLD: %s" % str(thres))

    if curr < thres:
        return True
    else:
        return False


def discrete_micro(micro, es):
    """ Performs discrete policy for autoscaling engine.

    Algorithm:
        if microservice crosses high threshold:
            scale-up microservice
        else:
            scale-down microservice
    """
    micro_config = util.read_config_file(eng.MICRO_CONFIG)

    if up_scale(micro, es, "Micro"):
        # Finally, scale up the microservice
        execute.scale_microservice(micro, int(micro_config.get(micro, 'up_step')))

    elif down_scale(micro, es, "Micro"):
        execute.scale_microservice(micro, int(micro_config.get(micro, 'down_step')))
    else:
        print("Discrete Policies rejects scaling decision for microservice: "+micro+". Keep Observing...")


def discrete_macro(macro, es):
    """ Performs discrete policy for autoscaling engine.

    Algorithm:
        if macroservice crosses high threshold:
            scale-up macroservice
        else:
            scale-down macroservice
    """
    macro_config = util.read_config_file(eng.MACRO_CONFIG)

    if up_scale(macro, es, "Macro"):
        # Finally, scale up the macroservice
        execute.scale_macroservice(macro, int(macro_config.get(macro, 'up_step')))

    elif down_scale(macro, es, "Macro"):
        execute.scale_macroservice(macro, int(macro_config.get(macro, 'down_step')))
    else:
        print("Discrete Policies rejects scaling decision for macroservice: "+macro+" . Keep Observing...")
