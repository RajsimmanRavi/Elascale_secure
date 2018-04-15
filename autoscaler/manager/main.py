from autoscaler.manager.elascale import Elascale
from autoscaler import util
import autoscaler.conf.engine_config as eng
from autoscaler.policy.discrete import algorithm as discrete_alg
from autoscaler.policy.adaptive import algorithm as adaptive_alg

def main():

    #gevent.signal(signal.SIGQUIT, gevent.kill)

    elascale = Elascale()
    elascale.set_elastic_client()

    while True:
        elascale.set_config()
        elascale.set_stats()

        #threads = []
        for micro in elascale.micro_config.sections():
            micro_status = util.check_status("Micro", micro, elascale.es)

            if micro_status["status"] == "Normal":
                print("Within CPU limit. Nothing to do for service: "+micro+"!\n")
            else:
                macro_status = util.check_status("Macro", micro, elascale.es)
                #discrete_alg(micro_status["status"], macro_status["status"], micro, macro_status["service"])
                adaptive_alg(micro, macro_status["service"], elascale.es)

                # You can use gevent threads too, but found to make negligant impact
                # Make sure you run gevent.sleep(0) on execute() function when calling util_run_command('scale up/down')
                #threads.append(gevent.spawn(alg, micro_status["status"], macro_status["status"], micro, macro_status["service"]))

        #gevent.joinall(threads)

        util.progress_bar(eng.MONITORING_INTERVAL)

if __name__=="__main__":
    main()
