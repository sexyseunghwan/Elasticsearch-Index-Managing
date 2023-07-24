""" 
Author      : Seunghwan Shin 
Create date : 2023-06-21 
Description : The code is a batch code that removes the largest index.
              Elasticsearch cluster(DEV,QA,STG) disk full is frequently occurring.
              This code operates when the disk occupancy rate is more than 80%.
    
History     : 2023-06-21 Seunghwan Shin       # first create
              2023-07-17 Seunghwan Shin       # Modified the code to leave a separate "INDEX DELETE" log.
              
""" 
from datetime import datetime
from elasticsearch import Elasticsearch
import time
import ssl
import logging
import logging.handlers
import json


"""
Function that records the log
"""
def setupLogging(log_inst_name, path, log_filename):
    
    file_handler = logging.handlers.TimedRotatingFileHandler('{}/{}.log'.format(path, log_filename), when="midnight", backupCount=10)
    file_handler.setFormatter(logging.Formatter('[ %(asctime)s ] %(levelname)s : %(message)s'))
    
    logger = logging.getLogger(log_inst_name)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    return logger



"""
Elasticsearch Class Objects
"""
class Elastic:
    def __init__(self, cluster_ip_port, cluster_id,cluster_pw,cluster_ver,cluster_ssl):
        self.cluster_ip_port = cluster_ip_port
        self.cluster_id = cluster_id
        self.cluster_pw = cluster_pw
        self.cluster_ver = cluster_ver
        self.cluster_ssl = cluster_ssl


""" 
Elasticsearch Connection Function
""" 
def elastic_conn(cluster):
    
    es = None
    ip_lists = cluster.cluster_ip_port
    user_id = cluster.cluster_id
    user_pw = cluster.cluster_pw
    ssl_check = cluster.cluster_ssl

    # If x-pack security is not applied
    if (cluster.cluster_id == None and user_pw == None):
        es = Elasticsearch(ip_lists,sniff_on_connection_fail=True,sniffer_timeout=5,timeout=30)
    
    # If x-pack security or search guard is applied
    else:
        # If x-pack security is applied
        if (ssl_check == None):
            es = Elasticsearch(ip_lists,sniff_on_connection_fail=True,sniffer_timeout=5,timeout=30,http_auth=(user_id,user_pw))
       
        # If search-guard is applied
        else:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            es = Elasticsearch(
                hosts=ip_lists
                ,sniff_on_connection_fail=True
                ,sniffer_timeout=5
                ,timeout=30
                ,scheme='https'
                ,http_auth=(user_id,user_pw)
                ,ssl_context=context) 

    es.ping()

    return es


"""
Returns elasticsearch objects
"""
def get_es_cluster_obj(server_info, server_logger):

    try:
        
        with open(server_info, "r") as f:
            inner_data = json.load(f)

        cluster_ip_port = inner_data.get('cluster_ip_port',None)
        cluster_id = inner_data.get('id',None)
        cluster_pw = inner_data.get('pw',None)
        cluster_ver = inner_data.get('ver',None)
        cluster_ssl = inner_data.get('ssl',None)
        
        elastics = Elastic(cluster_ip_port,cluster_id,cluster_pw,cluster_ver,cluster_ssl)

        return elastics

    except Exception as e:
        server_logger.error(str(e), exc_info=True)
        return None
    

def delete_big_size_index(cluster, server_logger):

    try:
        es = elastic_conn(cluster)
        cluster_name = es.cluster.health(params={"filter_path": "cluster_name"})['cluster_name']
        
        delete_flag = True

        while(delete_flag):
            
            response = es.transport.perform_request('GET', '/_nodes/stats/fs')
            
            # From JSON Extract the disk capacity of each node.
            for node_info in response['nodes'].items():
                node_name = node_info[1]['name']
                disk_stats = node_info[1]['fs']['total']
                host = node_info[1]['host']
                
                total_disk = disk_stats['total_in_bytes']
                available_disk = disk_stats['available_in_bytes']
                using_disk_per = round(((total_disk - available_disk) / total_disk) * 100,2)

                if (using_disk_per >= 80):
                    delete_flag = True
                    server_logger.info('ES-NAME : {} // NODE-NAME: {} // ip-addr: {} // Capacity of this NODE is close to the LIMIT.'.format(cluster_name, node_name, host))
                    break
                else:
                    delete_flag = False


            # Logic that handles when a particular index needs to be removed
            if (delete_flag):
                # Get all index information from Elasticsearch
                index_resp = es.cat.indices(v=True, s='store.size:desc')

                for line in index_resp.splitlines():
                    index_name = line.split()[2]
                    index_size = line.split()[8]
                    
                    # Among the indexes in ES, the INDEX with the largest capacity excluding the system index is REMOVED.
                    if (not index_name.startswith('.') and index_name != 'index'):
                        # REMOVE INDEX
                        delete_resp = es.indices.delete(index=index_name)
                        now = datetime.now().strftime("%Y-%m-%d")

                        delete_logger = setupLogging('delete_log','./delete_log','{}_index_deleted'.format(now))
                        delete_logger.info("ES-NAME : {} // Removing index : {} // size : {}".format(cluster_name, index_name, index_size))
                        
                        time.sleep(5)
                         
                        if delete_resp["acknowledged"]:
                            delete_logger.info("{} index deletion complete".format(index_name))
                        else:
                            delete_logger.error("{} index deletion faild".format(index_name))

                        break
        
    except Exception as e:
        server_logger.error(str(e), exc_info=True)


""" 
main function - execute
"""
def main():

    now = datetime.now().strftime("%Y-%m-%d")
    server_logger = setupLogging('server_log','./server_log',now)
    server_logger.info("Elasticsearch cluster index monitoring system has started operation.")

    server_info = "./server_info.json"  
    es_info = get_es_cluster_obj(server_info, server_logger)
    
    while True:
        delete_big_size_index(es_info, server_logger)
        time.sleep(60)


""" 
main function - execute
""" 
if __name__ == '__main__':
    main()