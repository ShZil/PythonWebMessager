import os
import socket

import http_codes as codes
from my_colors import *
from settings import *

# Adapted from assignment (23/01/2022).
__author__ = "Shaked Dan Zilberman"
CRLF = '\r\n'
RESPONSE_CONTENT_SNIPPET = False
types_dict = {
    'html': "text/html; charset=utf-8",
    'htm': "text/html; charset=utf-8",
    'txt': "text/plain",
    'css': "text/css",
    'js': "text/javascript; charset=utf-8",
    'jpg': "image/jpeg",
    'jpeg': "image/jpeg",
    'ico': "image/x-icon",
    'otf': "font/otf",
    'png': "image/png"
}


def parse_HTTP_request(req: str) -> tuple[str, str, str, str, list[tuple[str, str]], str]:
    """
    Disassembles an HTTP request.
    """
    try:
        # Each line ends with CRLF
        lines = req.split(CRLF)
        # Request ends with double CRLF, so remove those
        content = lines[-1]
        lines = lines[:-2]
        # First line separator is ' '
        method, url, version = lines[0].split(' ')
        if '?' in url:
            url, query = url.split('?')
        else:
            query = ''
        # Headers separator is ':'
        headers = [line.split(':', 1) for line in lines[1:]]
        # Pack headers to tuples
        headers = [(header[0], header[1]) for header in headers]

        # Fix 'JS fetch API' bug for `GET /chat`:
        if url == '/':
            chat = get_header(headers, "chat")
            if chat != '':
                url = ('' if chat.startswith('/') else '/') + chat.strip()

        return method, url, query, version, headers, content
    except IndexError:
        raise HTTPException("Invalid HTTP request")


def print_HTTP_request(method, url, query, version, headers, content):
    """
    Print the HTTP request you got.
    """
    CONTENT_PREVIEW_LENGTH = 100
    print(f"\n--------------------")
    print(f"Method: {method}\n")
    print(f"URL: {url}\n")
    print(f"Query: {query}\n")
    print(f"Version: {version}\n")
    print("Headers:")
    print("\n    " + "\n    ".join([':'.join(header) for header in headers]))
    print("\nContent:\n")
    print(content[:CONTENT_PREVIEW_LENGTH] + ("..." if len(content) > CONTENT_PREVIEW_LENGTH else content))
    print(f"\n--------------------")


def create_HTTP_response(version, status, content_type, content, headers={}):
    """
    Creates an HTTP response as string.
    """
    try:
        content = content.encode()
    except AttributeError:
        pass
    res = version + " " + str(status) + " " + codes.status[status][0] + CRLF
    length = len(content)
    res += "Content-Length: " + str(length) + CRLF
    res += "Content-Type: " + content_type + CRLF
    for header, value in headers.items():
        res += f"{header}: {value}" + CRLF
    res += CRLF
    res = res.encode()
    res += content
    return res


def print_HTTP_response(response, istext):
    """
    Prints an HTTP response.
    """
    CONTENT_PREVIEW_LENGTH = 1000
    if istext:
        if len(response) > CONTENT_PREVIEW_LENGTH:
            response = response[:CONTENT_PREVIEW_LENGTH - 3] + "...".encode()
        response = response.decode()
    print(response)
    print()


def get_404_page(url):
    """
    Creates a 404 response, either HTML or hard-coded short HTML.
    """
    try:
        return get_file("error.html").replace('/* PALETTE */', get_file('css/palette.css', log=False)).replace("NUM", "404").replace("TITLE", "NOT FOUND").replace("ERROR", "The resource was not found.").replace("EXPLAIN", "Select another resource.")
    except (FileNotFoundError, OSError):
        return f"<h1 style=\"font-family: sans-serif;\"><span style=\"color: red;\">404</span> Resource <code>{url}</code> was sadly not found, please try another.</h1>"


def get_403_page(url):
    """
    Creates a 403 response, either HTML or hard-coded short HTML.
    """
    try:
        return get_file("error.html").replace('/* PALETTE */', get_file('css/palette.css', log=False)).replace("NUM", "403").replace("TITLE", "FORBIDDEN").replace("ERROR", "This resource is forbidden.").replace("EXPLAIN", "Try to enter the website again.")
    except (FileNotFoundError, OSError):
        return f"<h1 style=\"font-family: sans-serif;\"><span style=\"color: red;\">403</span> Resource <code>{url}</code> is forbidden, please try another.</h1>"


