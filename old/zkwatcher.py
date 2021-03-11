from kazoo.client import KazooClient
import codecs

ZOOKEEPER_ADDRESS = "10.0.0.1"
ZOOKEEPER_PORT = "2181"
ZOOKEEPER_LOCATION = '{zookeeper_ip}:{zookeeper_port}'.format(zookeeper_ip=ZOOKEEPER_ADDRESS,
        zookeeper_port=ZOOKEEPER_PORT)



def my_func(event):
    backups = zk.get("/broker/broker/backup")
    print(backups)


print("Starting...")
zk = KazooClient(hosts=ZOOKEEPER_LOCATION)
zk.start()
print("Checking if zookeeper path exists")
while True:
    # Test is going to be a ZNodeState object whenever /broker/broker/master exists
    # If /broker/broker/master doesn't exist it will be none
    # So when a master dies, the ephemeral master disappears
    # test will be none
    test = zk.exists("/broker/broker/master", watch=my_func)
    #print(test)
    if test == None:
        print("Master has died")
        # We get back a Tuple of information with "Get"
        # ( b"IP ADDRESS BYTE STRING", ZNodeStat(OBJECT) )
        # We're going to just take the byte string with the 0 index
        # TODO: This will fail with multiple IP addresses
        backup_data = zk.get("/broker/broker/backup")
        backup_string = backup_data[0]
        # If this is "10.0.0.5 10.0.0.6"
        backup_decoded = codecs.decode(backup_string, "utf-8")
        # [ "10.0.0.5", "10.0.0.6" ]
        backup_split = backup_decoded.split()
        backup_first = backup_split[0]
        # recreate the master node
        zk.create("/broker/broker/master", ephemeral=True)
        # set 
        print("Setting IP address to {}".format(backup_first))
        zk.set("/broker/broker/master", codecs.encode(backup_first, "utf-8"))
