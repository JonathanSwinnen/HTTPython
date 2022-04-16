# import socket programming library
import mimetypes
import os
from datetime import datetime
from HTTP_Utils import *
import traceback
from datetime import timezone
from _thread import *

# Constants:
PORT = 8000
TIMEOUT = 120
DATE_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"
HOME_PAGE = "index.html"
WEB_ROOT = "web"

# Debug options
LOG_BODY = False
THREADING = True


# thread function
def handle_connection(c):
    print("\n--- CONNECTION: STARTED THREAD ---")

    # initialize close flag
    close = False

    while True:  # persistent connection: keep looping

        # empty method & headers
        method = ""
        headers = dict()

        try:
            # read head
            initial_line, headers, total, err = read_head(c)
            if err != "ok":
                print("-- read_head error: " + err)
                break
            print("\n-- Got request head: \n" + total)

            command = initial_line.split(" ")
            # get method
            method = command[0]
            # get path
            uri = command[1]
            parsed_uri = parse_uri(uri, getmyip(), PORT)
            path = parsed_uri.path
            if path[0] != "/":
                path = "/"+path
            if path == "/":
                path += HOME_PAGE
            path = WEB_ROOT + path

            # initialize response
            response = b""
            resp_str = ""

            # respond to bad uri
            if parsed_uri.err != "ok":
                response, resp_str, close = generate_response(
                    "400 Bad Request",
                    "<h1>ERROR 400 - BAD REQUEST</h1><p>Bad URI: +"+parsed_uri.err+"</p>",
                    close=True
                )

            # respond to bad host header
            elif not(headers.get("host") == getmyip()+":"+str(PORT)
                     or (PORT == 80 and headers.get("host") == getmyip())):
                response, resp_str, close = generate_response(
                    "400 Bad Request",
                    "<h1>ERROR 400 - BAD REQUEST</h1><p>Incorrect or missing host header!</p>",
                    close=True
                )

            # respond to 500 internal server error test
            elif headers.get("crashtest"):  # custom header just to test throwing an internal server error
                crash(headers.get("crashtest"))

            # respond to GET and HEAD requests
            elif method == "GET" or method == "HEAD":
                response, resp_str,  close = retrieve(path, headers, method == "GET")

            # respond to POST and PUT requests
            elif method == "POST" or method == "PUT":
                response, resp_str,  close = store(path, headers, c, method == "PUT")

            # respond to invalid method
            else:
                response, resp_str,  close = generate_response(
                    "400 Bad Request",
                    "<h1>ERROR 400 - BAD REQUEST</h1><p>The requested HTTP is invalid or not not implemented</p>",
                    close=True
                )
        # internal server error catch
        except Exception as e:
            print("\n-- Internal server error!!" + str(e.args) + " ending thread...")
            response, resp_str,  close = generate_response(
                "500 Internal Server Error",
                "<h1>ERROR 500 - Internal Server Error</h1><p>An unexpected exception occurred: "
                + str(e) + "</p><h4>Traceback:</h4><p>"+traceback.format_exc()+"</p>",
                include_body=(method != "HEAD"),
                close=True
            )

        # send response
        try:
            c.sendall(response)
            print("\n-- Sent response:\n" + resp_str)
            if close or headers.get("connection") == "close":
                break
        except socket.timeout:  # timeout
            print("\n-- sendall: timeout, ending thread\n")
        except BrokenPipeError:  # broken pipe
            print("\n-- sendall: broken pipe, ending thread\n")
            break
    c.close()
    print("\n--- CONNECTION CLOSED ---")


