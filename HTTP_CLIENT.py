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
    send_request(http_command, host, path)


def send_request(http_command, host, path):
    request = http_command + " " + path + " HTTP/1.1 \n\n"
    print(request)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, PORT))
        s.send(bytes(request, 'UTF-8'))
        response_handler(http_command, s, host, path)


def response_handler(http_command, s, host, path):
    data = s.recv(1024)
    all_data = data
    while len(data) == 1024:
        data = s.recv(1024)
        all_data += data
    print(all_data, len(data))
    if http_command == "GET":
        f = open(REQUESTED_PAGES_FOLDER + host + ".html", "w")
        f.write(str(all_data, "UTF-8"))
        f.close()
    s.close()


def main():
    try:
        while True:
            input_handler()

    except KeyboardInterrupt:
        pass

main()
