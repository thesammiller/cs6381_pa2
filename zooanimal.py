#
# Team 6
# Programming Assignment #2
#
# Contents:
#    - ZooAnimal
#

import codecs

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


class ZooAnimal:
    def __init__(self):
        self.zk = KazooClient(hosts=ZOOKEEPER_LOCATION)
        self.zk.start()

        # Use util function to get IP address
        self.ipaddress = [ip for ip in list(local_ip4_addr_list()) if ip.startswith(NETWORK_PREFIX)][0]

        # Inheriting children should assign values to fit the scheme
        # /approach/role/topic
        self.approach = None
        self.role = None
        self.topic = None

    def zookeeper_register(self):
        # This will result in a path of /broker/publisher/12345 or whatever
        # or /broker/broker/master
        role_topic = ZOOKEEPER_PATH_STRING.format(approach=self.approach, role=self.role, topic=self.topic)
        print("Zooanimal IP-> {}".format(self.ipaddress))
        try:
            self.zk.create(role_topic, ephemeral=True)
        except Exception as e:
            print("{} -> Topic already created.".format(e))

        # zk.ensure_path checks if path exists, and if not it creates it
        self.zk.ensure_path(role_topic)

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

