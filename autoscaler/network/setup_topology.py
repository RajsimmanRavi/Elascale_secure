import sys
import requests
import pprint
import networkx as nx
import autoscaler.conf.engine_config as eng
import autoscaler.network.network_util as net_util

# This is just an example topology for getting the switches in-between 2 hosts
def setup_graph():
    G = nx.Graph()

    G.add_node("h1")
    G.add_node("h2")
    G.add_node("h3")
    G.add_node("h4")
    G.add_node("sw_1")
    G.add_node("sw_2")
    G.add_node("sw_3")

    G.node["h1"]["ip"] = eng.H1_IP

    G.node["h4"]["ip"] = eng.H4_IP

    G.node["h2"]["ip"] = eng.H2_IP

    G.node["h3"]["ip"] = eng.H3_IP

    G.node["sw_1"]["ip"] = eng.SW1_IP

    G.node["sw_2"]["ip"] = eng.SW2_IP

    G.node["sw_3"]["ip"] = eng.SW3_IP

    G.add_edge("h1", "sw_1")
    G["h1"]["sw_1"]["port"] = "pair_h1_1"
    G.add_edge("h4", "sw_1")
    G["h4"]["sw_1"]["port"] = "pair_h2_1"
    G.add_edge("h2", "sw_2")
    G["h2"]["sw_2"]["port"] = "pair_h2_1"
    G.add_edge("h3", "sw_3")
    G["h3"]["sw_3"]["port"] = "pair_h2_1"
    G.add_edge("sw_1", "sw_2")
    G["sw_1"]["sw_2"]["port"] = "pair_h3_1"
    G.add_edge("sw_2", "sw_3")
    G["sw_2"]["sw_3"]["port"] = "pair_h3_1"

    return G

def get_port(G,src,dest):

    if G[src][dest]["port"]:
        return G[src][dest]["port"]
    else:
        return None

def find_inbetween_switches(G, src_ip, dest_ip):

    for n,d in G.nodes(data=True):

        if "ip" in d:
            if src_ip in d["ip"]:
                src_host = n

            if dest_ip in d["ip"]:
                dest_host = n

    #sw_list = nx.shortest_path(G,source=src_host,target=dest_host)[1:-1]
    path_nodes = nx.shortest_path(G,source=src_host,target=dest_host)

    return path_nodes

def setup_topology():
    G = setup_graph()

    return G

def find_path(G,src_ip, dest_ip):
    path_list = find_inbetween_switches(G,src_ip, dest_ip)

    """
    for i in range(len(path_list)):
        if i != len(path_list)-1:
            print(get_port(G, path_list[i], path_list[i+1]))
    """

    return path_list
"""
if __name__=="__main__":
    setup_and_find("192.168.200.12","192.168.200.13")
"""
