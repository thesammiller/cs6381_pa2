#!/usr/bin/python3

import sys
import time
import zmq
from random import randrange
from messageAPI import BrokerPublisher, FloodPublisher

system = {"BROKER": BrokerPublisher,
           "FLOOD" : FloodPublisher}

class WeatherPublisher:

    def __init__(self, topic, broker):
        self.topic = topic
        self.pub = system[broker](self.topic)
        self.pub.register_pub()
        
    def generateWeather(self):
        temperature = randrange(-80, 135)
        relhumidity = randrange(10, 60)
        return "{} {}".format(temperature, relhumidity)
        
    def weatherPublish(self):
        data = self.generateWeather()
        self.pub.publish("{data}".format(data=data))
        print ("Application sending: {topic} {data}".format(topic=self.topic, data=data))


def main():

    topic = sys.argv[1] if len(sys.argv) > 1 else "90210"
    api = sys.argv[2] if len(sys.argv) > 2 else "BROKER"
    
    if api not in system.keys():
        print("Usage error -- message api can either be FLOOD or BROKER")
        sys.exit(-1)

    if not topic.isdigit() or len(topic) != 5:
        print("Usage error -- topic must be 5 digit zipcode.")
        sys.exit(-1)
        
    wp = WeatherPublisher(topic, api)
    while True:
        wp.weatherPublish()
        time.sleep(1)

if __name__ == "__main__":
    main()
