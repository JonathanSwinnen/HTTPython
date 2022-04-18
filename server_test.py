import socket
import HTTP_SERVER

# test 4 standard methods
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HTTP_SERVER.getmyip(), HTTP_SERVER.PORT))
    s.sendall(
        b"""GET / HTTP/1.1\r\nHost: 192.168.2.20:8000\r\n\r\n"""
    )
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HTTP_SERVER.getmyip(), HTTP_SERVER.PORT))
    s.sendall(
        b"""HEAD / HTTP/1.1\r\nHost: 192.168.2.20:8000\r\n\r\n"""
    )
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HTTP_SERVER.getmyip(), HTTP_SERVER.PORT))
    s.sendall(
        b"""PUT /data/post_data.txt HTTP/1.1\r\nHost: 192.168.2.20:8000\r\nContent-Length: 20\r\n\r\nCleared by testsuite"""
    )
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HTTP_SERVER.getmyip(), HTTP_SERVER.PORT))
    s.sendall(
        b"""POST /data/post_data.txt HTTP/1.1\r\nHost: 192.168.2.20:8000\r\nContent-Length: 11\r\n\r\nAppend test"""
    )

# test unsupported method
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HTTP_SERVER.getmyip(), HTTP_SERVER.PORT))
    s.sendall(
        b"""BADMETHOD / HTTP/1.1\r\nHost: 192.168.2.20:8000\r\nIf-Modified-Since: Sun, 17 Apr 2022 20:50:58 GMT\r\n\r\n"""
    )
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HTTP_SERVER.getmyip(), HTTP_SERVER.PORT))
    s.sendall(
        b"""OPTIONS /trol HTTP/1.1\r\nHost: 192.168.2.20:8000\r\nEmpty-Header:\r\nContent-Length:-1\r\n\r\n"""
    )

# test other req line mistakes
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HTTP_SERVER.getmyip(), HTTP_SERVER.PORT))
    s.sendall(
        b"""GET HTTP/1.1\r\nHost: 192.168.2.20:8000\r\nIf-Modified-Since: Sun, 17 Apr 2022 20:50:58 GMT\r\n\r\n"""
    )
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HTTP_SERVER.getmyip(), HTTP_SERVER.PORT))
    s.sendall(
        b"""GET / BAD/1.1\r\nHost: 192.168.2.20:8000\r\nEmpty-Header:\r\nContent-Length:-1\r\n\r\n"""
    )
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HTTP_SERVER.getmyip(), HTTP_SERVER.PORT))
    s.sendall(
        b"""GET / HTTP/2.3\r\nHost: 192.168.2.20:8000\r\nEmpty-Header:\r\nContent-Length:-1\r\n\r\n"""
    )
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HTTP_SERVER.getmyip(), HTTP_SERVER.PORT))
    s.sendall(
        b"""GET / HTTP/bad\r\nHost: 192.168.2.20:8000\r\nEmpty-Header:\r\nContent-Length:-1\r\n\r\n"""
    )