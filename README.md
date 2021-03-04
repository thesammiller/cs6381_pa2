# CS 6381 Distributed Systems Programming Assignment #2

Application and middleware for ZooKeeper and 0MQ

```
git clone https://github.com/thesammiller/cs6381_pa2.git  
```    

Required pacakges:
```
sudo apt-get install python3-zmq
sudo apt-get install python3-kazoo
```



Follow the prompts to enter a zipcode and number of iterations.    

```
sudo mn --topo single,7
mininet> h1 ./startzoo.sh       
mininet> h2 ./brokerproxy.py &    
mininet> h3 ./floodproxy.py &    
mininet> h4 ./subscriber.py 12345 BROKER &     
mininet> h5 ./publisher.py 12345 BROKER &     
mininet> h6 ./subscriber.py 54321 FLOOD &    
mininet> h7 ./publisher.py 54321 FLOOD &    
``` 
check `ps` on any host to see terminal output






