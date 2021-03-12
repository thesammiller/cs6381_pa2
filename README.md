# CS 6381 Distributed Systems Programming Assignment #2

Application and middleware for ZooKeeper and 0MQ

```
git clone https://github.com/thesammiller/cs6381_pa2.git  
```    

*Note: This assumes that Zookeeper is installed at /opt/zookeeper*

Required packages:    
```
sudo apt-get install mn python3-zmq python3-kazoo python3-pip openvswitch-testcontroller
pip3 install mininet
sudo ln /usr/bin/ovs-testcontroller /usr/bin/controller 
```

To run:    
```
sudo python3 ps_mininet.py
mininet> source commands.txt      
``` 
check `ps` on any host to see terminal output    
check `logs/*.log` for time differential         

Run the following to generate graphs:    
```
python3 graph_average.py
python3 graph_quantile.py
```