def requested(client) -> tuple[str | bool, str | bool, str | bool, str | bool, list[tuple[str, str]] | bool, str | bool]:
    """
    Accept an HTTP request from a client and parse it.
    Returns tuple of the form: `(method: str, url: str, query: str, version: str, headers: [(str, str),...], content: str)`,
    or `(False, False, False, False, False, False)` if request could not be parsed.
    """
    try:
        req = client.recv(1024).decode()
    except UnicodeDecodeError:
        req = ""
    # print(req)
    try:
        method, url, query, version, headers, content = parse_HTTP_request(req)
        if not url.startswith('/'):
            url = '/' + url
        if method == "HEAD": method = "GET"
        # print_HTTP_request(method, url, query, version, headers, content)
    except HTTPException:
        print(f"~> Bad request (Len{'' if MINIMAL_PRINTING else 'gth'}={len(req)})", end=(': ' if len(req) > 0 else ''))
        print(req, end="   ")
        return False, False, False, False, False, False
    return method, url, query, version, headers, content


def reply(client, version, status, content, content_type="text/plain", headers={}):
    """
    Sends a reply.
    """
    res = create_HTTP_response(version, status, content_type, content, headers)
    client.send(res)

    status_color = gray
    if status >= 200: status_color = green
    if status >= 300: status_color = cyan
    if status >= 400: status_color = red
    if status >= 500: status_color = orange

    if MINIMAL_PRINTING:
        print(f"{yellow}{version} {status_color}{status} {codes.status[status][0]}{end}", end=" ")
        if len(headers) > 0:
            print("(", end="")
            for header, value in headers.items():
                print(f"{blue}{header}{end}", end=", ")
            print("\b\b) ", end="")
        print("~>")
    else:
        print(f"<~ {yellow}{version} {status_color}{status} {codes.status[status][0]}{end}")
        for header, value in headers.items():
            print(f"    {blue}{header}{end}: {magenta}{value}{end}")
        
    if RESPONSE_CONTENT_SNIPPET and not MINIMAL_PRINTING:
        CONTENT_PREVIEW = 100
        if isinstance(content, str):
            if len(content) > CONTENT_PREVIEW:
                content = content[:CONTENT_PREVIEW - 3] + '...'
            print("    ")
            for line in content.split('\n'):
                print(line.strip(), end="" if line.endswith('...') else r"\n")
            print()


def get_file(url, log=False):
    """
    Get and read a file. Exceptions shall be caught in a higher scope.
    """
    url = url.replace("/", "\\").replace("%20", " ")
    content_type = get_content_type(url)
    if not url.startswith('\\'):
        url = '\\' + url
    abs_path = os.path.abspath(os.path.dirname(__file__))
    if log:
        print(f"Opening file {underline}" + (url + f"{end}").ljust(25) + f'    ',
              "textual  " if content_type.startswith("text") else "binary   ", content_type.split(';')[0])
    if content_type.startswith("text"):
        file = open(abs_path + url, 'r', encoding="utf-8")
    else:
        file = open(abs_path + url, 'rb')
    try:
        content = file.read()
    except UnicodeDecodeError:
        content = bytes()
    file.close()
    return content


def get_content_type(url):
    """
    Find the valid content type for a requested resource.
    """
    try:
        return types_dict[url.split(".")[-1]]
    except KeyError:
        return "text/plain"


def isforbidden(url) -> bool:
    """A few files will return 403 Forbidden error. Returns a boolean."""
    return url.endswith('.py') or url.endswith('.pyc') or url.endswith('.bat') or url.endswith('.md') \
            or url.endswith('.bak') or url.startswith('.vscode') or url.startswith('__pycache__') or url.startswith('dicts')


def send_file(url, version, client, *, log=False, headers={}, replacements=dict()):
    """
    Send a resource as HTTP response.
    """
    try:
        if isforbidden(url):
            reply(client, version, 403, get_403_page(url), content_type="text/html")
        else:
            content_type = get_content_type(url)
            content = get_file(url, log=not MINIMAL_PRINTING)
            if isinstance(replacements, dict):
                for key, value in replacements.items():
                    content = content.replace(key, value)
            else:
                print(f"{yellow}WARNING:{end} http_util.send_file(...replacements -> not a dict)")
            reply(client, version, 200, content, content_type, headers=headers)
    except (FileNotFoundError, OSError):
        if url.endswith('.json'):
            reply(client, version, 404, r"{}", content_type="text/plain")
        else:
            reply(client, version, 404, get_404_page(url), content_type="text/html")


def parse_query(query: str):
    """
    Turn the query of a request (after a `?`) to a dictionary.
    """
    query = query.split('&')
    query_dict = {}
    for parameter in query:
        if '=' in parameter:
            parameter = parameter.split('=')
            query_dict[parameter[0]] = parameter[1]
        else:
            query_dict[parameter] = ""
    return query_dict


