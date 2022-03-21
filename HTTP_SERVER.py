# import socket programming library
import socket
import mimetypes
from urllib.parse import urlparse
import os
from email.utils import formatdate


# import thread module
from _thread import *
import threading

# thread function
def handle_connection(c):
    print("\n--- CONNECTION: STARTED THREAD ---")
    method, uri, httpv, headers, total = read_head(c)
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
                body += c.recv(cl).decode()
                print("reading body: " + body)
            if not len(body) == cl:
                print("body size does not equal content-length!")
                pass  # bad request

        print("writing to: " + parsed_uri.path)
        if method == "POST":
            with open(path, "a") as f:
                f.write(body)
        else:
            with open(path, "w+") as f:
                f.write(body)
        print("done writing")
    c.close()
    print("--- CONNECTION CLOSED ---")

def read_head(c):
    req = ""
    method = ""
    uri = ""
    httpv = ""
    total = ""
    headers = dict()
    reading_head = True
    while reading_head:
        # receive
        try:
            data_chunk = c.recv(1)
        except c.timeout as e:
            err = e.args[0]
            # this next if/else is a bit redundant, but illustrates how the
            # timeout exception is setup
            if err == 'timed out':
                print('TIMEOUT')
                break
            else:
                print(e)
                break
        except c.error as e:
            # Something else happened, handle error, exit, etc.
            print(e)
            break
        req += data_chunk.decode()
        total += data_chunk.decode()
        recv_lines = req.split("\r\n")
        # parse received lines
        i = 0
        for line in recv_lines:
            i += 1
            if i == len(recv_lines):  # last line
                if line == "":  # completed line at the end
                    req = ""
                else:  # incomplete line at the end
                    req = line  # continue receiving last request line
            elif method == "":  # expecting Request-Line (method, uri, http version)
                req_line = line.split(" ")
                method = req_line[0]
                uri = req_line[1]
                httpv = req_line[2]
                print("\nread request-line: " + line + "   , expecting headers ...")
            else:  # expecting headers or newline to end
                if line != "":
                    print("\nreading header: " + line)
                    header_line = line.split(":", 1)
                    print(header_line)
                    headers[header_line[0].lower()] = header_line[1].strip()
                else:  # CRLF after headers --> end request or body
                    print("END HEADERS\n")
                    reading_head = False
    return method, uri, httpv, headers, total



def respond(c, method, uri, httpv, headers, body):

    print("responding with header")



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
    s.settimeout(2)
    print("socket binded @ " + host + ":"+str(port))
    # put the socket into listening mode
    s.listen()
    print("socket is listening")

    # a forever loop until client wants to exit
    try:
        while True:
            # establish connection with client
            try:
                c, a = s.accept()
            except socket.timeout as e:
                continue
            print('Connected to :', a[0], ':', a[1])
            # Start a new thread and return its identifier
            #start_new_thread(handle_connection, (c,))
            handle_connection(c)
        s.close()
    except KeyboardInterrupt:
        pass



if __name__ == '__main__':
    Main()


