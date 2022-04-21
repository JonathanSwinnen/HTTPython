"""This file contains global constants and settings variables"""

# Constants:
DATE_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"


# initializes default global settings
def init():
    # Server settings:
    global PORT
    # default port 8000  (usually 80 for HTTP, but you need admin privileges which is not very convenient)
    PORT = 8000

    global IP
    # default to localhost
    IP = "127.0.0.1"

    global TIMEOUT
    # client connection timeout is 30 seconds
    TIMEOUT = 30

    global WEB_ROOT
    # website root directory is web/
    WEB_ROOT = "web"

    global HOME_PAGE
    # website homepage is web/index.html
    HOME_PAGE = "index.html"

    global ALLOW_WRITE
    # post and put requests are allowed in web/data/ and web/errors/error_data/
    ALLOW_WRITE = ("/data/", "/errors/error_data/")

    global ACCEPTED_HOSTNAMES
    # allowed hostnames for the Host: header. default to localhost
    ACCEPTED_HOSTNAMES = ["127.0.0.1", "localhost"]

    # Debug options
    global LOG_BODY
    # log response bodies
    LOG_BODY = True

    global THREADING
    # option to turn of threading
    THREADING = True


