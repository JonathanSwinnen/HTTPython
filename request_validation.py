""" this file contains the functions used to validate HTTP Request and generate appropriate error codes/messages """

from HTTP_utils import *
from datetime import datetime
import os
import server_settings


# validates the head of the request (method, uri, http version, headers)
def validate_head(initial_line, headers):
    err = []  # list containing all validation errors

    # split initial line into command, uri, httpv
    command = initial_line.split(" ", 3)
    if len(command) != 3:  # must all be present
        err.append((400, "Invalid Request-Line"))
        return "", "", err, []

    # get method
    method = command[0]
    # get httpv
    http_v = command[2].split("/", 1)
    # get path
    uri = command[1]
    # parse uri
    parsed_uri = parse_uri(uri, server_settings.IP, server_settings.PORT)
    path = parsed_uri.path
    if path[0] != "/":  # add leading slash to path if not present
        path = "/" + path
    if path == "/":  # replace '/' path with home page
        path += server_settings.HOME_PAGE
    # set web root as path base
    path = server_settings.WEB_ROOT + path

    # validate individual headers:
    err_h, ignored = validate_headers(headers, method)
    err += err_h

    # respond to bad uri
    if parsed_uri.err == "bad scheme":
        if server_settings.STRICT_VALIDATION:  # other servers sometimes ignore the scheme and act like it's always http
            err.append((400, "Bad URI: scheme. Only http:// allowed"))

    # bad HTTP version format ( correct: HTTP/int.int )
    if http_v[0] != "HTTP" or len(http_v) != 2 or len(http_v[1].split(".")) != 2 \
            or any(not v.isdigit for v in http_v[1].split()):
        err.append((400, "Bad HTTP version format"))
    # bad HTTP version
    elif not http_v[1] == "1.1":
        err.append((505, "Unsupported HTTP version"))

    # respond 404 (except for put and post, which will create new file when file does not exist)
    if (method == "GET" or method == "HEAD") and not (os.path.isfile(path) or os.path.isdir(path)):
        err.append((404, "The resource was not found"))

    # respond to invalid method
    if not (method == "GET" or method == "HEAD" or method == "PUT" or method == "POST"):
        err.append((405, "The requested method is not supported on this server."))
    # safety, post and put only in allowed directories
    elif (method == "POST" or method == "PUT") and not \
            any([path.startswith(server_settings.WEB_ROOT + write_dir) for write_dir in server_settings.ALLOW_WRITE]):
        err.append((405, "PUT and POST requests are only allowed for resources under the following directories: "
                    + str(server_settings.ALLOW_WRITE)[1:][-2::-1][::-1]))   # <-- this is bad lol
    # post and put can only be used on files, not on folders
    elif (method == "POST" or method == "PUT") and (os.path.isdir(path) or path[-1] == "/"):
        err.append((405, "POST and PUT requests are not supported on directories"))

    # return
    return method, path, err, ignored


def validate_headers(headers, method):
    err = []
    ignored = []

    # respond to bad host header, cannot be ignored
    if not check_host(headers.get("host")):
        err.append((400, "Bad host header"))

    # content-length header
    if headers.get("content-length") is not None:
        if method == "GET" or method == "HEAD":
            if server_settings.STRICT_VALIDATION:  # only allow content-length on put and post
                err.append((400, "No content-length should be present for GET or HEAD requests"))
        if headers.get("transfer-encoding") is not None:  # content-length and transfer-encoding shouldn't both be present
            msg = "Both transfer-encoding and content-length present"
            if server_settings.STRICT_VALIDATION:
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
        if server_settings.STRICT_VALIDATION:
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


def check_host(host):
    parsed_host = parse_uri(host)
    if parsed_host.scheme != "":  # there isn't supposed to be a scheme in the hostname
        return False
    if parsed_host.path != "/" or host[-1] == "/":  # there isn't supposed to be a path in the hostname
        return False
    if parsed_host.port != server_settings.PORT:  # port has to match
        return False
    if parsed_host.host not in server_settings.ACCEPTED_HOSTNAMES:
        return False
    return True
