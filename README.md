# CN_HTTP

This project implements a simple HTTP 1.1 server and client.

## Python version & Libraries

This project was made in python 3.6.8, and also uses the packages `Pillow` and `bs4`.

## Important files and directories:

 - `HTTP_CLIENT.py` : the client program
 - `HTTP_SERVER.py` : the main server program
 - `request_validation.py` : functions for the server to validate incoming requests
 - `server_settings.py` : a file where you can modify some default settings
 - `HTTP_utils.py` : useful functions used by both the client and server programs
 - `web/` : the root directory for the website hosted by the server

## How to use the programs:

### Client

To start the client, run `HTTP_CLIENT.py`
You will be prompted to enter an HTTP request, which should be in the following format: `HTTP_COMMAND URI`.
Where `HTTP_COMMAND` is one of four supported commands (`HEAD`, `GET`, `PUT`, `POST`) and the `URI` should follow the format: `http://DOMAIN_NAME[:PORT]/PATH`
The default port of `80` is used, a non-default port can be specified in the `URI` as shown above.

When you enter a `PUT` or `POST` request, the server prompts you to enter the data you want to send to the earlier entered host.

For each command, the sent request constructed based on the user input is shown. Once a response from the server has been received, the status code is displayed. For a `GET` request the status codes for the responses on possible `GET` requests for embedded images are shown as well, together with the source of that image.

The received HTML data from a `GET` request is stored in the following path: `web/imported_pages/HOST/index.html`
As for the images, these are stored relative to the paht `web/imported_pages/HOST`. Where `HOST` is the domain name or IP address of the host.

### Server

#### Starting the server
To start the server, run `HTTP_SERVER.py`. The server will start with the default settings found in `server_settings.py`.
The default port is 8000 instead of 80, since using port 80 requires admin privileges, which is less convenient for testing.
\
You can also run the server from the command line to start with different settings. Any of the following arguments can be set:
(all arguments are optional and can be left out, order does not matter)
```
python HTTP_SERVER.py -p <PORT> -t <TIMEOUT> -h <HOME_PAGE> -r <WEB_ROOT> --log-body --no-threading --localhost
```
- `-p` : Sets the server port. Default 8000. To use low numbered ports, you might need to run the command using `sudo`
- `-t` : Sets the connection timeout time. Default 30
- `-h` : Sets the website home page. Default `index.html`
- `-r` : Sets the website root directory. Default `web`
- `--log-body` : Log response bodies. Can be useful for debugging.
- `--no-threading` : Turn off threading. Can be useful for debugging.
- `--localhost` : Force the server to run on `localhost` / `127.0.0.1`

When the server starts, it prints its IP address and port. You can use this address to send HTTP requests to. When you are not connected to a network, 
the server will run on the localhost ip `127.0.0.1`. 

#### Functionality
The server can serve valid `GET` and `HEAD` requests for any existing resource under the website root. 
You can also visit the webpages using a standard web browser.\
When a `GET` or `HEAD` request is sent for a directory path, the server will generate a simple page listing the contents of the directory. \
Resources that are not found will properly return a `404 Not Found` status code along with an automatically generated error message webpage. 
`GET` and `HEAD` requests also support the `If-Modified-Since` header and return a `304 Not Modified` response without a body
when the requested resource was not modified since the given date.\
\
The server can execute `PUT` and `POST` requests to write to files contained in the directories specified in the `ALLOW_WRITE` 
setting in `server_settings.py`. A `PUT` request will overwrite the file, a `POST` will append its contents to the end of the file on a new line. \
Writing to a resource that is not contained in the allowed directories results in a `405 Method Not Allowed` response. This is demonstrated on 
the webpage `/web/errors/post_error.html`. This limitation was to ensure we didn't accidentally overwrite our homepage while testing, 
an can be turned off by just setting `ALLOW_WRITE = ("/",)` in `server_settings.py`. \
`PUT` and `POST` requests can't be used on directories, only on files. If a `PUT` or `POST` request is used on a file that does not exist,
it will be created if possible.\
\
The server will validate incoming requests and reject it when it is deemed invalid. In such a case, the server will respond with `400 Bad Request`.
Other error codes that the server can occasionaly throw, which were not required for the project assignment, but seemed useful anyways 
(for example for debugging), are `405 Method Not Allowed` for invalid methods, `411 Length Required` for missing content lengths, and `501 Not Implemented`
for unimplemented functionality. We also added `505 Version Not Supported` when the request HTTP version is not 1.1. \
\
We intentionally left an edge case in our code, which will result in an Exception. This happens when a `PUT` or `POST` request tries to create
a file in a folder that does not yet exist, but has the same name as a file that does exist. (for example, the file `/data/test` exists and a `PUT` request
tries to create the file `/data/test/file`). This causes an exception, which will be caught by a general exception handler resulting in a `500 Internal Server Error`.
A variant of this edge case is demonstrated on the page `/web/errors/post_edgecase.html`.














