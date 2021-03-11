from kazoo.client import KazooClient
import codecs

ZOOKEEPER_ADDRESS = "10.0.0.1"
ZOOKEEPER_PORT = "2181"
ZOOKEEPER_LOCATION = '{zookeeper_ip}:{zookeeper_port}'.format(zookeeper_ip=ZOOKEEPER_ADDRESS,
                                                              zookeeper_port=ZOOKEEPER_PORT)

def my_func():
    #print("With leader elected, setting new master.")
    # Get the lowest sequential node, since they are the leader
    new_master = election.lock.contenders()[0]
    print("New master -> {}".format(new_master))
    #zk.set("/broker/broker/master", master_ip)

if __name__ == '__main__':
    print("Starting...")
    zk = KazooClient(hosts=ZOOKEEPER_LOCATION)
    zk.start()
    print("Checking if zookeeper path exists")
    #election = zk.Election('/broker/broker', 'test-election')
    try:
        zk.create("/broker/broker/master", ephemeral=True)
    except:
        print("Already a master broker...")

    while True:
        election = zk.Election('/broker/broker', 'test-election')
        #print("Running loop...")
        election.run(my_func)


