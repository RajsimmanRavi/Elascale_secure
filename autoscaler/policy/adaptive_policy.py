from elascale import Elascale

class adapt(Elascale):

    def __init__(self):

        self.alpha = None
        self.beta = None
        self.ini_cpu_th = None
        self.ini_mem_th = None
        self.ini_net_tx_th = None
        self.ini_net_rx_th = None



