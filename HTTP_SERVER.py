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
    while True:  # persistent connection: keep looping
        method = ""
        headers = dict()
        close = False
        try:
            initial_line, headers, total, err = read_head(c)
            if err != "ok":
                print("-- read_head error: " + err)
                break
            command = initial_line.split(" ")
            method = command[0]
            uri = command[1]
            httpv = command[2]
            response = b""
            resp_str = ""
            print("\n-- Got request: \n" + total)
            parsed_uri = parse_uri(uri, getmyip(), PORT)
            path = parsed_uri.path
            if path[0] != "/":
                path = "/"+path
            if path == "/":
                path += HOME_PAGE
            path = WEB_ROOT + path
            if parsed_uri.err != "ok":
                response, resp_str, close = generate_response(
                    "400 Bad Request",
                    "<h1>ERROR 400 - BAD REQUEST</h1><p>Bad URI: +"+parsed_uri.err+"</p>",
                    close=True
                )

            elif not(headers.get("host") == getmyip()+":"+str(PORT)
                     or (PORT == 80 and headers.get("host") == getmyip())):
                response, resp_str, close = generate_response(
                    "400 Bad Request",
                    "<h1>ERROR 400 - BAD REQUEST</h1><p>Incorrect or missing host header!</p>",
                    close=True
                )
            elif headers.get("crashtest"):  # custom header just to test throwing an internal server error
                crash(headers.get("crashtest"))
            elif method == "GET" or method == "HEAD":
                response, resp_str,  close = retrieve(path, headers, method == "GET")
            elif method == "POST" or method == "PUT":
                response, resp_str,  close = store(path, headers, c, method == "PUT")
            else:
                response, resp_str,  close = generate_response(
                    "400 Bad Request",
                    "<h1>ERROR 400 - BAD REQUEST</h1><p>The requested HTTP is invalid or not not implemented</p>",
                    close=True
                )
        except Exception as e:
            print("\n-- Internal server error!!" + str(e.args) + " ending thread...")
            response, resp_str,  close = generate_response(
                "500 Internal Server Error",
                "<h1>ERROR 500 - Internal Server Error</h1><p>An unexpected exception occurred: "
                + str(e) + "</p><h4>Traceback:</h4><p>"+traceback.format_exc()+"</p>",
                include_body=(method != "HEAD"),
                close=True
            )
        try:
            c.sendall(response)
            print("\n-- Sent response:\n" + resp_str)
            if close or headers.get("connection") == "close":
                break
        except socket.timeout:
            print("\n-- sendall: timeout, ending thread\n")
        except BrokenPipeError:
            print("\n-- sendall: broken pipe, ending thread\n")
            break
    c.close()
    print("\n--- CONNECTION CLOSED ---")


def retrieve(path, headers, include_body):
    if not os.path.isfile(path):
        print("not found!")
        return generate_response(
            "404 Not Found",
            "<h1>ERROR 404 - NOT FOUND</h1><p>Sorry, this file does not exist on our server :(</p>",
            include_body=include_body
        )
    add_headers = dict()
    add_headers["Content-Type"] = mimetypes.guess_type(path)[0] or 'text/html'
    lm = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc).strftime(DATE_FORMAT)
    add_headers["Last-Modified"] = lm

    fin = open(path, "rb")
    content = fin.read()
    fin.close()

    ims = headers.get("if-modified-since")
    if ims is not None:
        try:
            ims_dat = datetime.strptime(ims, DATE_FORMAT)
        except ValueError:
            return generate_response(
                "400 Bad Request",
                "<h1>ERROR 400 - BAD REQUEST</h1><p>If-Modified-Since field bad format!</p>",
                include_body=include_body,
                close=True
            )
        if ims_dat >= datetime.strptime(lm, DATE_FORMAT):
            return generate_response(
                "304 Not Modified",
                content,
                add_headers,
                include_body=False
            )
    return generate_response("200 OK", content, add_headers, include_body)


def store(path, headers, c, overwrite):
    cl = int(headers.get("content-length"))
    chunked = False
    if cl is None and not chunked:
        print("no content-length or chunked given!")
        return generate_response(
            "400 Bad Request",
            "<h1>ERROR 400 - BAD REQUEST</h1><p>No Content-Length field or chunked encoding was specified!</p>"
        )
    else:
        body, err = read_body(c, cl, chunked)
        print(err)
        if err == "bad content_length":
            return generate_response(
                "400 Bad Request",
                "<h1>ERROR 400 - BAD REQUEST</h1><p>Inconsistent Content-Length!</p>",
                close=True
            )
        else:
            if not path.startswith("web/data/"):
                return generate_response(
                    "403 Forbidden",
                    "<h1>ERROR 403 - FORBIDDEN</h1><p>Please only use PUT & POST commands to resources under /data/</p>",
                    close=True
                )
            if not overwrite:
                with open(path, "a") as f:
                    f.write(body + "\n")
            else:
                with open(path, "w+") as f:
                    f.write(body)
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
    resp_str = "HTTP/1.1 " + code

    resp_str += "\r\nDate: " + datetime.utcnow().strftime(DATE_FORMAT)
    body_str = str(body)
    if body is not None:
        resp_str += "\r\nContent-Length: " + str(len(body))
        if type(body) == str:
            body = body.encode()
            additional_headers["Content-Type"] = "text/html"
    if close:
        resp_str += "\r\nConnection: close"

    for header in additional_headers:
        resp_str += "\r\n" + header + ": " + additional_headers[header]

    resp_str += "\r\n\r\n"
    response = resp_str.encode()

    if include_body and body is not None:
        response += body
        if LOG_BODY:
            resp_str += body_str
        else:
            resp_str += "<<response body: (" + str(len(body)) + " bytes)>>\n";
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
    print("socket binded @ " + host + ":"+str(PORT))
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


