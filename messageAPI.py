#
# Team 6
# Programming Assignment #2
#
# Contents:
#   - BrokerProxy
#   - BrokerPublisher
#   - BrokerSubscriber
#
#   - FloodProxy
#   - FloodPublisher
#   - FloodSubscriber

# Standard Library
import codecs
from collections import defaultdict
import sys
import time

# Third Party
import zmq

# Local
from util import local_ip4_addr_list
from zooanimal import ZooAnimal, ZOOKEEPER_ADDRESS, ZOOKEEPER_PORT, ZOOKEEPER_PATH_STRING

BROKER_PROXY_ADDRESS = "10.0.0.2"
BROKER_PUBLISHER_PORT = "5555"
BROKER_SUBSCRIBER_PORT = "5556"

FLOOD_PROXY_ADDRESS = "10.0.0.3"
FLOOD_PROXY_PORT = "5555"
FLOOD_SUBSCRIBER_PORT = "5556"

SERVER_ENDPOINT = "tcp://{address}:{port}"




class ZeroProxy(ZooAnimal):
    pass


##################################################################################
#
#
#           B R O K E R   P R O X Y 
#
#
####################################################################################

class BrokerProxy(ZooAnimal):
    def __init__(self):
        # ZooAnimal Initialize
        super().__init__()
        # ZooKeeper properties
        self.approach = 'broker'
        self.role = 'broker' # as opposed to pub/sub
        # Will be either Master or Backup, set in zookeeper_register
        self.topic = 'pool'
        # ZMQ Setup
        self.context = zmq.Context()
        self.poller = zmq.Poller()
        self.xsubsocket = self.create_XSub()
        self.xpubsocket = self.create_XPub()
        # API Registration
        self.zookeeper_register()

    

    def get_context(self):
        return self.context

    def create_XSub(self):
        self.xsubsocket = self.context.socket(zmq.XSUB)
        self.xsubsocket.bind(SERVER_ENDPOINT.format(address="*", port=BROKER_PUBLISHER_PORT))
        self.register_poller(self.xsubsocket)
        return self.xsubsocket

    def create_XPub(self):
        self.xpubsocket = self.context.socket(zmq.XPUB)
        self.xpubsocket.setsockopt(zmq.XPUB_VERBOSE, 1)
        self.xpubsocket.bind(SERVER_ENDPOINT.format(address="*", port=BROKER_SUBSCRIBER_PORT))
        self.register_poller(self.xpubsocket)
        return self.xpubsocket

    # unsure of parameters
    def register_poller(self, entity_id):
        self.poller.register(entity_id, zmq.POLLIN)
        return self.poller

    def poll(self):
        # print ("Poll with a timeout of 1 sec")
        self.events = dict(self.poller.poll(1000))
        print("Events received = {}".format(self.events))
        self.getPubData()
        self.getSubData()

    def getPubData(self):
        if self.xsubsocket in self.events:
            msg = self.xsubsocket.recv_string()
            print("Publication = {}".format(msg))
            # send the message to subscribers
            self.xpubsocket.send_string(msg)

    def getSubData(self):
        if self.xpubsocket in self.events:
            msg = self.xpubsocket.recv_string()
            print("Subscription = {}".format(msg))
            # send the subscription info to publishers
            self.xsubsocket.send_string(msg)

    def run(self):
        while True:
            try:
                self.poll()
            except NameError as e:
                print("Exception thrown: {}".format(sys.exc_info()[1]))


#############################################################
#
#
#           B R O K E R   P U B L I S H E R
#
#
##############################################################

class BrokerPublisher(ZooAnimal):

    def __init__(self, topic):
        # ZooAnimal Initialize
        super().__init__()
        # ZooAnimal properties
        self.approach = 'broker'
        self.role = 'publisher'
        self.topic = topic
        # ZMQ Properties
        self.context = zmq.Context()
        self.socket = None
        # API Operations
        self.zookeeper_register()
        self.get_broker()
        print("Publisher BROKER -> {}".format(self.broker))

    def broker_update(self, data):
        for i in range(10):
            try:
                self.get_broker()
                self.register_pub()
                break
            except:
                print("No master yet...")
            time.sleep(0.2)

    def register_pub(self):
        pubId = SERVER_ENDPOINT.format(address=self.broker, port=BROKER_PUBLISHER_PORT)
        self.socket = self.context.socket(zmq.PUB)
        print("Publisher connecting to proxy at: {}".format(pubId))
        self.socket.connect(pubId)

    def publish(self, value):
        # print ("Message API Sending: {} {}".format(self.topic, value))
        now = time.time()
        self.socket.send_string("{topic} {time} {value}".format(topic=self.topic, time=now, value=value))


################################################################################
#
#
#             B R O K E R   S U B S C R I B E R
#
#
################################################################################


