import socket
PORT = 80
ALLOWED_COMMANDS = ["HEAD", "GET", "PUT", "POST"]
test_command = "test"

def input_handler():
    user_input = input("HTTP request: ")
    http_command, URI = user_input.split(" ")[:2]
    if http_command not in ALLOWED_COMMANDS:
        print("Not an allowed command, allowed commands are: ", *ALLOWED_COMMANDS)
        return
    stripped_URI = URI.split("/", 3)
    #print(stripped_URI, len(stripped_URI))
    host = stripped_URI[2]
    path = "/"
    if len(stripped_URI) >= 4:
        path += stripped_URI[3]
    #print(http_command, URI)
    print(http_command, host, path)
    if (http_command == "HEAD"):
        return send_request(http_command, host, path)
    elif (http_command == "GET"):
        header = send_request("HEAD", host, path)
        is_chunked, content_length = extract_metadata(header)
        print(int(content_length))
        full_page_size = len(header) + int(content_length)
        print(full_page_size)
        dummy = send_request("GET", host, path, is_chunked, int(content_length))



def send_request(http_command, host, path, is_chunked=None, content_length=None):
    request = http_command + " " + path + " HTTP/1.1\r\nHost: " + host + "\r\n\r\n"
    print(request)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, PORT))
        s.send(bytes(request, 'UTF-8'))
        return response_handler(http_command, s, host, is_chunked, content_length)


def response_handler(http_command, s, host, is_chunked=None, content_length=None):
    if http_command == "HEAD":
        data = s.recv(1024)
        all_data = data
        while len(data) == 1024:
            data = s.recv(1024)
            all_data += data
    elif http_command == "GET":
        if is_chunked:
            pass
        else:
            all_data = s.recv(content_length)
        f = open(host + ".html", "w")
        f.write(str(all_data, "UTF-8"))
        f.close()
    s.close()
    print(all_data)
    return all_data

"""
determine if content is chunked or not
- if chunked: return True and length of zero
- if not chunked: return False and content length
"""
def extract_metadata(header):
    chunked_string = b"Transfer-Encoding: chunked"
    content_length_string = b"Content-Length: "
    content_length_begin_index = header.find(content_length_string)
    #check if content length in header -> determine content length
    if content_length_begin_index != -1:
        content_length_end_index =  content_length_begin_index + header[content_length_begin_index:].find(b"\r\n")
        return False, header[content_length_begin_index+len(content_length_string):content_length_end_index]
    #check if chunked
    elif chunked_string in header:
        return True, 0



def main():
    try:
        while True:
            input_handler()

    except KeyboardInterrupt:
        pass

main()
