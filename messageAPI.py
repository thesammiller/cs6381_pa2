#
# Team 6
# Programming Assignment #1
#
# Contents:
#   - BrokerProxy
#   - BrokerPublisher
#   - BrokerSubscriber
#
#   - FloodProxy
#   - FloodPublisher
#   - FloodSubscriber

from collections import defaultdict
import datetime
import os
from random import randrange
import sys
import time

import zmq
from util import local_ip4_addr_list

BROKER_PROXY_ADDRESS = "10.0.0.1"
BROKER_PUBLISHER_PORT = "5555"
BROKER_SUBSCRIBER_PORT = "5556"

FLOOD_PROXY_ADDRESS = "10.0.0.2"
FLOOD_PROXY_PORT = "5555"
FLOOD_SUBSCRIBER_PORT = "5556"

SERVER_ENDPOINT = "tcp://{address}:{port}"

##################################################################################
#
#
#           B R O K E R   P R O X Y 
#
#
####################################################################################

class BrokerProxy:
    def __init__(self):
        self.context = zmq.Context()
        self.poller = zmq.Poller()
        self.xsubsocket = self.create_XSub()
        self.xpubsocket = self.create_XPub()
        
    def get_context(self): 
        return self.context 

    def create_XSub(self):
        self.xsubsocket = self.context.socket(zmq.XSUB)
        self.xsubsocket.bind(SERVER_ENDPOINT.format(address="*", port=BROKER_PUBLISHER_PORT))
        self.register_poller(self.xsubsocket)
        return self.xsubsocket

    def create_XPub(self):
        self.xpubsocket = self.context.socket (zmq.XPUB)
        self.xpubsocket.setsockopt(zmq.XPUB_VERBOSE, 1)
        self.xpubsocket.bind (SERVER_ENDPOINT.format(address="*", port=BROKER_SUBSCRIBER_PORT))
        self.register_poller(self.xpubsocket)
        return self.xpubsocket

    # unsure of parameters
    def register_poller(self, entity_id):
        self.poller.register(entity_id, zmq.POLLIN)
        return self.poller

    def poll(self):
        #print ("Poll with a timeout of 1 sec")
        self.events = dict (self.poller.poll (1000))
        print ("Events received = {}".format (self.events))
        self.getPubData()
        self.getSubData()

    def getPubData(self):
        if self.xsubsocket in self.events:
            msg = self.xsubsocket.recv_string()
            print ("Publication = {}".format (msg))
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
            except (NameError):
                print("Exception thrown: {}".format(sys.exc_info()[1]))

                
#############################################################
#
#
#           B R O K E R   P U B L I S H E R
#
#
##############################################################
                
class BrokerPublisher:

    def __init__(self, topic):
        self.context = zmq.Context()
        self.socket = None
        self.topic = topic

    def register_pub(self):
        pubId = SERVER_ENDPOINT.format(address=BROKER_PROXY_ADDRESS, port=BROKER_PUBLISHER_PORT)
        self.socket = self.context.socket(zmq.PUB)
        print("Publisher connecting to proxy at: {}".format(pubId))
        self.socket.connect(pubId)
        
    def publish(self, value):
        #print ("Message API Sending: {} {}".format(self.topic, value))
        seconds = (datetime.datetime.now() - datetime.datetime(1970,1,1)).total_seconds()
        #print(seconds)
        time = seconds
        self.socket.send_string("{topic} {time} {value}".format(topic=self.topic, time=time, value=value))

################################################################################
#
#
#             B R O K E R   S U B S C R I B E R
#
#
################################################################################
        

class BrokerSubscriber:

    def __init__(self, topic):
        self.context = zmq.Context()
        self.topic = topic

    def register_sub(self):
        subId = SERVER_ENDPOINT.format(address=BROKER_PROXY_ADDRESS, port=BROKER_SUBSCRIBER_PORT)
        # Since we are the subscriber, we use the SUB type of the socket
        self.socket = self.context.socket(zmq.SUB)
        print("Collecting updates from weather server proxy at: {}".format(subId))
        self.socket.connect(subId)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, self.topic)

    #sub gets message
    def notify(self):
        message = self.socket.recv_string()
        #print("Message received")
        topic, time, *values = message.split()
        #epoch
        seconds = (datetime.datetime.now() - datetime.datetime(1970,1,1)).total_seconds()
        difference = seconds - float(time)

        addresses = list(local_ip4_addr_list())
        ip = [addr for addr in addresses if addr.startswith("10")][0]
        with open("seconds_{}.txt".format(ip), "a") as f:
            f.write(str(difference) + "\n")
        
        return " ".join(values)

"<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>"
        
#########################################################
#
#            F L O O D   P R O X Y
#
################################################################