class BrokerSubscriber(ZooAnimal):

    def __init__(self, topic):
        # ZooAnimal initialize
        super().__init__()
        # ZooAnimal Properties
        self.approach = 'broker'
        self.role = 'subscriber'
        self.topic = topic
        # ZMQ
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        # API
        self.zookeeper_register()
        self.get_broker()
        print("Subscriber Broker --> {}".format(self.broker))

    def broker_update(self, data):
        for i in range(10):
            try:
                self.get_broker()
                self.register_sub()
                break
            except:
                print("No master yet...")
            time.sleep(0.5)
        

    def register_sub(self):
        subId = SERVER_ENDPOINT.format(address=self.broker, port=BROKER_SUBSCRIBER_PORT)
        print("Registering subscriber at: {}".format(subId))
        self.socket.connect(subId)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, self.topic)

    # sub gets message
    def notify(self):
        message = self.socket.recv_string()
        # Split message based on our format
        topic, pub_time, *values = message.split()
        # convert time to epoch in seconds
        seconds = time.time()
        difference = seconds - float(pub_time)
        # Write the difference in time from the publisher to the file
        with open("./logs/seconds_{}.log".format(self.ipaddress), "a") as f:
            f.write(str(difference) + "\n")

        return " ".join(values)


"<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>"

FLOOD_PUBLISHER = "publisher"
FLOOD_SUBSCRIBER = "subscriber"
NO_REGISTERED_ENTRIES = ""


#########################################################
#
#            F L O O D   P R O X Y
#
################################################################

class FloodProxy(ZooAnimal):
    def __init__(self):
        # ZooAnimal
        super().__init__()
        self.approach = 'flood'
        self.role = 'broker'
        self.topic = 'pool'
        # ZMQ
        self.context = zmq.Context()  # returns a singleton object
        self.incoming_socket = self.context.socket(zmq.REP)
        # creating a server bound to port 5555
        self.incoming_socket.bind(SERVER_ENDPOINT.format(address="*", port=FLOOD_PROXY_PORT))
        # Initialize Registry
        self.registry = {}
        self.registry[FLOOD_PUBLISHER] = defaultdict(list)
        self.registry[FLOOD_SUBSCRIBER] = defaultdict(list)
        # API registration
        #backup_path = ZOOKEEPER_PATH_STRING.format(approach=self.approach, role=self.role, topic='backup')
        #self.zk.create(backup_path, makepath=True, ephemeral=True, sequence=True)
        self.zookeeper_register()

    def checkRegistry(self):
        if self.zk.get("/flood/broker/master")[0] == codecs.encode(self.ipaddress, 'utf-8'): # And we are the master.
            # get all the /flood/subscriber children
            children = self.zk.get_children("/flood/subscriber")
            # entry = 12345
            for entry in children:
                #e = codecs.decode(entry, 'utf-8')
                decoded_data = codecs.decode(self.zk.get('/flood/subscriber/{}'.format(entry))[0], 'utf-8')
                print("SUB -> {}".format(decoded_data))
                self.registry['subscriber'][entry] = decoded_data.split()
            children = self.zk.get_children("/flood/publisher")
            for entry in children:
                decoded_data = codecs.decode(self.zk.get('/flood/publisher/{}'.format(entry))[0], 'utf-8')
                self.registry['publisher'][entry] = decoded_data.split()
                print("PUB -> {}".format(decoded_data))

    # Application interface --> run() encloses basic functionality
    def run(self):
        while True:
            self.listen()
            self.checkRegistry()

    def listen(self):
        #  Wait for next request from client
        self.message = self.incoming_socket.recv_string()
        role, topic, ipaddr = self.message.split()
        print("Received request: Role -> {role}\t\tTopic -> {topic}\t\tData -> {data}".format(role=role, 
                                                                                              topic=topic,
                                                                                              data=ipaddr))
        if ipaddr not in self.registry[role][topic]:
            self.registry[role][topic].append(ipaddr)

        # based on our role, we need to find the companion ip addresses in the registry
        if role == FLOOD_PUBLISHER:
            other = FLOOD_SUBSCRIBER
        if role == FLOOD_SUBSCRIBER:
            other = FLOOD_PUBLISHER

        # if we have entries in the registry for the companion ip addresses
        # TODO: shouldn't this be ` if self.registry[other][topic]:`
        if self.registry[other][topic]:
            # registry[other][topic] is a list of ip addresses
            # these belong to the companion to the registering entity
            result = " ".join(self.registry[other][topic])
        # we'll have to check for nones in sub and pub
        else:
            result = NO_REGISTERED_ENTRIES
        #print(result)
        print("REGISTRY -> {}".format(self.registry))
        self.incoming_socket.send_string(result)


############################################################################################
#
#
#            F L O O D   P U B L I S H E R
#
#
##########################################################################################

