# import socket programming library
import mimetypes
import os
from datetime import datetime
from HTTP_utils import *
import traceback
from datetime import timezone
from _thread import *
from request_validation import validate_head
import server_settings
import sys


# server entry point
def main(args):
    print("\nStarting server... args: "+str(args))
    try:  # load settings
        init_settings(args)
    except Exception as e:
        print("Failed startup: Invalid args: " + str(e) + "\n")
        return

    # start TCP socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # When the server is shut down, the address can be reused.
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:  # try to bind
        s.bind((server_settings.IP, server_settings.PORT))
    except PermissionError:
        print("Failed startup: Permission denied. Admin privileges are required to use this port\n")
        return
    except OSError as e:
        if e.args[0] == 48:  # errno 48 = address already in use
            print("Failed startup: Address/port already in use\n")
            return
        else:  # something else happened ?
            raise e
    except Exception as e:
        raise e

    print("Socket bound @ " + server_settings.IP + ":"+str(server_settings.PORT))
    # put the socket into listening mode
    s.listen()
    print("Socket is listening.")

    # a forever loop until client wants to exit
    try:
        while True:
            # establish connection with client
            c, a = s.accept()
            # set client timeout setting for this connection
            c.settimeout(server_settings.TIMEOUT)
            print('\n-------\nAccepted incoming connection :', a[0], ':', a[1])
            # Start a new thread and return its identifier
            if server_settings.THREADING:  # handle connection via new thread
                start_new_thread(handle_connection, (c,))
            else:  # threading can be turned off for debugging purposes
                handle_connection(c)
    except KeyboardInterrupt:
        # stop server after keyboard interrupt (stop button in pycharm, CTRL+C in terminal, ...)
        print("\nClosing socket")
        s.close()
        print("Server stopped\n")


def init_settings(args):
    server_settings.init()
    # interpret command line arguments
    if "-p" in args:  # -p <port>
        server_settings.PORT = int(args[args.index("-p")+1])
    if "-t" in args:  # -t <timeout>
        server_settings.TIMEOUT = int(args[args.index("-t")+1])
    if "-h" in args:  # -h <homepage>
        server_settings.HOME_PAGE = args[args.index("-h")+1]
    if "-r" in args:  # -r <webroot>
        server_settings.WEB_ROOT = args[args.index("-r")+1]
    if "--log-body" in args:  # --log-body -> set true
        server_settings.LOG_BODY = True
    if "--no-threading" in args:  # --no-threading  -> set false
        server_settings.THREADING = False
    if "--strict" in args:  # --strict -> set true
        server_settings.STRICT_VALIDATION = True
    if "--localhost" not in args:  # --localhost -> force 127.0.0.1
        server_settings.IP = getmyip()
    if server_settings.IP == "127.0.0.1":
        print("running on localhost")
    else:
        server_settings.ACCEPTED_HOSTNAMES = [server_settings.IP]


# thread entry point
def handle_connection(c):
    print("--- CONNECTION: STARTED THREAD ---")

    # close connection flag
    close = False
    # persistent connection: keep looping until connection closes
    while not close:
        print("\n WAITING FOR NEW REQUEST")

        # empty method & headers
        method = ""
        headers = dict()
        try:
            # read head
            initial_line, headers, total, rh_err = read_head(c)
            if rh_err != "ok":  # problems reading head  (usually a timeout)
                print("\n-- read_head error: " + rh_err)
                break  # can't continue without head, break and close
            print("\n-- Got request head: \n" + total)

            # initialize response
            response = b""
            resp_str = ""

            # validate the received head and retrieve the method & path
            method, path, err, ignored = validate_head(initial_line, headers)

            if len(ignored) != 0:  # some errors can be ignored when server_settings.STRICT_VALIDATION = False
                print("ignored errors: " + str(ignored))
            if len(err) != 0:  # Errors have been detected
                response, resp_str, close = report_error(err, ignored, method != "HEAD")  # send error response
                if not close:  # read body if connection will not close, so it isn't mixed in with the next request
                    _, rb_err = read_body(c, headers)
                    if rb_err != "ok":  # timeout during read body?
                        print("\n-- read_body error: " + rh_err)
                        break  # end connection

            # respond to GET and HEAD requests
            elif method == "GET" or method == "HEAD":
                response, resp_str = retrieve(path, headers, method == "GET")
            # respond to POST and PUT requests
            elif method == "POST" or method == "PUT":
                body, rb_err = read_body(c, headers)
                if rb_err != "ok":  # timeout during read body?
                    print("\n-- read_body error: " + rh_err)
                    break  # end connection
                # store resource and generate response
                response, resp_str, close, err = store(path, headers, body, method == "PUT")

        # internal server error catch
        except Exception as e:
            print("\n-- Internal server error!!" + str(e.args) + " ending thread...")
            response, resp_str = generate_response(  # generate internal server error response page
                "500 Internal Server Error",
                "<h1>ERROR 500 - Internal Server Error</h1><p>An unexpected exception occurred: "
                + str(e) + "</p><h4>Traceback:</h4><p>"+traceback.format_exc()+"</p>",
                include_body=(method != "HEAD"),
                close=True
            )
            close = True
        try:
            c.sendall(response)  # send response
            print("\n-- Sent response:\n" + resp_str)
            close = close or (headers.get("connection") == "close")  # check for connection: close header
        # send failed due to disconnect or timeout: close connection
        except socket.timeout:  # timeout
            print("\n-- sendall: timeout, ending thread\n")
            close = True
        except BrokenPipeError:  # broken pipe
            print("\n-- sendall: broken pipe, ending thread\n")
            close = True
    c.close()
    print("\n--- CONNECTION CLOSED ---")


# retrieves data / handles HEAD and GET requests
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
        content = generate_dirpage(path)
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
def store(path, headers, body, overwrite):
    err = "ok"
    directory = os.path.dirname(path)
    if not os.path.exists(directory) or os.path.isfile(directory):
        os.makedirs(directory)

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
        if server_settings.LOG_BODY:  # for logging purposes
            resp_str += body_str
        else:
            resp_str += "<<response body: (" + str(len(body)) + " bytes)>>\n"

    return response, resp_str


# generates a directory index html page
def generate_dirpage(path):
    if path[-1] != "/":
        path += "/"
    web_path = path[len(server_settings.WEB_ROOT):]
    content = "<h1>Contents of: " + web_path + "</h1><ul>"
    for entry in os.listdir(path):
        content += "<li><a href='" + web_path + entry + "'>" + entry
        if os.path.isdir(path + entry):
            content += "/"
        content += "</a></li>"
    content += "</ul>"
    return content


# startup server with command line args
if __name__ == '__main__':
    main(sys.argv)


