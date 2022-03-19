# import socket programming library
import socket
import mimetypes

# import thread module
from _thread import *
import threading

# thread function
def threaded(c):

    # loop & receive data
    print("started thread")
    req = ""
    method = ""
    uri = ""
    httpv = ""
    total = ""
    headers = dict()
    while True:

        print("-- READ LOOP: NEW CHUNK")
        # receive
        try:
            data_chunk = c.recv(1024)
        except c.timeout as e:
            err = e.args[0]
            # this next if/else is a bit redundant, but illustrates how the
            # timeout exception is setup
            if err == 'timed out':
                print('recv timed out, retry later')
                continue
            else:
                print(e)
                break
        except c.error as e:
            # Something else happened, handle error, exit, etc.
            print(e)
            break

        req += data_chunk.decode()
        total += data_chunk.decode()
        print("carry + chunk received ::\n\n" + req)
        print("\n::end received")
        recv_lines = req.split("\r\n")

        # parse received lines
        i = 0
        for line in recv_lines:
            i += 1
            if i == len(recv_lines):
                if line == "":  # completed line at the end
                    print("finished with complete line, ... clearing")
                    req = ""
                else:           # incomplete line at the end
                    print("incomplete line ... carrying over")
                    req = line # continue receiving last request line
            elif method == "":  # expecting Request-Line (method, uri, http version)
                req_line = line.split(" ")
                if req_line[0] == "GET":
                    method = "GET"
                    uri = req_line[1]
                    httpv = req_line[2]
                    print("read GET request: " + line + "   , expecting headers ...")
                else:
                    pass  # !!! only GET is implemented
            else:  # expecting headers or newline to end
                if line != "":
                    print("reading header: " + line)
                    header_line = line.split(":", 1)
                    print(header_line)
                    headers[header_line[0]] = header_line[1].strip()
                else:
                    print("END parsing")
                    print(total)
                    respond(c, method, uri, httpv, headers)
                    method = ""
                    uri = ""
                    headers = dict()
                    httpv = ""
                    req = ""
                    c.close()
                    return
        print(method)
        print(uri)
        print(httpv)
        print(headers)
    print("ended connection")


def respond(c, method, uri, httpv, headers):
    if method == "GET":
        print("responding to GET request")
        if uri == '/':
            uri = '/index.html'
        content_type = mimetypes.guess_type(uri)[0] or 'text/html'

        fin = open('webpage' + uri, "rb")
        content = fin.read()
        fin.close()
        response = ('HTTP/1.0 200 OK\nContent-Type: '+content_type+'\n\n').encode() + content
        c.sendall(response)

def Main():
    host = "127.0.0.1"
    port = 8000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.settimeout(2)
    print("socket binded to port", port)
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
            start_new_thread(threaded, (c,))
        s.close()
    except KeyboardInterrupt:
        pass



if __name__ == '__main__':
    Main()
