"""This file contains global constants and settings variables"""

# Constants:
DATE_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"


# initializes default global settings
def init():
    # Server settings
    global PORT
    PORT = 8000

    global IP
    IP = "127.0.0.1"

    global TIMEOUT
    TIMEOUT = 30

    global HOME_PAGE
    HOME_PAGE = "index.html"

    global WEB_ROOT
    WEB_ROOT = "web"

    global ALLOW_WRITE
    ALLOW_WRITE = ("/data/", "/errors/error_data/")

    global STRICT_VALIDATION
    STRICT_VALIDATION = False

    global ACCEPTED_HOSTNAMES
    ACCEPTED_HOSTNAMES = ["127.0.0.1", "localhost"]

    # Debug options
    global LOG_BODY
    LOG_BODY = False

    global THREADING
    THREADING = False


