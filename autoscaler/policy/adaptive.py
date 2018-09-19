import time
import autoscaler.enforcer.execute as execute
import autoscaler.conf.engine_config as eng
import autoscaler.conf.config_modifier as modify
from autoscaler import util

def up_scale(service, es, service_type):
    alpha = float(eng.ALPHA)
    beta = eng.BETA

    curr_info = util.get_cpu_util(service,es, service_type, "high")
    curr,thres = curr_info["util"], curr_info["thres"]

    print("In UP_SCALE for service: %s" % service)
    print("First CURR: %s" % str(curr))
    print("First THRESHOLD: %s" % str(curr_info["thres"]))

    if curr >= thres:
        if curr < (1-alpha):
            # wait for beta seconds and get utilization again
            util.progress_bar(beta)

            curr_info = util.get_cpu_util(service,es,service_type, "high")
            curr,thres = curr_info["util"], curr_info["thres"]

            print("Second CURR: %s" % str(curr))
            print("Second THRESHOLD: %s" % str(thres))

            if curr > thres:

                print("Threshold is about to change...")
                thres = thres * (1+alpha)
                thres = "%.2f " % thres  # Round it off 2 decimal places and make it into string
                print("NEW Threshold: %s" % thres)
                # change threshold of cpu_up_lim of that microservice
                modify.update_config_attribute(service_type, service, "cpu_up_lim", thres)
        else:
            return True

    print("returning False...")
    return False


def down_scale(service, es, service_type):
    alpha = float(eng.ALPHA)
    beta = eng.BETA
    min_T = float(eng.MIN_THRES)

    curr_info = util.get_cpu_util(service,es, service_type, "low")
    curr, thres = curr_info["util"], curr_info["thres"]

    print("In Down_SCALE for service: %s" % service)
    print("First CURR: %s" % str(curr))
    print("First THRESHOLD: %s" % str(thres))

    if curr >= min_T:
        util.progress_bar(beta)

        curr_info = util.get_cpu_util(service,es, service_type, "low")
        curr, thres = curr_info["util"], curr_info["thres"]

        print("Second CURR: %s" % str(curr))
        print("Second THRESHOLD: %s" % str(thres))

        if curr < thres:

            print("Threshold is about to change...")
            thres = thres * (1-alpha)
            thres = "%.2f " % thres  # Round it off 2 decimal places and make it into string
            print("NEW Threshold: %s" % thres)
            # change threshold of cpu_up_lim of that microservice
            modify.update_config_attribute(service_type, service, "cpu_down_lim", thres)
    else:
        return True

    print("Returing False...")
    return False

def adaptive_micro(micro, es):
    micro_config = util.read_config_file(eng.MICRO_CONFIG)

    if up_scale(micro, es, "Micro"):
        # Finally, scale up the microservice
        execute.scale_microservice(micro, int(micro_config.get(micro, 'up_step')))

    elif down_scale(micro, es, "Micro"):
        execute.scale_microservice(micro, int(micro_config.get(micro, 'down_step')))
    else:
        print("Adaptive Policies rejects scaling decision for microservice: "+micro+". Keep Observing...")

def adaptive_macro(macro, es):
    macro_config = util.read_config_file(eng.MACRO_CONFIG)

    if up_scale(macro, es, "Macro"):
        # Finally, scale up the microservice
        execute.scale_macroservice(macro, int(macro_config.get(macro, 'up_step')))

    elif down_scale(macro, es, "Macro"):
        execute.scale_macroservice(macro, int(macro_config.get(macro, 'down_step')))
    else:
        print("Adaptive Policies rejects scaling decision for macroservice: "+macro+". Keep Observing...")

"""
def algorithm(micro, macro, es):

    micro_config = util.read_config_file(eng.MICRO_CONFIG)
    macro_config = util.read_config_file(eng.MACRO_CONFIG)

    if up_scale(micro, es, "Micro"):
        if up_scale(macro, es, "Macro"):
            execute.scale_macroservice(macro, int(macro_config.get(macro, 'up_step')))

        # Finally, scale up the microservice
        execute.scale_microservice(micro, int(micro_config.get(micro, 'up_step')))

    elif down_scale(micro, es, "Micro"):
        execute.scale_microservice(micro, int(micro_config.get(micro, 'down_step')))
        if down_scale(macro, es, "Macro"):
            execute.scale_macroservice(macro, int(macro_config.get(macro, 'down_step')))
    else:
        print("Adaptive Policies rejects scaling decision. Keep Observing...")
"""
