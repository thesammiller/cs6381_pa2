from messageAPI import BrokerProxy

#to be run on 10.0.0.1

def main():
    print("Starting Broker Proxy...")
    bp = BrokerProxy()
    print("Broker Proxy initialized.")
    bp.run()
    print("This should not be visible because Broker Proxy is running.")

if __name__ == '__main__':
    main()



        



       



