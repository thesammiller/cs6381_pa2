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

PATH_TO_MASTER = {'flood': PATH_TO_FLOOD_BROKER,
                  'broker': PATH_TO_MASTER_BROKER}


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
        #Will only be set by pub and sub
        self.broker = None
        # Zookeeper
        #self.election = None
        self.election = self.zk.Election('/broker/broker', self.ipaddress)
        self.zk_seq_id = None

    def zookeeper_watcher(self, watch_path):
        @self.zk.DataWatch(watch_path)
        def zookeeper_election(data, stat, event):
            print("Setting election watch.")
            print("Watching node -> ", data)
            if data is None:
                print("Data is none.")
                self.election.run(self.zookeeper_register)
                #self.election.cancel()

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
            broker_path = "/{}/broker".format(self.approach)
            #for i in range(10):
            #    if self.zk.exists("/broker/broker/master") == None:
            #        self.zookeeper_master()
            #        break
            #    time.sleep(.44)
            if self.zk_seq_id == None:
                self.zk.create(role_topic, ephemeral=True, sequence=True, makepath=True, value=encoded_ip)
                brokers = self.zk.get_children(broker_path)
                try:
                    brokers.pop(brokers.index("master"))
                except:
                    pass
                brokers = [x for x in brokers if "lock" not in x]
                broker_nums = {y: int(y[4:]) for y in brokers}
                #sort based on the values
                broker_sort = sorted(broker_nums, key=lambda data: broker_nums[data])
                latest_id = broker_sort[-1]
                print(latest_id)
                self.zk_seq_id = latest_id
            for i in range(10):
                if self.zk.exists(broker_path+"/master") == None:
                    self.zookeeper_master()
                    break
                time.sleep(0.2)
            if self.zk.exists(broker_path + "/master"):
                # Get all the children
                path = self.zk.get_children(broker_path)
                # Remove the master
                path.pop(path.index("master"))
                #path.pop(path.index(self.zk_seq_id))
                # Process out the locks
                path = [x for x in path if "lock" not in x]
                #Convert into a dictionary of znode:sequential
                #We keep the path name as the key
                #Use the sequential number as the value
                # e.g. key pool000001 value 000001
                path_nums = {y: int(y[4:]) for y in path}
                #sort based on the values
                path_sort = sorted(path_nums, key=lambda data: path_nums[data])
                # Watch the node that is previous to us
                # path_sort[0] is the lowest number, [-1] is us, so [-2] is one before usd
                #if path_sort.index(self.zk_seq_id) == 0:
                #    if self.zk.exists("/broker/broker/master") == None:
                #        self.zookeeper_master()
                #else:
                previous = path_sort[path_sort.index(self.zk_seq_id)-1]
                #previous = path_sort[-1]
                watch_path = broker_path + "/" + previous
                self.zookeeper_watcher(watch_path)
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
    
    # This is a function stub for the get_broker watch callback
    # The child is expected to implement their own logic
    # Pub and Sub need to register_sub()
    def broker_update(self, data):
        print("Broker updated.")
        print("Data -> {}".format(data))
        pass

    def get_broker(self):
        for i in range(10):
            if self.zk.exists(PATH_TO_MASTER[self.approach]):
                node_data = self.zk.get(PATH_TO_MASTER[self.approach], watch=self.broker_update)
                broker_data = node_data[0]
                master_broker = codecs.decode(broker_data, 'utf-8')
                if master_broker != '':
                    self.broker = master_broker
                else:
                    raise Exception("No master broker.")
            time.sleep(0.2)
    '''
    def get_flood_broker(self):
        broker_data = self.zk.get(PATH_TO_FLOOD_BROKER)[0]
        master_broker = codecs.decode(broker_data, 'utf-8')
        if master_broker != '':
            return master_broker
        else:
            raise Exception("No master broker.")
    '''
