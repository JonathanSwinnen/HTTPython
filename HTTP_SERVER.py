# import socket programming library
import socket
import mimetypes
from urllib.parse import urlparse
import os
from email.utils import formatdate
from HTTP_Utils import read_head

# import thread module
from _thread import *
import threading

# thread function
def handle_connection(c):
    print("\n--- CONNECTION: STARTED THREAD ---")
    initial_line, headers, total = read_head(c)
    command = initial_line.split(" ")
    method = command[0]
    uri = command[1]
    httpv = command[2]
    print("got request: \n" + total)
    # if not full uri (form: http://server/path) --> convert so we can use urlparse

    if uri.startswith("/"):
        if uri == "/":
            uri = "/index.html"
        uri = "http://" + c.getsockname()[0] + uri
    parsed_uri = urlparse(uri)
    path = os.getcwd() + "/web" + parsed_uri.path

    if method == "GET" or method == "HEAD":
        response = "HTTP/1.1 "
        content = ""
        content_type = 'text/html'
        print("get path: " + path)
        if not os.path.isfile(path):
            print("not found!!")
            response += "404 Not Found"
            content = "Sorry! The requested file was not found on our server :(".encode()
        else:
            response += '200 OK'
            content_type = mimetypes.guess_type(uri)[0] or 'text/html'
            fin = open(path, "rb")
            content = fin.read()
            fin.close()

        response += "\r\nContent-Type: " + content_type
        response += "\r\nDate: " + formatdate(timeval=None, localtime=False, usegmt=True)
        response += "\r\n\r\n"

        c.send(response.encode())
        if method == "GET":
            c.sendall(content)

    elif method == "POST" or method == "PUT":
        cl = int(headers.get("content-length"))
        body = ""
        if cl is None:
            print("no content-length given!")
            pass  # bad request
        else:
            while len(body) < cl:
                body += c.recv(cl-len(body)).decode()
                print("reading body: " + body)
            if not len(body) == cl:
                print("body size does not equal content-length!")
                pass  # bad request

        print("writing to: " + parsed_uri.path)
        if method == "POST":
            with open(path, "a") as f:
                f.write(body+"\n")
        else:
            with open(path, "w+") as f:
                f.write(body)
        print("done writing")
    c.close()
    print("--- CONNECTION CLOSED ---")




def getmyip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def Main():
    host = getmyip()
    port = 8000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    print("socket binded @ " + host + ":"+str(port))
    # put the socket into listening mode
    s.listen()
    print("socket is listening")

    # a forever loop until client wants to exit
    try:
        while True:
            # establish connection with client
            c, a = s.accept()
            print('Connected to :', a[0], ':', a[1])
            # Start a new thread and return its identifier
            #start_new_thread(handle_connection, (c,))
            handle_connection(c)
        s.close()
    except KeyboardInterrupt:
        pass



if __name__ == '__main__':
    Main()


