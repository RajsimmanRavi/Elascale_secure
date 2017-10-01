# Monitoring component of the MAPE-K loop
import os
import configparser
from elasticsearch import Elasticsearch

config = configparser.ConfigParser()
config_name = os.path.realpath('./../conf') + "/config.ini"
config.read(config_name)

ca_cert = str(config.get('elasticsearch', 'ca_cert'))
print(ca_cert)
es = Elasticsearch([{'host': 'elasticsearch', 'port': int(config.get('elasticsearch', 'port'))}], use_ssl=True, ca_certs=ca_cert)

start_time = "now-30s"  # we look into last 30 seconds of metric data; the value is an average during 30 seconds


def get_microservices_utilization():
    res = es.search(index='dockbeat-*', body={
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "analyze_wildcard": True,
                            "query": "*"
                        }
                    },
                    {
                        "query_string": {
                            "analyze_wildcard": True,
                            "query": "*"
                        }
                    },
                    {
                        "range": {
                            "@timestamp": {
                                "gte": start_time,
                                "lte": "now",
                                "format": "epoch_millis"
                            }
                        }
                    }
                ],
                "must_not": []
            }
        },
        "size": 0,
        "_source": {
            "excludes": []
        },
        "aggs": {
            "2": {
                "terms": {
                    "script": {
                        "inline": "def path = doc['containerName.keyword'].value;\nif (path != null) {\nint lastSlashIndex = path.indexOf('.');\nif (lastSlashIndex > 0) {\nreturn path.substring(0, lastSlashIndex);\n}\n}\nreturn \"\";",
                        "lang": "painless"
                    },
                    "size": 11,
                    "order": {
                        "1": "desc"
                    },
                    "valueType": "string"
                },
                "aggs": {
                    "1": {
                        "avg": {
                            "field": "cpu.totalUsage"
                        }
                    },
                    "3": {
                        "avg": {
                            "field": "memory.usage_p"
                        }
                    },
                    "4": {
                        "avg": {
                            "field": "net.rxBytes_ps"
                        }
                    },
                    "5": {
                        "avg": {
                            "field": "net.txBytes_ps"
                        }
                    },
                    "6": {
                        "avg": {
                            "field": "blkio.total_ps"
                        }
                    }
                }
            }
        }
    })
    utilization = {}
    for service in res['aggregations']['2']['buckets']:
        utilization[service['key']] = {'cpu': service['1']['value'], 'memory': service['3']['value'],
                                       'net_rx': service['4']['value'], 'net_tx': service['5']['value'],
                                       'blockIO': service['6']['value']}
    return utilization


def get_macroservices_utilization():
    res = es.search(index="metricbeat-*", body={
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": "*",
                            "analyze_wildcard": True
                        }
                    },
                    {
                        "query_string": {
                            "analyze_wildcard": True,
                            "query": "*"
                        }
                    },
                    {
                        "range": {
                            "@timestamp": {
                                "gte": start_time,
                                "lte": "now",
                                "format": "epoch_millis"
                            }
                        }
                    }
                ],
                "must_not": []
            }
        },
        "size": 0,
        "_source": {
            "excludes": []
        },
        "aggs": {
            "3": {
                "terms": {
                    "field": "beat.name",
                    "order": {
                        "1": "desc"
                    }
                },
                "aggs": {
                    "1": {
                        "avg": {
                            "field": "system.cpu.idle.pct"
                        }
                    },
                    "2": {
                        "avg": {
                            "field": "system.memory.used.pct"
                        }
                    }
                }
            }
        }
    }
                    )
    utilization = {}
    data = res['aggregations']['3']['buckets']
    hosts_info = get_hosts_info(data)
    base_hosts = get_base_host_names(hosts_info)

    for base_host in base_hosts:
        utilization[base_host] = {'cpu': 0, 'memory': 0, 'host_cnt': 0}
        cnt = 0
        for host in hosts_info:
            if str(host['name']).__contains__(base_host):
                cnt += 1
                utilization[base_host]['cpu'] += host['cpu']
                utilization[base_host]['memory'] += host['memory']

        utilization[base_host]['cpu'] = utilization[base_host]['cpu'] / float(cnt)
        utilization[base_host]['memory'] = utilization[base_host]['memory'] / float(cnt)
        utilization[base_host]['host_cnt'] = cnt

    return utilization


