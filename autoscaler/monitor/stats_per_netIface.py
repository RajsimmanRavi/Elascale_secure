import engine_config

# Monitoring component of the MAPE-K loop (written by ByungChul Park, modified later by Rajsimman Ravi)

def get_microservices_utilization(es):
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
                                "gte": engine_config.START_TIME,
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


def get_macroservices_utilization(es):
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
                                "gte": engine_config.START_TIME,
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
            "6": {
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
                    },
                    "3": {
                        "terms": {
                            "field": "system.network.name",
                            "order": {
                                "1": "desc"
                            }
                        },
                        "aggs":{
                            "1": {
                                "avg": {
                                    "field": "system.network.in.bytes"
                                }
                            },
                            "2": {
                                "avg": {
                                    "field": "system.network.out.bytes"
                                }
                            }
                        }
                    }
                }
            }
        }
    })

    utilization = {}
    data = res['aggregations']['6']['buckets']
    hosts_info = get_hosts_info(data)
    base_hosts = get_base_host_names(hosts_info)

    print(data)
    print(hosts_info)

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
