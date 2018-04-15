import time
import autoscaler.enforcer.execute as execute
import autoscaler.conf.engine_config as eng
from autoscaler import util

def up_scale(service, es, service_type):
    alpha = float(eng.ALPHA)
    beta = eng.BETA

    curr_info = get_cpu_util(service,es, service_type, "high")
    curr = curr_info["util"]
    if curr < (1-alpha):
        # wait for beta seconds and get utilization again
        util.progress_bar(beta)

        curr_info = get_cpu_util(service,es,service_type, "high")
        curr,thres = curr_info["util"], curr_info["thres"]
        if curr > thres:
            thres = thres * (1+alpha)
            # change threshold of cpu_up_lim of that microservice
            if service_type == "Micro":
                modify.update_config_attribute(eng.MICRO_CONFIG, service, "cpu_up_lim", thres)
            else:
                modify.update_config_attribute(eng.MACRO_CONFIG, service, "cpu_up_lim", thres)

    else:
        return True

    return False


def down_scale(service, es, service_type):
    alpha = float(eng.ALPHA)
    beta = eng.BETA
    min_T = float(eng.MIN_THRES)

    curr_info = get_cpu_util(service,es, service_type, "low")
    curr, thres = curr_info["util"], curr_info["thres"]
    if curr >= min_T:
        util.progress_bar(beta)

        curr_info = get_cpu_util(service,es, service_type, "low")
        curr, thres = curr_info["util"], curr_info["thres"]
        if curr < thres:
            util.progress_bar(beta)

            thres = thres * (1-alpha)
            # change threshold of cpu_up_lim of that microservice
            if service_type == "Micro":
                modify.update_config_attribute(eng.MICRO_CONFIG, service, "cpu_down_lim", thres)
            else:
                modify.update_config_attribute(eng.MACRO_CONFIG, service, "cpu_down_lim", thres)
    else:
        return True


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





