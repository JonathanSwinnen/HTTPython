""" this file contains the functions used to validate HTTP Request and generate appropriate error codes/messages """

from HTTP_utils import *
from datetime import datetime
import os
import server_settings
import mimetypes

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
    err_h = validate_headers(headers, method)
    err += err_h

    # respond to bad uri
    if parsed_uri.err == "bad scheme":
        # uri has to start with http:// or be an absolute path
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
    elif (method == "POST" or method == "PUT") and not check_write_allowed(path, headers):
        err.append((405, "PUT and POST requests are only allowed for resources under the following directories: "
                    + str(server_settings.ALLOW_WRITE)))   # <-- this is bad lol

    return method, path, err


def validate_headers(headers, method):
    err = []

    # respond to bad host header
    if not check_host(headers.get("host")):
        err.append((400, "Bad host header"))

    # content-length header
    if headers.get("content-length") is not None:
        if method == "GET" or method == "HEAD":
            err.append((400, "No content-length or message body should be present for GET or HEAD requests"))
        # content-length and transfer-encoding shouldn't both be present, transfer-encoding overrides
        if headers.get("transfer-encoding") is not None:
            del headers["content-length"]  # override
        # content length not an integer or negative
        elif not headers.get("content-length").isdigit() or int(headers.get("content-length")) < 0:
            err.append((400, "invalid content-length"))
    else:
        # transfer-encoding
        if headers.get("transfer-encoding") is not None:
            if method == "GET" or method == "HEAD":
                err.append((400, "No transfer-encoding or message body should be present for GET or HEAD requests"))
            if headers.get("transfer-encoding") != "chunked":
                # only transfer-encoding: chunked supported, no other transfer-encodings
                err.append((501, "Only chunked transfer encoding supported"))
        # content-length or transfer-encoding necessary but not present
        elif method == "POST" or method == "PUT":
            err.append((411, "No content-length or chunked encoding specified"))

    # if-modified-since date format
    if headers.get("if-modified-since") is not None and not check_date_format(headers.get("if-modified-since")):
        del headers["if-modified-since"]

    return err


# validates the format of a date string
def check_date_format(date):
    try:
        datetime.strptime(date, "%a, %d %b %Y %H:%M:%S GMT")
    except ValueError:  # bad date format
        return False
    return True


# checks if the host header field is matching
def check_host(host):
    parsed_host = parse_uri(host)
    if parsed_host.scheme != "":  # there isn't supposed to be a scheme in the hostname
        return False
    if parsed_host.path != "/" or host[-1] == "/":  # there isn't supposed to be a path in the hostname
        return False
    if parsed_host.port != server_settings.PORT:  # port has to match
        return False
    if parsed_host.host not in server_settings.ACCEPTED_HOSTNAMES:  # not an accepted hostname
        return False
    # all checks passed
    return True


# returns true if path in an ALLOW_WRITE directory
def check_write_allowed(path, headers):
    # resource not in allowed directory
    return any([path.startswith(server_settings.WEB_ROOT + write_dir) for write_dir in server_settings.ALLOW_WRITE])