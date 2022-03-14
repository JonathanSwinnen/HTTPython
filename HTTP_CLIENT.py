import socket
PORT = 80

input = input("HTTP request: ")
http_command, URI = input.split(" ")[:2]
stripped_URI = URI.split("/", 3)
HOST = stripped_URI[2]
PATH = "/" + stripped_URI[3]
print(http_command, URI)
print(HOST, PATH)


def send_request(http_command, HOST, PATH):
    request = http_command + PATH + "HTTP/1.1"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(("127.0.0.1", PORT))
        s.send(bytes(request, 'UTF-8'))
        data = s.recv(1024)
        all_data = data
        while len(data) == 1024:
            data = s.recv(1024)
            all_data += data

send_request(http_command, 0, "/")