class FloodProxy:
    def __init__(self):
        #print("initializing baby broker API")
        self.context = zmq.Context ()   # returns a singleton object
        self.incoming_socket = self.context.socket(zmq.REP)
        #creating a server bound to port 5555
        self.incoming_socket.bind(SERVER_ENDPOINT.format(address="*", port=FLOOD_PROXY_PORT))
        self.registry = {}
        self.registry["PUB"] = defaultdict(list)
        self.registry["SUB"] = defaultdict(list)

    #Application interface --> run() encloses basic functionality
    def run(self):
        while True:
            #print("Listening...")
            self.listen()

    def listen(self):
        #  Wait for next request from client
        self.message = self.incoming_socket.recv_string()
        print(self.message)
        role, topic, ipaddr = self.message.split()
        print("Received request: Role -> {role}\t\tTopic -> {topic}\t\tData -> {data}".format(role=role, topic=topic, data=ipaddr))
        if ipaddr not in self.registry[role][topic]:
            self.registry[role][topic].append(ipaddr)

        #based on our role, we need to find the companion ip addresses in the registry
        if role == "PUB":
            other = "SUB"
        if role == "SUB":
            other = "PUB"

        #if we have entries in the registry for the companion ip addresses
        if self.registry[other] != []:
            #registry[other][topic] is a list of ip addresses
            #these belong to the companion to the registering entity
            result = " ".join(self.registry[other][topic])

        #we'll have to check for nones in sub and pub
        else:
            result = "none"

        self.incoming_socket.send_string(result)

############################################################################################
#
#
#            F L O O D   P U B L I S H E R
#
#
##########################################################################################

class FloodPublisher:

    def __init__(self, topic):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.connect_str = SERVER_ENDPOINT.format(address=FLOOD_PROXY_ADDRESS, port=FLOOD_PROXY_PORT)
        self.socket.connect(self.connect_str)
        addresses = list(local_ip4_addr_list()) 
        self.ipaddress = [ip for ip in addresses if ip.startswith("10.")][0]
        #print(self.ipaddress)
        self.role = "PUB"
        self.topic = topic
        self.registry = []
        self.message = ""
        

    def register_pub(self):
        #print("Registering publisher")
        self.hello_message = "{role} {topic} {ipaddr}".format(role=self.role, topic=self.topic, ipaddr=self.ipaddress)
        self.socket.send_string(self.hello_message)
        self.reply = self.socket.recv_string()
        #self.reply = self.publish_lazy(self.hello_message)
        if self.reply != "none":
            self.registry = self.reply.split()
            print("Received registry.")
            
        
    def publish(self, data):
        for ipaddr in self.registry:
            seconds = (datetime.datetime.now() - datetime.datetime(1970,1,1)).total_seconds()
            self.socket = self.context.socket(zmq.REQ)
            self.connect_str = "tcp://{}".format(ipaddr)
            self.socket.connect(self.connect_str)
            self.message = "{time} {data}".format(time=seconds, data=data)
            self.socket.send_string(self.message)
            reply = self.socket.recv_string()
            
                
###################################################################################################################
#
#
#            F L O O D    S U B S C R I B E R
#
#
####################################################################################################################
            
class FloodSubscriber:
    def __init__(self, topic):
        self.context = zmq.Context ()   # returns a singleton object
        self.socket = self.context.socket (zmq.REP)
        self.socket.bind (SERVER_ENDPOINT.format(address="*", port=FLOOD_SUBSCRIBER_PORT))
        self.topic = topic
        print("Baby Subscriber API initialized. Listening on {}".format(FLOOD_SUBSCRIBER_PORT))
        self.register_sub()
        

    def register_sub(self):
        #print("Registering Baby Subscriber API")
        self.hello_socket = self.context.socket(zmq.REQ)
        self.connect_str = SERVER_ENDPOINT.format(address=FLOOD_PROXY_ADDRESS, port=FLOOD_PROXY_PORT)
        self.hello_socket.connect(self.connect_str)
        addresses = list(local_ip4_addr_list())
        self.ipaddress = [ip for ip in addresses if ip.startswith("10")][0]
        self.ipaddress += ":{}".format(FLOOD_SUBSCRIBER_PORT)
        self.role = "SUB"
        self.hello_message = "{role} {topic} {ipaddr}".format(role=self.role, topic=self.topic, ipaddr=self.ipaddress)
        print(self.hello_message)
        self.hello_socket.send_string(self.hello_message)
        self.reply = self.hello_socket.recv_string()
            
    def notify(self):
        #print("Baby Subscriber API listening.")
        #  Wait for next request from client
        self.message = self.socket.recv_string()
        seconds = (datetime.datetime.now() - datetime.datetime(1970,1,1)).total_seconds()
        time, *values = self.message.split()
        difference = seconds - float(time)
        with open("seconds_{}.txt".format(self.ipaddress), "a") as f:
            f.write(str(difference) + "\n")
        print("Subscriber received data {data}".format(data=" ".join(values)))
        self.socket.send_string(self.message)
        return " ".join(values)


