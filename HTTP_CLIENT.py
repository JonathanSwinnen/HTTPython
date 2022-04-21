import socket
import HTTP_utils
import os
from io import BytesIO
from bs4 import BeautifulSoup
from PIL import Image

ALLOWED_COMMANDS = ["HEAD", "GET", "PUT", "POST"]
REQUESTED_PAGES_FOLDER = "web/imported_pages/"

# asks user for input, parses it and calls the command handler
def input_handler():
    # ask user for input on command line
    user_input = input("HTTP request: ").split(" ")
    # extract HTTP command and uri from user input
    http_command, uri = user_input[0], user_input[1]
    # check if http command is one of four supported/allowed commands
    if http_command not in ALLOWED_COMMANDS:
        print("Not an allowed command, allowed commands are: ", *ALLOWED_COMMANDS)
        return

    # parse entered uri (using helper function parse_uri in HTTP_utils)
    parsed_uri = HTTP_utils.parse_uri(uri)
    host = parsed_uri.host
    port = parsed_uri.port
    path = parsed_uri.path
    # if there is a query in the uri, add it to the path
    if parsed_uri.query != "":
        path += "?"+parsed_uri.query

    # call the command handler which takes action based on the entered HTTP command
    command_handler(http_command, host, port, path)


# create a socket, establish connection with the host, construct the HTTP request, send it to the host and call the response handler
def command_handler(http_command, host, port, path):
    # create a socket that will be used throughout the rest of the code
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # connect to the host, which is listening on the given port
        s.connect((host, port))
        # each request needs an HTTP command, path, HTTP version and a host
        request = http_command + " " + path + " HTTP/1.1\r\n"
        request += "Host: " + host
        # if the port is different than the default port 80, add it to the Host header
        if port != 80:
            request += ":" + str(port)
        request += "\r\n"
        # ask the server to keep the connection open since images might be requested and server over the same socket
        request += "Connection: Keep-Alive\r\n"

        # for the HEAD and GET command, no extra headers have to be added to the request
        if http_command == "HEAD" or http_command == "GET":
            pass
        # for the PUT and POST command, extra headers and a body has to be added
        if http_command == "PUT" or http_command == "POST":
            # ask to user to input the data for the body of the PUT and POST request
            data_to_send = input("Data to send: ")
            # determine and set the Content-Length of the data in the body + and the head with a double CRLF
            request += "Content-Length: " + str(len(data_to_send)) + "\r\n\r\n"
            # add the data to send as the body of the request
            request += data_to_send
        # add a final CRLF; for a double CRLF to end the head for a HEAD and GET command or to end the body for a PUT and POST command
        request += "\r\n"

        # convert the request string to bytes with a UTF-8 encoding and send it to the host
        s.send(bytes(request, 'UTF-8'))
        # show the final request that was sent, to the user
        print("\nSent request:\n" + request)
        # call the response handler, which will make sure the response is received correctly and take different action depending on which HTTP command was sent
        response_handler(http_command, host, port, s, is_html_data=True)
        # once the response has been fully handled, the connection to the host can be closed
        s.close()


# read the head of the response, for GET commands also read the body and take different action depending on the type of returned data
def response_handler(http_command, host, port, s, is_html_data):
    # read the head of the response (using the helper function read_head in HTTP_utils)
    initial_line, headers, header_data, header_error = HTTP_utils.read_head(s)
    status_code = initial_line.split(" ")[1:]
    # in case of a GET command, read the body, save the html data and look for and save embedded images
    if http_command == "GET" or http_command == "TEST":
        # read the body of the response (using the helper function read_body in HTTP_utils)
        data, body_error = HTTP_utils.read_body(s, headers)
        
        # if the received data is HTML data; decode it, search for embedded images and save the HTML data to a file
        if is_html_data:
            # show the status code of the response to the user
            print("GET request returned with status code: ", *status_code, "for HTML data")
            # decode the data using the ISO-8859-1 standard (UTF-8 gives errors on certain characters)
            html_data = data.decode(encoding="ISO-8859-1")
            # search for and retrieve images + change path of images when necessary (using the retrieve_images function)
            modified_html_data = retrieve_images(s, host, port, html_data)
            # write modified HTML data to a file
            # the HTML file will be saved in a folder named with the domain name of the host
            path = REQUESTED_PAGES_FOLDER + host
            # create this folder if it does not exist yet
            os.makedirs(path, exist_ok=True)
            # open the file in writing mode and create the file if it does not exist yet
            f = open(path + "/index.html", "w+")
            # write the data and close the file
            f.write(modified_html_data)
            f.close()
        else:
            # initialize image error to ok (there is no error)
            image_error = "ok"
            # if the received content is not an image type, the image will not have been retrieved successfully
            if headers.get("content-type")[:5] != "image":
                image_error = initial_line.split(" ")[1:]
            # return the data to the retrieve_images function
            return data, status_code
    else:
        # show the status code of the response to the user
        print(http_command + " request returned with status code: ", *status_code)



# search the HTML data for embedded images and their sources, retrieve the images over the same or a different socket than the HTML, depending on the host that holds the images
def retrieve_images(s, host, port, html_data):
    # parse the HTML into a Beautifulsoup object
    soup = BeautifulSoup(html_data, 'html.parser')
    # loop through all images (labeled with the 'img' tag), found in the HTML
    for image in soup.find_all("img"):
        # get the source from the 'src' attribute of the 'img' tag
        img_source = image['src']
        retrieve_image_from_source(s, host, port, image, img_source, 'src')
        # check if there is also a 'lowsrc' attribute
        if image.has_attr('lowsrc'):
            retrieve_image_from_source(s, host, port, image, image['lowsrc'], 'lowsrc')
        
    # return the modified HTML after re-encoding it
    return soup.prettify(soup.original_encoding)