def parse_cookie(cookie: str):
    """
    Turn the cookie of a request (inside an header) to a dictionary.
    """
    cookie = cookie.split(';')
    cookie_dict = {}
    for parameter in cookie:
        if '=' in parameter:
            parameter = [x.strip() for x in parameter.split('=')]
            cookie_dict[parameter[0]] = parameter[1]
        else:
            cookie_dict[parameter] = ""
    return cookie_dict


def get_header(headers: list[tuple[str, str]], header: str):
    """
    Get a header from `headers` without errors.
    """
    for name, value in headers:
        if name == header:
            return value
    return ""


def get_query(queries, want):
    """
    Get a query from `queries` dictionary without errors.
    """
    for name, value in queries.items():
        if name == want:
            return value
    return ""
    

def save_file(name, content, binary=False):
    """Save some content to a file.
    Example: http.save_file(parse_query(query)["file-name"], content);"""
    abs_path = os.path.abspath(os.path.dirname(__file__)) + "\\uploads"
    extend = name.split('.')[-1]
    name = name[:len(name) - len(extend) - 1]
    count = 0
    
    while True:
        count += 1
        path = abs_path + "\\" + name + str(hex(count)[2:].upper()) + '.' + extend
        if not os.path.isfile(path):
            break
        
    try:
        file = open(path, "wb" if binary else "w")
        file.write(content)
        file.close()
        return str(hex(count)[2:].upper()) if binary else True
    except OSError:
        return False


def reply_error(client, version, err_msg, err_msg_more="", status: int=200):
    try:
        page = get_file("error.html")
    except (FileNotFoundError, OSError):
        page = f"<h1 style=\"font-family: sans-serif;\"><span style=\"color: red;\">Form Error</span> ERROR - EXPLAIN</h1>"
    reply(client, version, status, page.replace('/* PALETTE */', get_file('css/palette.css', log=False)).replace("NUM", str(status) if status != 200 else "400").replace("TITLE", codes.status[status][0] if status != 200 else "Form Failure").replace("ERROR", err_msg).replace("EXPLAIN", err_msg_more), content_type="text/html")


def start(*, ip='0.0.0.0', port=80):
    """Create and return a socket object (server) sutible for this library."""
    try:

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((ip, port))
        server.listen()
        if ip == '0.0.0.0':
            print(f"{green}Server is listening from {bold}{underline}{socket.gethostbyname(socket.gethostname())}:{str(port)}{end}")
        else:
            print(f"{green}Server is listening to {bold}{underline}{ip}{end}{green} from {bold}{underline}{socket.gethostbyname(socket.gethostname())}:{str(port)}{end}")

    except OSError:
        print(f"{red}{bold}Could not initialise server.{end}")
        print(f"{red}Perhaps there's already an instance running?{end}\n\n")
        raise

    return server


class HTTPException(Exception):
    pass


if __name__ == '__main__':
    print("This module contains a few utilities for handling HTTP with python+socket.")
    print("    - (constant) CRLF: str")
    print("    - (constant) RESPONSE_CONTENT_SNIPPET: bool")
    print("    - (constant) types_dict: dict[str, str]")
    print("    - (function) parse_HTTP_request(req: str) -> tuple[str, str, str, str, list[tuple[str, str]], str]")
    print("    - (function) print_HTTP_request(method, url, query, version, headers, content)")
    print("    - (function) create_HTTP_response(version, status, content_type, content, headers={})")
    print("    - (function) print_HTTP_response(response, istext)")
    print("    - (function) get_404_page(url)")
    print("    - (function) get_403_page(url)")
    print("    - (function) requested(client) -> tuple[str | bool, str | bool, str | bool, str | bool, list[tuple[str, str]] | bool, str | bool]")
    print("    - (function) reply(client, version, status, content, content_type=\"text/plain\", headers={})")
    print("    - (function) get_file(url, log: bool)")
    print("    - (function) get_content_type(url)")
    print("    - (function) isforbidden(url) -> bool")
    print("    - (function) send_file(url, version, client, *, log=False, headers={}, replacements=dict())")
    print("    - (function) parse_query(query: str)")
    print("    - (function) parse_cookie(cookie: str)")
    print("    - (function) get_header(headers: list[tuple[str, str]], header: str)")
    print("    - (function) get_query(queries, want)")
    print("    - (function) save_file(name, content, binary=False)")
    print("    - (function) reply_error(client, version, err_msg, err_msg_more=\"\", status: int)")
    print("    - (function) start(*, ip='0.0.0.0', port=80)")
    print("    - (exception) HTTPException")
