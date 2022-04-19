import socket
import HTTP_SERVER

# test 4 standard methods
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(("192.168.0.124", 80))
    s.sendall(
        b"""PUT /data2/test/deep%20folder/txt.txt HTTP/1.1\r\nHost: 192.168.0.124\r\nContent-Length:5\r\n\r\n12345"""
    )