class FloodPublisher(ZooAnimal):

    def __init__(self, topic):
        # Initialize ZooAnimal
        super().__init__()
        # ZooAnimal Properties
        self.approach = "flood"
        self.role = FLOOD_PUBLISHER
        self.topic = topic
        #self.broker = self.get_broker()
        self.zk_path = ZOOKEEPER_PATH_STRING.format(approach=self.approach, role=self.role, topic=self.topic)
        #print("{} -> ZooAnimal Setup".format(self.zk_path))
        # ZMQ Setup
        self.context = zmq.Context()
        self.context.setsockopt(zmq.LINGER, 10)
        #print("{} -> ZMQ Setup".format(self.zk_path))
        # API Setup
        self.registry = []
        self.message = ""
        self.zookeeper_register()
        self.get_broker()


    def broker_update(self, data):
        self.registry = [] 
        self.broker = None
        for i in range(10):
            try:
                self.get_broker()
                self.register_pub()
                break
            except:
                print("No master yet...")
            time.sleep(1)

    def register_pub(self):
        print("{} - > Registering publisher to address {}".format(self.zk_path, self.broker))
        # Create handshake message for the Flood Proxy
        hello_message = "{role} {topic} {ipaddr}".format(role=self.role, 
                                                              topic=self.topic, 
                                                              ipaddr=self.ipaddress)
        # Send to the proxy
        hello_socket = self.context.socket(zmq.REQ)
        print(self.broker)
        connect_str = SERVER_ENDPOINT.format(address=self.broker, port=FLOOD_PROXY_PORT)
        hello_socket.connect(connect_str)
        hello_socket.send_string(hello_message)
        # Wait for return message
        event = hello_socket.poll(timeout=3000)  # wait 3 seconds
        if event == 0:
        # timeout reached before any events were queued
            pass
        else:
        #    events queued within our time limit
            reply = hello_socket.recv_string(flags=zmq.NOBLOCK)
            print(reply)
            if reply != NO_REGISTERED_ENTRIES:
                self.registry = reply.split()
                print("{zk_path} -> Received new registry: {registry}".format(zk_path=self.zk_path, 
                                                                          registry=self.registry))
            if reply == NO_REGISTERED_ENTRIES:
                print("No entries.")                
                self.registry = []

    def publish(self, data):
        print("{} -> Publishing...".format(self.zk_path))
        self.register_pub()
        for ipaddr in self.registry:
            print("{} -> Address {}".format(self.zk_path, ipaddr))
            seconds = time.time()
            self.socket = self.context.socket(zmq.REQ)
            self.connect_str = SERVER_ENDPOINT.format(address=ipaddr, port=FLOOD_SUBSCRIBER_PORT)
            #print(self.connect_str)
            self.socket.connect(self.connect_str)
            self.message = "{time} {data}".format(time=seconds, data=data)
            #print(self.message)
            self.socket.send_string(self.message)
            reply = self.socket.recv_string()

###################################################################################################################
#
#
#            F L O O D    S U B S C R I B E R
#
#
####################################################################################################################

class FloodSubscriber(ZooAnimal):
    def __init__(self, topic):
        # Initialize ZooAnimal
        super().__init__()
        # ZooAnimal Properties
        self.approach = "flood"
        self.role = FLOOD_SUBSCRIBER
        self.topic = topic
        self.zk_path = ZOOKEEPER_PATH_STRING.format(approach=self.approach, role=self.role, topic=self.topic)
        #print("{} -> ZooAnimal Setup".format(self.zk_path))
        # ZMQ Setup
        self.context = zmq.Context()  # returns a singleton object
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(SERVER_ENDPOINT.format(address="*", port=FLOOD_SUBSCRIBER_PORT))
        #print("{} -> ZMQ Setup".format(self.zk_path))
        # API Registration
        self.zookeeper_register()
        self.get_broker()
        #self.register_sub()
        #print("{} -> API Setup".format(self.zk_path))

    def broker_update(self, data):
        for i in range(10):
            try:
                self.get_broker()
                self.register_sub()
                break
            except:
                print("No master yet...")
            time.sleep(1)

    def register_sub(self):
        #print("{} -> Registering subscriber API".format(self.zk_path))
        self.hello_socket = self.context.socket(zmq.REQ)
        self.connect_str = SERVER_ENDPOINT.format(address=self.broker, port=FLOOD_PROXY_PORT)
        self.hello_socket.connect(self.connect_str)
        self.send_address = "{ip}".format(ip=self.ipaddress)
        self.hello_message = "{role} {topic} {ipaddr}".format(role=self.role, 
                                                              topic=self.topic, 
                                                              ipaddr=self.send_address)
        #print("Hello message -> " + self.hello_message)
        self.hello_socket.send_string(self.hello_message)
        self.reply = self.hello_socket.recv_string()
        #print("Reply message -> " + self.reply)

    def notify(self):
        print("{} -> Waiting for notification".format(self.zk_path))
        self.message = self.socket.recv_string()
        # Write to file with time difference from sent to received
        seconds = time.time()
        pub_time, *values = self.message.split()
        difference = seconds - float(pub_time)
        with open("logs/{approach}_{ip}.log".format(approach=self.approach, ip=self.ipaddress), "a") as f:
            f.write(str(difference) + "\n")

        print("{zk_path} -> Subscriber received data {data}".format(zk_path=self.zk_path, data=" ".join(values)))
        self.socket.send_string(self.message)
        return " ".join(values)