# retrieve image from provided source
def retrieve_image_from_source(s, host, port, soup_image, img_source, src_attribute):
    # parse the image source (using the helper function parse_uri in HTTP_utils)
    img_source_parsed = HTTP_utils.parse_uri(img_source)
    img_host = img_source_parsed.host
    img_path = img_source_parsed.path
    img_port = img_source_parsed.port

    # check if the image needs to be retrieved from a different host than the one used for the HTML
    if img_host != host and img_host != img_source.split("/")[0] and img_host != None:
        # construct the GET request using the image path and its host
        image_request = "GET " + img_path + " HTTP/1.1\r\n"
        image_request += "Host: " + img_host
        # if a specific (non-default) port was specified add the port to the Host header
        if img_port != None:
            image_request += ":" + str(img_port)
        # end the header (and request) with a double CRLF (a Connection: Keep-Alive is not needed since a different socket is used for each image)
        image_request += "\r\n\r\n"
        # create a new socket to retrieve the image
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
            # connect to the host that holds the image, listening at the specified port
            s2.connect((img_host, img_port))
            # convert the constructed request to bytes using UTF-8 encoding and send it to the host
            s2.send(bytes(image_request, 'UTF-8'))
            # call on the response handler to correctly receive the image
            image_data, status_code = response_handler("GET", img_host, port, s2, is_html_data=False)
            # close the connection to the host once the image has been retrieved
            s2.close()
        # show the status code of the response to the user
        print("GET request returned with status code: ", *status_code, "for image with source: " + img_source)
        # check that the image got retrieved correctly if so:
        #   - write received image data to file
        #   - change the image source in the HTML so the HTML file looks in the right place
        if status_code == ["200", "OK"]:
            # the image will be saved in a folder named with the domain name of the host (that hosts the HTML page, not the one that hosts the image),
            #   followed by the path extracted from the source URI (except the filename itself)
            path = REQUESTED_PAGES_FOLDER + host + img_path.rsplit("/",1)[0]
            # create this folder if it does not exist yet
            os.makedirs(path, exist_ok=True)
            # convert the image data byte string to a byte stream
            stream = BytesIO(image_data)
            # save the image to the previously specified path (now with filename)
            img = Image.open(stream)
            img.save(REQUESTED_PAGES_FOLDER + host + img_path)
            # change the src_attribute of the 'img' tag, so the HTML file looks in the right place for the image
            #   + make sure there is no leading slash, so that the HTML file looks for the image in its own folder, not the root folder
            if img_path[0] == "/":
                soup_image[src_attribute] = img_path[1:]
            else:
                soup_image[src_attribute] = img_path
            # make sure there are no %-characters in the source path
            soup_image[src_attribute] = soup_image[src_attribute].replace("%","")

    # if not; retrieve image from current host using same socket
    else:
        # having or not having a leading slash, both create a different problem
        #   	+ make sure there are no %-characters in the source paths
        if img_source[0] == "/":
            # leading slash -> make sure the HTML file looks for the image in the same folder as the HTML file, not the root folder,
            #   therefore modify the src_attribute of the 'img' tag
            soup_image[src_attribute] = img_source[1:].replace("%","")
        else:
            # no leading slash -> make sure there is a leading slash in the path for the GET request
            img_source = "/" + img_source
            soup_image[src_attribute] = soup_image[src_attribute].replace("%","")
        
        # construct the GET request for the image
        image_request = "GET " + img_source + " HTTP/1.1\r\n"
        image_request += "Host: " + host
        # if the port is different than the default port 80, add it to the Host header
        if port != 80:
            image_request += ":" + str(port)
        image_request += "\r\n"
        # ask the host to keep the connection open, since requests for other images might follow
        image_request += "Connection: Keep-Alive\r\n\r\n"
        # convert the constructed request to bytes using UTF-8 encoding and send it to the host
        s.send(bytes(image_request, 'UTF-8'))
        # call on the response handler to correctly receive the image
        image_data, status_code = response_handler("GET", host, port, s, is_html_data=False)
         # show the status code of the response to the user
        print("GET request returned with status code: ", *status_code, "for image with source: " + img_source)
        # check that the image got retrieved correctly if so:
        #   - write received image data to file
        if status_code == ["200", "OK"]:
            # make sure there are no %-characters in the source path
            img_source = img_source.replace("%","")
            # the image will be saved in a folder named with the domain name of the host, followed by the path extracted from the source URI (except the filename itself)
            path = REQUESTED_PAGES_FOLDER + host + img_source.rsplit("/",1)[0]
            # create this folder if it does not exist yet
            os.makedirs(path, exist_ok=True)
            # convert the image data byte string to a byte stream
            stream = BytesIO(image_data)
            # save the image to the previously specified path (now with filename)
            img = Image.open(stream)
            img.save(REQUESTED_PAGES_FOLDER + host + img_source)


# Client entry point
def main():
    print("\n========================================================================\n")
    print("Welcome to this HTTP client.")
    print("This client supports HTTP version 1.1")
    print("The requests should be entered in the following format: HTTP_COMMAND URI")
    print("Supported commands: HEAD, GET, PUT, POST")
    print("\n========================================================================\n")
    try:
        # keep on running the input handler to serve new requests once the previous request has completed
        while True:
            input_handler()
            print("\n========================================================================\n")

    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
