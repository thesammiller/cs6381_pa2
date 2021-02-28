# CS 6381 Distributed Systems Programming Assignment #2

Writing application and middleware for 0MQ.
```
git clone https://github.com/thesammiller/cs6381_pa2.git  
```    

Follow the prompts to enter a zipcode and number of iterations.    

```
sudo mn --topo single,6       
mininet> h1 python3 brokerproxy.py &    
mininet> h2 python3 floodproxy.py &    
mininet> h3 python3 subscriber.py 12345 BROKER &     
mininet> h4 python3 publisher.py 12345 BROKER &     
mininet> h5 python3 subscriber.py 54321 FLOOD &    
mininet> h6 python3 publisher.py 54321 FLOOD &    
``` 
check "ps" on any host to see terminal output






