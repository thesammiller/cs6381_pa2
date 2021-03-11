#
# Team 6
# Programming Assignment #2
#
# Contents:
#    - ZooAnimal
#

import codecs
import time
import threading

from kazoo.client import KazooClient, KazooState

from util import local_ip4_addr_list

ZOOKEEPER_ADDRESS = "10.0.0.1"
ZOOKEEPER_PORT = "2181"
ZOOKEEPER_LOCATION = '{zookeeper_ip}:{zookeeper_port}'.format(zookeeper_ip=ZOOKEEPER_ADDRESS,
                                                              zookeeper_port=ZOOKEEPER_PORT)
# For mininet -> 10.0.0.x
NETWORK_PREFIX = "10"


ZOOKEEPER_PATH_STRING = '/{approach}/{role}/{topic}'
PATH_TO_MASTER_BROKER = "/broker/broker/master"
PATH_TO_FLOOD_BROKER = "/flood/broker/master"

#####################################################
#
# ZooAnimal for Zookeeper Registrants
# Broker will Overload Zookeeper Register
# Properties must be defined by children:
#   - role
#   - approach
#   - topic
#
######################################################


def start_kazoo_client():
    zk = KazooClient(hosts=ZOOKEEPER_LOCATION)
    zk.start()
    return zk

class ZooAnimal:
    def __init__(self):
        self.zk = start_kazoo_client() #KazooClient(hosts=ZOOKEEPER_LOCATION)
        #self.zk.start()

        # Use util function to get IP address
        self.ipaddress = [ip for ip in list(local_ip4_addr_list()) if ip.startswith(NETWORK_PREFIX)][0]

        # Inheriting children should assign values to fit the scheme
        # /approach/role/topic
        self.approach = None
        self.role = None
        self.topic = None
        # Zookeeper
        #self.election = None
        self.election = self.zk.Election('/broker/broker', self.ipaddress)

    def zookeeper_watcher(self):
        @self.zk.DataWatch("/broker/broker/master")
        def zookeeper_election(data, stat, event):
            print("Setting election watch.")
            print(data)
            if data is None:
                print("Data is none.")
                self.election.run(self.zookeeper_master)

    '''
    def post_election(self):
        print("After the election")
        #if self.zk.exists("/broker/broker/master") == None and self.election.lock.contenders()[0] == self.ipaddress:
        print("I am the leader now")
        self.zookeeper_master()
    '''

    def zookeeper_master(self):
        print("Becoming the master.")
        role_topic = ZOOKEEPER_PATH_STRING.format(approach=self.approach, role=self.role, topic='master')
        encoded_ip = codecs.encode(self.ipaddress, "utf-8")
        self.zk.create(role_topic, ephemeral=True, makepath=True, value=encoded_ip)
        return True

    def zookeeper_register(self):
        # This will result in a path of /broker/publisher/12345 or whatever
        # or /broker/broker/master
        role_topic = ZOOKEEPER_PATH_STRING.format(approach=self.approach, role=self.role, topic=self.topic)
        print("Zooanimal IP-> {}".format(self.ipaddress))
        encoded_ip = codecs.encode(self.ipaddress, "utf-8")
        if self.role == 'broker':
            self.zk.create(role_topic, ephemeral=True, sequence=True, makepath=True, value=encoded_ip)
            if self.zk.exists("/broker/broker/master") == None:
                self.zookeeper_master()
            else:
                self.zookeeper_watcher()
        elif self.role =='publisher' or self.role=='subscriber':
            # zk.ensure_path checks if path exists, and if not it creates it
            try:
                self.zk.create(role_topic, ephemeral=True, makepath=True)
            except:
                print("Topic already exists.")

            # get the string from the path - if it's just created, it will be empty
            # if it was created earlier, there should be other ip addresses
            other_ips = self.zk.get(role_topic)

            # Zookeeper uses byte strings --> b'I'm a byte string'
            # We don't like that and need to convert it
            other_ips = codecs.decode(other_ips[0], 'utf-8')

            # if we just created the path, it will be an empty byte string
            # if it's empty, this will be true and we'll add our ip to the end of the other ips
            if other_ips != '':
                print("Adding to the topics list")
                self.zk.set(role_topic, codecs.encode(other_ips + ' ' + self.ipaddress, 'utf-8'))
            # else the byte string is empty and we can just send our ip_address
            else:
                self.zk.set(role_topic, codecs.encode(self.ipaddress, 'utf-8'))


    def get_broker(self):
        broker_data = self.zk.get(PATH_TO_MASTER_BROKER)[0]
        master_broker = codecs.decode(broker_data, 'utf-8')
        if master_broker != '':
            return master_broker
        else:
            raise Exception("No master broker.")

    def get_flood_broker(self):
        broker_data = self.zk.get(PATH_TO_FLOOD_BROKER)[0]
        master_broker = codecs.decode(broker_data, 'utf-8')
        if master_broker != '':
            return master_broker
        else:
            raise Exception("No master broker.")

