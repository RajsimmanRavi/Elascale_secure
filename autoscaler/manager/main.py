from autoscaler.manager.elascale import Elascale
from autoscaler import util
import autoscaler.conf.engine_config as eng

def main():

    #gevent.signal(signal.SIGQUIT, gevent.kill)

    elascale = Elascale()
    elascale.set_elastic_client()

    while True:
        elascale.set_config()
        elascale.set_stats()

        #start_time = time.time()
        elascale.compare_util()
        #elapsed_time = time.time() - start_time
        #print("Time took to complete comparison: %s" % elapsed_time)

        util.progress_bar(eng.MONITORING_INTERVAL)

if __name__=="__main__":
    main()
