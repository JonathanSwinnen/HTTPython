import socket
import HTTP_Utils
PORT = 8000
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
        request = http_command + " " + path + " HTTP/1.1\r\nHost: " + host + "\r\n"
        if http_command == "HEAD" or http_command == "GET":
            request += "\r\n"
        if http_command == "PUT" or http_command == "POST":
            data_to_send = input("Data to send: ")
            request += "Content-Length: " + str(len(data_to_send)) + "\r\n"
            request += "\r\n"
            request += data_to_send
        s.send(bytes(request, 'UTF-8'))
        response_handler(http_command, host, s)
        s.close()



# def send_request(request, s):
#     print(request)
        


def response_handler(http_command, host, s):
    initial_line, headers, all_data = HTTP_Utils.read_head(s)
    if http_command == "GET":
        # first_part_of_data = s.recv(1024)
        # check if end of header is found (CRLF)
        print(all_data)
        print(len(all_data))
        print(headers)
        # is_chunked, content_length = extract_metadata(all_data)
        # print(int(content_length))
        # dummy = send_request("GET", host, path, is_chunked, int(content_length))

        if headers.get("transfer-encoding") == "chunked":
            print("chunked transfer encoding is not yet supported")
        else:
            # print(first_part_of_data[:determine_header_length(first_part_of_data)])
            # remaining_content_length = int(content_length) - (len(first_part_of_data) - determine_header_length(first_part_of_data))
            # print(remaining_content_length)
            content_length = int(headers.get("content-length"))
            print(content_length)
            data = s.recv(int(content_length)).decode()
            print(data)
            print(len(data))
            all_data += data
        f = open(REQUESTED_PAGES_FOLDER + host + ".html", "w")
        f.write(all_data)
        f.close()
    print(all_data)
    print(len(all_data))
    print(http_command + " request returned with status code: ", *initial_line.split(" ")[1:])
    # return all_data

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
