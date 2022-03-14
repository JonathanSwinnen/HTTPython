# import socket programming library
import socket

# import thread module
from _thread import *
import threading

# thread function
def threaded(c):
    # loop
    data = ""
    while True:
        # receive data
        data += c.recv(1024).decode()  # if no more data available
        if not data:
            break
        print(data);
    # connection closed
    c.close()

def Main():
    host = "127.0.0.1"
    port = 80
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    print("socket binded to port", port)
    # put the socket into listening mode
    s.listen()
    print("socket is listening")

    # a forever loop until client wants to exit
    while True:
        # establish connection with client
        c, a = s.accept()
        print('Connected to :', a[0], ':', a[1])
        # Start a new thread and return its identifier
        start_new_thread(threaded, (c,))
    s.close()


if __name__ == '__main__':
    Main()
