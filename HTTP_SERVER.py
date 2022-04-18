# import socket programming library
import mimetypes
import os
from datetime import datetime
from HTTP_utils import *
import traceback
from datetime import timezone
from _thread import *
from request_validation import validate_head
from server_settings import *


# thread function
def handle_connection(c):
    print("--- CONNECTION: STARTED THREAD ---")

    # initialize close flag
    close = False
    # persistent connection: keep looping
    while True:
        print("\n WAITING FOR NEW REQUEST")

        # empty method & headers
        method = ""
        headers = dict()
        try:
            # read head
            initial_line, headers, total, rh_err = read_head(c)
            if rh_err != "ok":
                print("\n-- read_head error: " + rh_err)
                break
            print("\n-- Got request head: \n" + total)

            # initialize response
            response = b""
            resp_str = ""

            # validate the received head
            method, path, err, ignored = validate_head(initial_line, headers)
            if len(ignored) != 0:
                print("ignored errors: " + str(ignored))
            if len(err) != 0:
                response, resp_str, close = report_error(err, ignored, method != "HEAD")
            # respond to 500 internal server error test
            elif headers.get("crashtest"):  # custom header just to test throwing an internal server error
                crash(headers.get("crashtest"))
            # respond to GET and HEAD requests
            elif method == "GET" or method == "HEAD":
                response, resp_str = retrieve(path, headers, method == "GET")
            # respond to POST and PUT requests
            elif method == "POST" or method == "PUT":
                response, resp_str, close, err = store(path, headers, c, method == "PUT")
                if err == "timeout" or err == "connection reset":
                    break

        # internal server error catch
        except Exception as e:
            print("\n-- Internal server error!!" + str(e.args) + " ending thread...")
            response, resp_str = generate_response(
                "500 Internal Server Error",
                "<h1>ERROR 500 - Internal Server Error</h1><p>An unexpected exception occurred: "
                + str(e) + "</p><h4>Traceback:</h4><p>"+traceback.format_exc()+"</p>",
                include_body=(method != "HEAD"),
                close=True
            )
            close = True
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


# handles HEAD and GET requests
def retrieve(path, headers, include_body):
    # add required headers for GET and HEAD requests
    add_headers = dict()
    add_headers["Content-Type"] = mimetypes.guess_type(path)[0] or 'text/html'
    lm = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc).strftime(DATE_FORMAT)
    add_headers["Last-Modified"] = lm
    content = b""
    if os.path.isfile(path):
        # read file
        fin = open(path, "rb")
        content = fin.read()
        fin.close()
    else:  # path is directory, generate contents page
        if path[-1] != "/":
            path += "/"
        web_path = path[len(WEB_ROOT):]
        content = "<h1>Contents of: " + web_path + "</h1><ul>"
        for entry in os.listdir(path):
            content += "<li><a href='" + web_path + entry + "'>" + entry
            if os.path.isdir(path+entry):
                content += "/"
            content += "</a></li>"
        content += "</ul>"
    # check If-Modified-Since header and respond accordingly
    ims = headers.get("if-modified-since")
    if ims is not None:
        # not modified, respond 304
        if datetime.strptime(ims, DATE_FORMAT) >= datetime.strptime(lm, DATE_FORMAT):
            return generate_response(
                "304 Not Modified",
                content,
                add_headers,
                include_body=False
            )
    # everything normal, respond 200 OK
    return generate_response("200 OK", content, add_headers, include_body)


# handles PUT and POST requests
def store(path, headers, c, overwrite):
    cl = int(headers.get("content-length"))
    chunked = False
    # read body
    body, err = read_body(c, cl, chunked)
    print(err)
    # incorrect content length, bad request
    if err == "bad content_length":
        return generate_response(
            "400 Bad Request",
            "<h1>ERROR 400 - BAD REQUEST</h1><p>Inconsistent Content-Length!</p>",
            close=True
        ), + (True, err,)
    elif err == "timeout" or err == "connection reset":
        return b"", "", True, err
    else:
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
        ) + (False, err,)


def report_error(err, ignored, include_body):
    codes = [e[1] for e in err]
    close_codes = [400, 411, 500, 505]
    # automatically close connection on bad/unsupported requests and internal server errors
    close = len([c for c in codes if c in close_codes]) != 0
    sorted_err = sorted(err)
    highest_err = sorted(err)[-1]
    err_msg = "<h1>ERROR " + str(highest_err[0]) + " - " + status_msg(highest_err[0]).upper() + "</h1>" + \
              "<p>" + highest_err[1] + "</p>"
    if len(err) > 1:
        err_msg += "<h3>Other potential errors have been detected:</h3>"
        for e in sorted_err[-2::-1]:
            err_msg += "<h5>" + str(e[0]) + ": " + status_msg(e[0]).upper() + "</h5>" + \
                       "<p>" + e[1] + "</p>"
    if len(ignored) > 0:
        err_msg += "<h3>The following errors are ignored because strict validation is disabled:</h3><ul>"
        for e in ignored:
            err_msg += "<li>" + e + "</li>"
        err_msg += "</ul>"

    response, resp_str = generate_response(
        str(highest_err[0]) + " " + status_msg(highest_err[0]),
        err_msg,
        close=close,
        include_body=include_body
    )

    return response, resp_str, close


# 500 internal error test
def crash(test):
    print("-- Internal Server Error test: ")
    if test == "div-by-zero":
        a = 0 / 0
    elif test == "index-oob":
        a = [1, 2, 3]
        b = a[100]
    elif test == "custom":
        raise Exception("custom exception")


# generates response bytes
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

    return response, resp_str


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
            print('\n-------\nConnected to :', a[0], ':', a[1])
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


