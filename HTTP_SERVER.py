# import socket programming library
import socket

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
    headers = dict()
    while True:

        print("-- READ LOOP: NEW CHUNK")
        # receive
        data_chunk = c.recv(1)
        req += data_chunk.decode()
        print("carry + chunk received ::\n" + req)
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
                    print("END")

        print(method)
        print(uri)
        print(httpv)
        print(headers)
        if not data_chunk:
            break

    http_response = "hya"
    c.sendall(http_response)
    c.close()
    print("ended connection")

def Main():
    host = "127.0.0.1"
    port = 8000
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    print("socket binded to port", port)
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
            #start_new_thread(threaded, (c,))
            threaded(c)
        s.close()
    except KeyboardInterrupt:
        pass



if __name__ == '__main__':
    Main()
