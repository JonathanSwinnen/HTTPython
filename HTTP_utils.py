import socket


def read_head(c):
    """
    This function reads data from a socket and interprets it as an HTTP request + headers.
    After a double CRLF it stops reading. To continue reading the body, use the function read_body

    :param c: (socket) the socket to read from
    :return: a tuple containing the initial request line, a dictionary with the headers, the total head as a string, and an error message.
    """
    error = "ok"
    req = ""
    initial_line = ""
    total = ""
    headers = dict()
    reading_head = True
    while reading_head:
        # receive
        try:
            data_chunk = c.recv(1)
        except socket.timeout:
            error = "timeout"
            break
        except ConnectionResetError:
            error = "connection reset"
            break
        req += data_chunk.decode()
        # print(req)
        total += data_chunk.decode()
        recv_lines = req.split("\r\n")
        # parse received lines
        i = 0
        for line in recv_lines:
            i += 1
            if i == len(recv_lines):  # last line
                if line == "":  # completed line at the end
                    req = ""
                else:  # incomplete line at the end
                    req = line  # continue receiving last request line
            elif initial_line == "":  # expecting Request-Line (method, uri, http version)
                initial_line = line
            else:  # expecting headers or newline to end
                if line != "":
                    header_line = line.split(":", 1)
                    headers[header_line[0].lower()] = header_line[1].strip()
                else:  # CRLF after headers --> end request or body
                    reading_head = False
    return initial_line, headers, total, error


def determine_chunk_size(c):
    req = ""
    reading_chunk_size = True
    while reading_chunk_size:
        # receive
        try:
            data_chunk = c.recv(1)
        except c.error as e:
            # Something happened ?
            print(e)
            break
        req += data_chunk.decode()
        # print(bytes(req, "utf-8"))
        if req[-2:] == "\r\n":
            chunk_size = req[:-2]
            if not chunk_size == "":
                reading_chunk_size = False
    return int(chunk_size, 16)


def read_body(c, headers):
    """
    This function reads data from a socket and interprets it as the body of a http request.

    :param c: (socket) the socket to read from
    :param headers: (dict) the request headers
    :return: a tuple containing a string representing the decoded body, and an error message
        (at this time, only string bodies are implemented)
    """
    content_length = int(headers.get("content-length", 0))
    chunked = headers.get("transfer-encoding") == "chunked"

    body = b""
    err = "ok"
    if chunked:
        receiving_response = True
        while receiving_response:
            chunk_size = determine_chunk_size(c)
            if chunk_size != 0:
                chunk_data = b""
                # print("chunk size: ", chunk_size)
                remaining_data_size = chunk_size
                while remaining_data_size > 0:
                    data = c.recv(remaining_data_size)
                    chunk_data += data
                    remaining_data_size = chunk_size - len(chunk_data)
                    # print(data)
                    # print("received data size: ", len(data))
                    # print("====================")
                    # print("remaining data size: ", remaining_data_size)
                body += chunk_data
                # print("++++++++++++++++++++++++++++++++")
            else:
                receiving_response = False
    else:
        # receive body
        while len(body) < content_length:
            try:
                body += c.recv(content_length-len(body))
            except socket.timeout:
                err = "timeout"
                break
            except ConnectionResetError:
                err = "connection reset"
    return body.decode(encoding="ISO-8859-1"), err


def parse_uri(uri, host=None, port=80):
    """
    This function parses a given uri
    :param uri: (string) the uri that should be parsed
    :param host: (string) optional. if the hostname is known, specify it to improve accuracy.
        If not provided, the parser will guess.
    :param port: (int) optional. default=80. if the hostname is specified, but the port is not 80, change it
    :return: an object with the following properties:
        obj.scheme (string)
        obj.host (string)
        obj.port (int)
        obj.path (string)
        obj.query (string)
        obj.err (string, error message)
    """
    split_scheme = uri.split("://", 1)
    stripped_uri = ""
    ret = type('', (object,),
               {"scheme": "", "host": host, "port": port, "path": "", "query": "", "err": "ok"})()
    if uri == "":
        ret.path = "/"
    elif uri[0] == "/":  # absolute path form:  /path?query
        stripped_uri = uri[1:]
    else:  # absolute uri form?:  http://host/path?query
        if len(split_scheme) > 1:  # uri starts with scheme://
            ret.scheme = split_scheme[0]
            if ret.scheme != "http":
                ret.err = "bad scheme"
                return ret
        no_scheme = split_scheme[-1]  # host/path?query
        split_domain = no_scheme.split("/", 1)
        if host is not None and \
                (split_domain[0] == host+":"+str(port) or (split_domain[0] == host and port == 80)):
            # first entry is the correct domain
            stripped_uri = (split_domain[1]) if 1 < len(split_domain) else ""
        elif host is None:  # assume first entry is the domain
            host_port = split_domain[0].split(":")
            ret.host = host_port[0]
            if len(host_port) == 2:
                ret.port = int(host_port[1])
            else:
                ret.port = 80
            stripped_uri = (split_domain[1]) if 1 < len(split_domain) else ""
        else:
            # interpret as absolute file path but without leading /
            stripped_uri = no_scheme
    split_query = stripped_uri.split("?", 1)
    ret.path = "/" + split_query[0]
    if len(split_query) == 2:
        ret.query = split_query[1]
    return ret

# gets server ip
def getmyip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ip = ""
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except OSError as e:
        if e.args[0] == 51:  # if not connected to network, use localhost
            ip = "127.0.0.1"
        else:
            raise e
    s.close()
    return ip

def status_msg(code):
    if code == 200: return "OK"
    if code == 201: return "Created"
    if code == 304: return "Not Modified"
    if code == 400: return "Bad Request"
    if code == 404: return "Not Found"
    if code == 405: return "Method Not Allowed"
    if code == 411: return "Length Required"
    if code == 500: return "Internal Server Error"
    if code == 501: return "Not Implemented"
    if code == 505: return "Version Not Supported"
    return "ERROR CODE NOT RECOGNIZED"
