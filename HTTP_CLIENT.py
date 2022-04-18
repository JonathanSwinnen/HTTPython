import socket
import HTTP_utils
from bs4 import BeautifulSoup
# import sys
# print(sys.version)
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
    # parsed_URI = HTTP_Utils.parse_uri(URI)
    stripped_URI = URI.split("/", 3)
    #print(stripped_URI, len(stripped_URI))
    host = stripped_URI[2]
    path = "/"
    if len(stripped_URI) >= 4:
        path += stripped_URI[3]
    print(http_command, URI)
    print(http_command, host, path)
    command_handler(http_command, host, path)


def command_handler(http_command, host, path):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, PORT))
        request = http_command + " " + path + " HTTP/1.1\r\n"
        request += "Host: " + host + "\r\n"
        request += "Connection: Keep-Alive\r\n"
        if http_command == "HEAD" or http_command == "GET":
            request += "\r\n"
        if http_command == "PUT" or http_command == "POST":
            data_to_send = input("Data to send: ")
            request += "Content-Length: " + str(len(data_to_send)) + "\r\n"
            request += "\r\n"
            request += data_to_send
        print(request)
        s.send(bytes(request, 'UTF-8'))
        response_handler(http_command, host, s)
        s.close()



# def send_request(request, s):
#     print(request)
        


def response_handler(http_command, host, s):
    initial_line, headers, header_data = HTTP_utils.read_head(s)
    if http_command == "GET":
        print(header_data)
        print(len(header_data))
        print(headers)
        chunked = headers.get("transfer-encoding")
        if headers.get("transfer-encoding") == "chunked":
            content_length = 0
        else:
            content_length = int(headers.get("content-length"))
        html_data, error = HTTP_utils.read_body(s, content_length, chunked)
        # write received html data to file
        f = open(REQUESTED_PAGES_FOLDER + host + ".html", "w")
        f.write(html_data)
        f.close()
        # search for and retrieve images
        retrieve_images(s, host, html_data)
        

    # print(header_data)
    # print(len(header_data))
    # if html_data:
    #     print(html_data)
    #     print(len(html_data))
    print(http_command + " request returned with status code: ", *initial_line.split(" ")[1:])
    # return all_data


def retrieve_images(s, host, html_data):
    soup = BeautifulSoup(html_data, 'html.parser')
    print(soup.find_all("img"))
    for image in soup.find_all("img"):
        img_source = image['src']
        if img_source[0] != "/":
            img_source = "/" + img_source
        image_request = "GET " + img_source + " HTTP/1.1\r\n"
        image_request += "Host: " + host + "\r\n"
        image_request += "Connection: Keep-Alive\r\n"
        print(image_request)
        s.send(bytes(image_request, 'UTF-8'))
        image_data = b""
        image_size = 0
        while True:
            try:
                data = s.recv(1024)
                if not data:
                    break
                image_size = image_size + len(data)
                print(len(data), image_size)
                image_data += data
            except KeyboardInterrupt:
                break
        print(img_source, image_data)

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
