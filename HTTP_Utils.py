def read_head(c):
    req = ""
    initial_line = ""
    total = ""
    headers = dict()
    reading_head = True
    while reading_head:
        # receive
        try:
            data_chunk = c.recv(1)
        except c.error as e:
            # Something happened ?
            print(e)
            break
        req += data_chunk.decode()
        # print(req)
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
            elif initial_line == "":  # expecting Request-Line (method, uri, http version)
                initial_line = line
                # print("\nread request-line: " + line + "   , expecting headers ...")
            else:  # expecting headers or newline to end
                if line != "":
                    # print("\nreading header: " + line)
                    header_line = line.split(":", 1)
                    # print(header_line)
                    headers[header_line[0].lower()] = header_line[1].strip()
                else:  # CRLF after headers --> end request or body
                    # print("END HEADERS\n")
                    reading_head = False
    return initial_line, headers, total
