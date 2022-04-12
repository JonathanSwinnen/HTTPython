import socket
PORT = 80
ALLOWED_COMMANDS = ["HEAD", "GET", "PUT", "POST"]
REQUESTED_PAGES_FOLDER = "requested_pages/"

def input_handler():
    user_input = input("HTTP request: ").split(" ")
    http_command, URI = user_input[0], user_input[1]
    if http_command not in ALLOWED_COMMANDS:
        print("Not an allowed command, allowed commands are: ", *ALLOWED_COMMANDS)
        return
    if len(user_input) > 2:
        port = user_input[2]
    stripped_URI = URI.split("/", 3)
    #print(stripped_URI, len(stripped_URI))
    host = stripped_URI[2]
    path = "/"
    if len(stripped_URI) >= 4:
        path += stripped_URI[3]
    #print(http_command, URI)
    print(http_command, host, path)
    command_handler(http_command, host, path)

def command_handler(http_command, host, path):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, PORT))
        if (http_command == "HEAD"):
            dummy = send_request(http_command, host, path, s)
        elif (http_command == "GET"):
            # header = send_request("HEAD", host, path, s)
            # is_chunked, content_length = extract_metadata(header)
            # print(int(content_length))
            # full_page_size = len(header) + int(content_length)
            # print(full_page_size)
            dummy = send_request("GET", host, path, s)
        s.close()



def send_request(http_command, host, path, s):
    request = http_command + " " + path + " HTTP/1.1\r\nHost: " + host + "\r\n\r\n"
    print(request)
    s.send(bytes(request, 'UTF-8'))
    return response_handler(http_command, host, s)
    


def response_handler(http_command, host, s):
    if http_command == "HEAD":
        data = s.recv(1024)
        all_data = data
        while len(data) == 1024:
            data = s.recv(1024)
            all_data += data
    elif http_command == "GET":
        first_part_of_data = s.recv(1024)
        all_data = first_part_of_data
        print(all_data)
        print(len(all_data))
        is_chunked, content_length = extract_metadata(all_data)
        print(int(content_length))
        # full_page_size = len(header) + int(content_length)
        # print(full_page_size)
        # dummy = send_request("GET", host, path, is_chunked, int(content_length))

        if is_chunked:
            print("chunked transfer encoding is not yet supported")
        else:
            print(first_part_of_data[:determine_header_length(first_part_of_data)])
            remaining_content_length = int(content_length) - (len(first_part_of_data) - determine_header_length(first_part_of_data))
            print(remaining_content_length)
            data = s.recv(int(content_length))
            print(data)
            print(len(data))
            all_data += data
        f = open(REQUESTED_PAGES_FOLDER + host + ".html", "w")
        f.write(str(all_data, "UTF-8"))
        f.close()
    print(all_data)
    print(len(all_data))
    return all_data

"""
determine header length
"""
def determine_header_length(first_part_of_data):
    CLRF = b"\r\n\r\n"
    header_end_index = first_part_of_data.find(CLRF)
    return header_end_index + len(CLRF)

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
