import io
import numpy as np
import socket
import time

HOST = "192.168.4.1"  # The server's hostname or IP address
PORT = 100
 
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print("connecting to ESP32-S3-Eye")
    #give a two second heads up for capturing the next image
    time.sleep(2)
    
    s.sendall(b'{"N":3,"D1":3,"D2":200}')
    print("message sent")
    s.sendall(b"{Heartbeat}") 
    time.sleep(2)
   
    s.sendall(b'{"N":3,"D1":2,"D2":95}')
    print("movement 2")
    s.sendall(b"{Heartbeat}") 
    time.sleep(1)

    s.sendall(b'{"N":3,"D1":3,"D2":200}')
    print("message sent")
    s.sendall(b"{Heartbeat}") 
    time.sleep(2)    

    s.sendall(b'{"N":100}')