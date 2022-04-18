from HTTP_Utils import *
from datetime import datetime
import os

from Settings import *


def validate_head(initial_line, headers):
    err = []

    command = initial_line.split(" ", 3)
    if len(command) != 3:
        err.append((400, "Invalid Request-Line"))
        return "", "", err, []

    # get method
    method = command[0]
    # get httpv
    http_v = command[2].split("/", 1)
    # get path
    uri = command[1]
    parsed_uri = parse_uri(uri, getmyip(), PORT)
    path = parsed_uri.path
    if path[0] != "/":
        path = "/" + path
    if path == "/":
        path += HOME_PAGE
    path = WEB_ROOT + path
    # validate individual headers:
    err_h, ignored = validate_headers(headers, method)
    err += err_h

    # respond to bad uri
    if parsed_uri.err == "bad scheme":
        if STRICT_VALIDATION:  # We have seen other servers ignore the scheme and act like it's always http
            err.append((400, "Bad URI: scheme. Only http:// allowed"))
            close = True

    # bad HTTP version format ( correct: HTTP/int.int )
    if http_v[0] != "HTTP" or len(http_v) != 2 or len(http_v[1].split(".")) != 2 \
            or any(not v.isdigit for v in http_v[1].split()):
        err.append((400, "Bad HTTP version format"))
        close = True
    # bad HTTP version
    elif not http_v[1] == "1.1":
        err.append((505, "Unsupported HTTP version"))
        close = True

    # respond 404 (except for put and post, which will create new files when file does not exist)
    if (method == "GET" or method == "HEAD") and not os.path.isfile(path):
        err.append((404, "The resource was not found"))

    # respond to invalid method
    if not (method == "GET" or method == "HEAD" or method == "PUT" or method == "POST"):
        err.append((405, "The requested method is not supported on this server."))
    elif (method == "POST" or method == "PUT") and not path.startswith("web/data"):
        err.append((405, "PUT and POST requests are only supported for resources under /data/"))

    return method, path, err, ignored


def validate_headers(headers, method):
    err = []
    ignored = []

    # respond to bad host header, cannot be ignored
    if not (headers.get("host") == getmyip() + ":" + str(PORT)
            or (PORT == 80 and headers.get("host") == getmyip())):
        err.append((400, "Bad host header"))

    # content-length header
    if headers.get("content-length") is not None:
        if method == "GET" or method == "HEAD":
            if STRICT_VALIDATION:
                err.append((400, "No content-length should be present for GET or HEAD requests"))
        if headers.get("transfer-encoding") is not None:
            msg = "Both transfer-encoding and content-length present"
            if STRICT_VALIDATION:
                err.append((400, msg))
            else:
                ignored.append(msg)
                del headers["content-length"]  # override
        elif not headers.get("content-length").isdigit() or int(headers.get("content-length")) < 0:
            err.append((400, "invalid content-length"))
    else:
        # transfer-encoding
        if headers.get("transfer-encoding") is not None:
            if headers.get("transfer-encoding") != "chunked":
                err.append((501, "Only chunked transfer encoding supported"))
        elif method == "POST" or method == "PUT":
            err.append((411, "No content-length or chunked encoding specified"))

    # if-modified-since date format
    if headers.get("if-modified-since") is not None and not check_date_format(headers.get("if-modified-since")):
        if STRICT_VALIDATION:
            err.append((400, "If-Modified-Since: bad date format"))
        else:
            ignored.append = "If-Modified-Since: bad date format"
            del headers["if-modified-since"]

    return err, ignored


def check_date_format(date):
    try:
        datetime.strptime(date, "%a, %d %b %Y %H:%M:%S GMT")
    except ValueError:  # bad date format
        return False
    return True
