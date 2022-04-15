def read_head(c):
    req = ""
    method = ""
    uri = ""
    httpv = ""
    total = ""
    headers = dict()
    reading_head = True
    while reading_head:
        # receive
        try:
            data_chunk = c.recv(1)
        except c.timeout as e:
            err = e.args[0]
            # this next if/else is a bit redundant, but illustrates how the
            # timeout exception is setup
            if err == 'timed out':
                print('TIMEOUT')
                break
            else:
                print(e)
                break
        except c.error as e:
            # Something else happened, handle error, exit, etc.
            print(e)
            break
        req += data_chunk.decode()
        print(req)
        total += data_chunk.decode()
        recv_lines = req.split("\r\n")
        # parse received lines
        i = 0
        for line in recv_lines:
            i += 1
            if i == len(recv_lines):  # last line
                if line == "":  # completed line at the end
                    req = ""
                else:  # incomplete line at the end
                    req = line  # continue receiving last request line
            elif method == "":  # expecting Request-Line (method, uri, http version)
                req_line = line.split(" ")
                method = req_line[0]
                uri = req_line[1]
                httpv = req_line[2]
                print("\nread request-line: " + line + "   , expecting headers ...")
            else:  # expecting headers or newline to end
                if line != "":
                    print("\nreading header: " + line)
                    header_line = line.split(":", 1)
                    print(header_line)
                    headers[header_line[0].lower()] = header_line[1].strip()
                else:  # CRLF after headers --> end request or body
                    print("END HEADERS\n")
                    reading_head = False
    return method, uri, httpv, headers, total