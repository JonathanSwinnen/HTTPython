import binascii
import socket
import HTTP_utils
from bs4 import BeautifulSoup
import os
from io import BytesIO
from PIL import Image
ALLOWED_COMMANDS = ["HEAD", "GET", "PUT", "POST"]
REQUESTED_PAGES_FOLDER = "web/imported_pages/"

def input_handler():
    user_input = input("HTTP request: ").split(" ")
    http_command, uri = user_input[0], user_input[1]
    if http_command not in ALLOWED_COMMANDS:
        print("Not an allowed command, allowed commands are: ", *ALLOWED_COMMANDS)
        return

    parsed_uri = HTTP_utils.parse_uri(uri)
    host = parsed_uri.host
    port = parsed_uri.port
    path = parsed_uri.path
    if parsed_uri.query != "":
        path += "?"+parsed_uri.query

    print(http_command, uri)
    print(http_command, host, path)
    command_handler(http_command, host, port, path)


def command_handler(http_command, host, port, path):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        request = http_command + " " + path + " HTTP/1.1\r\n"
        request += "Host: " + host
        if port != 80:
            request += ":" + str(port)
        request += "\r\n"
        request += "Connection: Keep-Alive\r\n"

        if http_command == "HEAD" or http_command == "GET":
            pass
        if http_command == "PUT" or http_command == "POST":
            data_to_send = input("Data to send: ")
            request += "Content-Length: " + str(len(data_to_send)) + "\r\n\r\n"
            request += data_to_send
        request += "\r\n"
        print(request)
        s.send(bytes(request, 'UTF-8'))
        response_handler(http_command, host, port, s, is_html_data=True)
        s.close()


def response_handler(http_command, host, port, s, is_html_data):
    initial_line, headers, header_data, header_error = HTTP_utils.read_head(s)
    if http_command == "GET" or http_command == "TEST":
        data, body_error = HTTP_utils.read_body(s, headers)
        
        if is_html_data:
            print(header_data)
            print(headers)
            html_data = data.decode(encoding="ISO-8859-1")
            # search for and retrieve images + change path of images when necessary
            modified_html_data = retrieve_images(s, host, port, html_data)
            # write received html data to file
            path = REQUESTED_PAGES_FOLDER + host
            os.makedirs(path, exist_ok=True)
            f = open(path + "/index.html", "w+")
            f.write(modified_html_data)
            f.close()
        else:
            image_error = "ok"
            # if the received content is not an image type, the image won;t have been retrieved successfully
            if headers.get("content-type")[:5] != "image":
                image_error = initial_line.split(" ")[1:]
            return data, image_error
        

    # print(header_data)
    # print(len(header_data))
    # if html_data:
    #     print(html_data)
    #     print(len(html_data))
    print(http_command + " request returned with status code: ", *initial_line.split(" ")[1:])
    # return all_data


def retrieve_images(s, host, port, html_data):
    soup = BeautifulSoup(html_data, 'html.parser')
    print(soup.find_all("img"))
    for image in soup.find_all("img"):
        print(image['src'])
        img_source = image['src']
        img_source_parsed = HTTP_utils.parse_uri(image['src'])
        img_host = img_source_parsed.host
        img_path = img_source_parsed.path
        img_port = img_source_parsed.port
        print(img_host, img_path)

        # check if the image needs to be retrieved from a different source
        if img_host != host and img_host != img_source.split("/")[0] and img_host != None:
            image_request = "GET " + img_path + " HTTP/1.1\r\n"
            image_request += "Host: " + img_host
            if img_port != None:
                image_request += ":" + str(img_port)
            image_request += "\r\n\r\n"
            # image_request += "Connection: Keep-Alive\r\n\r\n"
            print(image_request)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
                s2.connect((img_host, img_port))
                s2.send(bytes(image_request, 'UTF-8'))
                image_data, error = response_handler("GET", img_host, port, s2, is_html_data=False)
            print(image['src'])
            print(img_source, image_data)
            if error != "ok":
                print("Retrieving image with source " + img_source + ", returned with status code: ", *error)
            else:
                # write received image data to file
                path = REQUESTED_PAGES_FOLDER + host + img_path.rsplit("/",1)[0]
                os.makedirs(path, exist_ok=True)
                stream = BytesIO(image_data)
                img = Image.open(stream)
                img.save(REQUESTED_PAGES_FOLDER + host + img_path)

        # if not retrieve image from current host using same socket
        else:
            # having or not having a leading slash both create a (different) problem
            if img_source[0] == "/":
                # make sure the html file looks for the image in the same folder, not the root folder
                image['src'] = img_source[1:]
            else:
                # make sure there is a leading slash in the path for the GET request
                img_source = "/" + img_source
            image_request = "GET " + img_source + " HTTP/1.1\r\n"
            image_request += "Host: " + host
            if port != 80:
                image_request += ":" + str(port)
            image_request += "\r\n"
            image_request += "Connection: Keep-Alive\r\n\r\n"
            print(image_request)
            s.send(bytes(image_request, 'UTF-8'))
            image_data, error = response_handler("GET", host, port, s, is_html_data=False)
            print(image['src'])
            print(img_source, image_data)
            if error != "ok":
                print("Retrieving image with source " + img_source + ", returned with status code: ", *error)
            else:
                # write received image data to file
                path = REQUESTED_PAGES_FOLDER + host + img_source.rsplit("/",1)[0]
                os.makedirs(path, exist_ok=True)
                stream = BytesIO(image_data)
                img = Image.open(stream)
                img.save(REQUESTED_PAGES_FOLDER + host + img_source)

    return soup.prettify(soup.original_encoding)


def main():
    try:
        while True:
            input_handler()

    except KeyboardInterrupt:
        pass

main()
