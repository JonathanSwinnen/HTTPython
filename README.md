# CN_HTTP

This project implements a simple HTTP 1.1 server and client.

## Important files and directories:

 - `HTTP_CLIENT.py` : the client program
 - `HTTP_SERVER.py` : the main server program
 - `request_validation.py` : functions for the server to validate incoming requests
 - `server_settings.py` : a file where you can modify some default settings
 - `HTTP_utils.py` : useful functions used by both programs
 - `web/` : the root directory for the website hosted by the server

## How to use the programs:

### Client

To start the client, run `HTTP_CLIENT.py`
...  <-- TODO: Andres leg jij hier nog even heel basic uit hoe de client werkt? Het moet niet even veel zijn als voor de server hoor. Gewoon kort wat er moet ingetypt worden en waar de gedownloade files kunnen teruggevonden worden.


### Server

#### Starting the server
To start the server, run `HTTP_SERVER.py`. The server will start with the default settings found in `server_settings.py`.
The default port is 8000 instead of 80, since using port 80 requires admin privileges, which is less convenient for testing.
\
You can also run the server from the command line to start with different settings. Any of the following arguments can be set:
(all arguments are optional and can be left out, order does not matter)
```
python HTTP_SERVER.py -p <PORT> -t <TIMEOUT> -h <HOME_PAGE> -r <WEB_ROOT> --log-body --no-threading --strict --localhost
```
- `-p` : Sets the server port. Default 8000. To use low numbered ports, you might need to run the command using `sudo`
- `-t` : Sets the connection timeout time. Default 30
- `-h` : Sets the website home page. Default `index.html`
- `-r` : Sets the website root directory. Default `web`
- `--log-body` : Log response bodies. Can be useful for debugging.
- `--no-threading` : Turn off threading. Can be useful for debugging.
- `--strict` : Turns on some header validations that might be too strict. These are things we weren't 100% sure about and observed some other servers reject and others don't.
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
setting in `server_settings.py`. This limitation was to ensure we didn't accidentally overwrite our homepage while testing, an can be turned off
by just setting `ALLOW_WRITE = ("/",)`. A `PUT` request will overwrite the file, a `POST` will append its contents to the end of the file on a new line. \
Writing to a resource that is not contained in the allowed directories results in a `405 Method Not Allowed` 
response. This is demonstrated on the webpage `/web/errors/post_error.html`. `PUT` and `POST` requests can't be used on directories, only on files. If a `PUT` or `POST` request is used on a file that does not exist,
it will be created if possible.\
\
The server will validate incoming requests and reject it when it is deemed invalid. In such a case, the server will respond with `400 Bad Request`.
Other error codes that the server can occasionaly throw, which were not required for the project assignment, but seemed useful anyways 
(for example for debugging), are `405 Method Not Allowed` for invalid methods, `411 Length Required` for missing content lengths, and `501 Not Implemented`
for unimplemented functionality. We also added `505 Version Not Supported` when the request HTTP version is not 1.1. \
\
We intentionally left an edge case in our code, which will result in an Exception. This happens when a `PUT` or `POST` request tries to create
a file in a folder that does not yet exist, but has the same name as a file that does exist. (for example, the file `/data/test` exists and a `PUT` request
tries to create the file `/data/test/file`). This causes an exception, which will be caught by a main unknown exception handler resulting in a `500 Internal Server Error`.
A variant of this problem is demonstrated on the page `/web/errors/post_edgecase.html`.