def retrieve(path, headers, include_body):
    # respond 404
    if not os.path.isfile(path):
        print("not found!")
        return generate_response(
            "404 Not Found",
            "<h1>ERROR 404 - NOT FOUND</h1><p>Sorry, this file does not exist on our server :(</p>",
            include_body=include_body
        )
    # add required headers for GET and HEAD requests
    add_headers = dict()
    add_headers["Content-Type"] = mimetypes.guess_type(path)[0] or 'text/html'
    lm = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc).strftime(DATE_FORMAT)
    add_headers["Last-Modified"] = lm
    # read file
    fin = open(path, "rb")
    content = fin.read()
    fin.close()

    # check If-Modified-Since header and respond accordingly
    ims = headers.get("if-modified-since")
    if ims is not None:
        try:
            ims_dat = datetime.strptime(ims, DATE_FORMAT)
        except ValueError:  # bad date format
            return generate_response(
                "400 Bad Request",
                "<h1>ERROR 400 - BAD REQUEST</h1><p>If-Modified-Since field bad format!</p>",
                include_body=include_body,
                close=True
            )
        # not modified, respond 304
        if ims_dat >= datetime.strptime(lm, DATE_FORMAT):
            return generate_response(
                "304 Not Modified",
                content,
                add_headers,
                include_body=False
            )
    # everything normal, respond 200 OK
    return generate_response("200 OK", content, add_headers, include_body)


def store(path, headers, c, overwrite):
    cl = int(headers.get("content-length"))
    chunked = False

    # no length & not chunked, bad request
    if cl is None and not chunked:
        print("no content-length or chunked given!")
        return generate_response(
            "400 Bad Request",
            "<h1>ERROR 400 - BAD REQUEST</h1><p>No Content-Length field or chunked encoding was specified!</p>"
        )
    else:
        # read body
        body, err = read_body(c, cl, chunked)
        print(err)
        # incorrect content length, bad request
        if err == "bad content_length":
            return generate_response(
                "400 Bad Request",
                "<h1>ERROR 400 - BAD REQUEST</h1><p>Inconsistent Content-Length!</p>",
                close=True
            )
        else:
            # for safety, writing outside data folder is forbidden
            if not path.startswith("web/data/"):
                return generate_response(
                    "403 Forbidden",
                    "<h1>ERROR 403 - FORBIDDEN</h1><p>Please only use PUT & POST commands to resources under /data/</p>",
                    close=True
                )
            if not overwrite:  # POST
                with open(path, "a") as f:
                    f.write(body + "\n")
            else:  # PUT
                with open(path, "w+") as f:
                    f.write(body)
            # respond
            return generate_response(
                "201 Created",
                "<h1>201 - Created</h1><p>Data submitted successfully!</p>"
            )


def crash(test):
    print("-- Internal Server Error test: ")
    if test == "div-by-zero":
        a = 0 / 0
    elif test == "index-oob":
        a = [1, 2, 3]
        b = a[100]
    elif test == "custom":
        raise Exception("custom exception")


def generate_response(code, body=None, additional_headers=dict(), include_body=True, close=False):
    # initial response line
    resp_str = "HTTP/1.1 " + code

    # date
    resp_str += "\r\nDate: " + datetime.utcnow().strftime(DATE_FORMAT)

    # body string (for logging purposes)
    body_str = str(body)

    if body is not None:
        # add content-length
        resp_str += "\r\nContent-Length: " + str(len(body))
        # turn string body into bytes
        if type(body) == str:
            body = body.encode()
            additional_headers["Content-Type"] = "text/html"

    # close connection
    if close:
        resp_str += "\r\nConnection: close"

    # additional parameter specified headers
    for header in additional_headers:
        resp_str += "\r\n" + header + ": " + additional_headers[header]

    # end double CRLF
    resp_str += "\r\n\r\n"

    # encode
    response = resp_str.encode()

    # include body in response (false for HEAD requests and 304 responses)
    if include_body and body is not None:
        response += body
        if LOG_BODY:  # for logging purposes
            resp_str += body_str
        else:
            resp_str += "<<response body: (" + str(len(body)) + " bytes)>>\n"

    return response, resp_str, close


def getmyip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def main():
    host = getmyip()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, PORT))
    print("socket bound @ " + host + ":"+str(PORT))
    # put the socket into listening mode
    s.listen()
    print("socket is listening")

    # a forever loop until client wants to exit
    try:
        while True:
            # establish connection with client
            c, a = s.accept()
            c.settimeout(TIMEOUT)
            print('Connected to :', a[0], ':', a[1])
            # Start a new thread and return its identifier
            if THREADING:
                start_new_thread(handle_connection, (c,))
            else:
                handle_connection(c)
        s.close()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()