def get_container_utilization():
    res = es.search(index='dockbeat-*', body={
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "analyze_wildcard": True,
                            "query": "*"
                        }
                    },
                    {
                        "query_string": {
                            "query": "*",
                            "analyze_wildcard": True
                        }
                    },
                    {
                        "range": {
                            "@timestamp": {
                                "gte": start_time,
                                "lte": "now",
                                "format": "epoch_millis"
                            }
                        }
                    }
                ],
                "must_not": []
            }
        },
        "size": 0,
        "_source": {
            "excludes": []
        },
        "aggs": {
            "3": {
                "terms": {
                    "field": "beat.hostname.keyword",
                    "size": 5,
                    "order": {
                        "1": "desc"
                    }
                },
                "aggs": {
                    "1": {
                        "avg": {
                            "field": "memory.usage_p"
                        }
                    },
                    "2": {
                        "avg": {
                            "field": "cpu.totalUsage"
                        }
                    }
                }
            }
        }
    })
    utilization = {}
    for host in res['aggregations']['3']['buckets']:
        utilization[host['key']] = {'cpu': host['1']['value'], 'memory': host['2']['value']}
    return utilization


def get_hosts_info(res):
    """
    This function returns the hostname, cup utilization and memory utilization for all active hosts.
    :param res:
    :return: macroservice information of hosts.
    """
    hosts_info = []
    for host in res:
        host_info = {'name': host['key'], 'cpu': 1 - float(host['1']['value']), 'memory': host['2']['value']}
        hosts_info.append(host_info)
    return hosts_info


def get_base_host_names(hosts_info):
    """
    This function returns the base host names. These hosts are the original hosts of the application.
    Elascale scales hosts and with same base name that will be concatenated with '.' and the timestamp.
    So, if a host name does not contain '.', it means that host is the original host of the application.
    :param hosts_info:
    :return: the original host names
    """
    base_host_names = []
    for host in hosts_info:
        if not str(host['name']).__contains__('.'):
            base_host_names.append(host['name'])
    return base_host_names


# returns the cpu utilization percentage
def get_vm_cpu_util(host_name):
    res = es.search(index="metricbeat-*", body={
        "size": 1,
        "aggs": {
            "avg-cpu-idle": {
                "avg": {
                    "field": "system.cpu.idle.pct"
                }
            },
        },
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": "metricset.name: cpu AND beat.name: like " + host_name,
                            "analyze_wildcard": True
                        }
                    },
                    {
                        "range": {
                            "@timestamp": {
                                "gte": start_time,
                                "lte": "now",
                                "format": "epoch_millis"
                            }
                        }
                    }
                ],
                "must_not": []
            }
        },
        "_source": {
            "excludes": []
        },
        "version": True
    })
    for doc in res['hits']['hits']:
        print("%s" % doc['_source'])
        break
    return 1 - (res['aggregations']['avg-cpu-idle']['value'])  # to have the cpu usage = 1 - idle


# using metricbeat index we return the percentage  of memory usage.
def get_vm_mem_util(host_name):
    res = es.search(index="metricbeat-*", body={
        "size": 1,
        "aggs": {
            "avg-mem-util": {
                "avg": {
                    "field": "system.memory.actual.used.pct"
                }
            },
        },
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": "metricset.name: memory AND beat.name: " + host_name,
                            "analyze_wildcard": True
                        }
                    },
                    {
                        "range": {
                            "@timestamp": {
                                "gte": start_time,
                                "lte": "now",
                                "format": "epoch_millis"
                            }
                        }
                    }
                ],
                "must_not": []
            }
        },
        "_source": {
            "excludes": []
        },
        "version": True
    })
    for doc in res['hits']['hits']:
        print("%s" % doc['_source'])
        break
    return res['aggregations']['avg-mem-util']['value']


# using dockbeat index we get total cpu usage by the container in last minute
def get_cont_cpu_util(container_name):
    res = es.search(index="dockbeat*", body={
        "size": 1,
        "aggs": {
            "avg-cpu-util": {
                "avg": {
                    "field": "cpu.totalUsage"
                }
            },
        },
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": "container.names: like " + container_name,
                            "analyze_wildcard": True
                        }
                    },
                    {
                        "range": {
                            "@timestamp": {
                                "gte": start_time,
                                "lte": "now",
                                "format": "epoch_millis"
                            }
                        }
                    }
                ],
                "must_not": []
            }
        },
        "_source": {
            "excludes": []
        },
        "version": True
    })
    print("%s" % res)
    return res['aggregations']['avg-cpu-util']['value']


# using dockbeat index we get memory usage by the container in last minute
def get_cont_mem_util(container_name):
    res = es.search(index="dockbeat*", body={
        "size": 1,
        "aggs": {
            "avg-mem-util": {
                "avg": {
                    "field": "memory.usage"
                }
            },
        },
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": "container.names: like " + container_name,
                            "analyze_wildcard": True
                        }
                    },
                    {
                        "range": {
                            "@timestamp": {
                                "gte": start_time,
                                "lte": "now",
                                "format": "epoch_millis"
                            }
                        }
                    }
                ],
                "must_not": []
            }
        },
        "_source": {
            "excludes": []
        },
        "version": True
    })
    print("%s" % res)
    return res['aggregations']['avg-mem-util']['value']
