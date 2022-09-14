import os

import http_util as http
from get import *
from post import *
from my_colors import *
from settings import *
from util import *

### Pre-initialisation ###
__author__ = "Shaked Dan Zilberman"


for folder in FOLDERS: os.makedirs(folder, exist_ok=True)


### Flow Control Logic (main methods) ###
def handle_GET(client, version, headers, url, query, content, log=False):
    """Handles a GET request from a client.
    if `url == '/'`, and cookie is verified, send `main.html`.
    if a query action was defined in `http.queries`, apply it via `http.operate(...)`.
    if `url == '/main.html'` and cookie is unverified, send error.
    if `url.startswith("/chats/")`, check the cookie and send only wanted data.
    In all other cases, send the requested file."""
    
    cookie = verify_cookie(client, version, headers, res=False, log=False)
    
    # Route homepage requests (`GET / HTTP/1.1`):
    if url == '/':
        url = '/main.html' if cookie else '/index.html'
    
    # Preform checks on private / restricted content:
    if url == '/chats':
        if not verify_cookie(client, version, headers, log=False):
            if not MINIMAL_PRINTING: print(f"{red}Asked for the chats with an invalid cookie.{end}")
            return
        send_chats(client, version, headers, log=True)
        return
    
    if url.startswith('/chats/chat'):
        if not cookie:
            if not MINIMAL_PRINTING: print(f"{red}Asked for a chat with an invalid cookie.{end}")
            http.reply(client, version, 301, "Your cookie isn't updated. Refresh the page.", headers={"Set-Cookie": f"token=", "Location": "/"})
            return
        if not can_chat(get_user_by_headers(headers), url[len('/chats/'):][:len('.json')]):
            print(f"{red}not a participant{end}" if MINIMAL_PRINTING else f"{red}Asked for a chat but isn't participating in it.{end}\n", end="")
            http.reply(client, version, 403, "You do not have access to this chat.")
            return
    
    # Authorisation of access:
    if url == "/main.html":
        if cookie:
            send_main_html(client, version, headers)
        else:
            http.reply_error(client, version, "Unauthorised Access.", "In the address bar, remove the part that says <code>main.html</code> only.", status=401)
        return
    
    if url.startswith('/user/'):
        if cookie:
            send_user(client, version, headers, url)
        else:
            http.reply_error(client, version, "Unauthorised Access.", "In the address bar, remove the part that says <code>/user/...</code> only.", status=401)
        return
    
    # If no special action is found, it's a file request
    url = url.strip('/')
    folder = get_folder(url)
    http.send_file(f"{folder}/{url}", version, client)


def handle_POST(client, version, headers, url, query, content, log=False):
    """Handles a POST request from a client."""
    binary = ['/media']
    form = ['/signup', '/login']
    textual = ['/message', '/invite', '/quit', '/create', '/delete']

    try:
        length = int(http.get_header(headers, "Content-Length"))
    except ValueError:
        http.reply(client, version, 411, "Invalid Content Length.")
        return

    if log and not MINIMAL_PRINTING: print(f"POST pre-content (Length={len(content)}): {content}")

    try:

        if url in binary:
            if log: print(f"Binary contents")
            return act(url, client, version, headers, query, content, length, None, log=False)

        content = safe_recv(client, length, content, timeout=2)
        print_POST_content(content, log)

        if url in form:
            form_data = http.parse_query(content.replace('+', ' '))
            if not act(url, client, version, headers, query, content, length, form_data, log=False):
                if log and not MINIMAL_PRINTING: print(f"          {green}login/signup was successful.{end}")
                token = user_token(form_data["username"])
                send_refresh_page(client, version, token)
        
        elif url in textual:
            return act(url, client, version, headers, query, content, length, None, log=False)

        else:
            raise NotImplementedError("Unrecognised POST action")
        
    except KeyError:
        if log: print(f"{red}invalid <form> info{end}" if MINIMAL_PRINTING else f"          {red}invalid information sent in form{end}")
        http.reply_error(client, version, "Sorry, something went wrong.", "HTML<form> is invalid. Try again :)")
        return
    
    except NotImplementedError:
        unknown_POST_error(client, version)


def act(url, client, version, headers, query, content, length, form_data, log):
    """Chooose a POST request to act on. Return the value from the action."""
    match url:
        case '/media':
            return do_media(client, version, query, headers, length, content, log)
        case '/signup':
            return do_signup(client, version, form_data)
        case '/login':
            return do_login(client, version, form_data)
        case '/message':
            return do_message(client, version, query, headers, content, log)
        case '/invite':
            return do_invite(client, version, query, headers, log)
        case '/quit':
            return do_quit(client, version, query, headers, log)
        case '/create':
            return do_create(client, version, headers, content)
        case '/delete':
            return do_delete(client, version, headers)
        case _:
            raise NotImplementedError("Unrecognised POST action.")
            

def main():
    """La méthode main()"""
    server = http.start(ip=ADDRESS, port=PORT)

    while True:
        try:
            (client, (ip, port)) = server.accept()
            print_connection(ip, port)

            method, url, query, version, headers, content = http.requested(client)

            if not method:
                handle_bad_request(client)
                client.close()
                continue

            reprint()
            if not PRINT_GET and method == 'GET':
                unprint()

            print_start_line(method, url, query, version)
            verify_cookie(client, version, headers, res=False, log=True)

            # http.print_HTTP_request(method, url, query, version, headers, content)
            
            if method == 'POST': handle_POST(client, version, headers, url, query, content, log=True)
            elif method == "GET": handle_GET(client, version, headers, url, query, content, log=False)
            else:
                print(f"{red}Invalid method: '{method}'{end}")
                http.reply(client, version, 501, 'Unknown Method')
                client.close()
        except (ConnectionAbortedError, ConnectionRefusedError, ConnectionResetError, InterruptedError):
            print(f"{orange}Unexpectedly disconnected.{end}")
        except (OSError, FileNotFoundError, FileExistsError) as error:
            print(f"\n{red}{error}{end}")
            print(f"{orange}Fatal OS/FileSystem error.{end}")
            http.reply(client, version, 500, "Fatal OS/FileSystem error.")
        except KeyboardInterrupt:
            print(f"{orange}(^C){end}")
        except:
            print(f"{orange}Exception.{end}")


### Simplify Flow Control Logic's methods ###
def print_connection(ip, port) -> None:
    """Prints the details of a connection. Uses `gray` colour.
    Printing follows format of `"From ip:port"` or `"Connected to ip:port"`.
    If ip is 127.0.0.*: write localhost instead.
    If port is shorter than 5 characters, zero-fill."""
    ip = str(ip)
    port = str(port)

    if ip.startswith('127.0.0.'): ip = 'localhost'
    if MINIMAL_PRINTING:
        print(f"{gray}From {underline}{ip.rjust(-1)}:{port.zfill(5)}{end}", end=" ")
    else:
        print(f"{gray}Connected to {underline}{ip}:{port}{end}")


def print_start_line(method: str, url: str, query: str, version: str) -> None:
    """Prints the start line of an HTTP request.
    It follows the format: `~> METHOD /url?query HTTP/version`.
    If query is empty `""`, don't show question mark `?`.
    Pad the print statement with spaces to the right, if its length is less than 60."""
    method_color = red
    if method == 'GET': method_color = green;
    if method == 'POST': method_color = magenta
    title = f"~> {method_color}{method} {cyan}{url}{'' if query == '' else '?'}{query} {yellow}{version}{end}"
    print(title, end=" " * abs(60 - len(title)))


def handle_bad_request(client):
    """Handles a bad request that could not be parsed:
    1. Prints in red `"Failed HTTP request"`.
    2. Replies to the client with a `400 Bad Request` response."""
    print(f"{red}Failed HTTP request{end}                    ", end=" " if MINIMAL_PRINTING else "\n")
    http.reply(client, "HTTP/1.1", 400, "Bad Request sent.")


def get_folder(url: str) -> str:
    """
    File system routing. Select the matching folder for a requested resource `url`.
    * Doesn't route those with a `/`, because they know exactly what they're looking for.
    * Files ending with `.js` or `.css` go to folders `/js/` and `/css/` respectively.
    * Files ending with `.png` or `.ico` go to `/images/`, because they're server-wide images.
    * Otherwise, send everyone to folder `''` (path determined only by url).
    """
    if url.count('/') > 0: return ''
    extension = url.split('.')[-1]
    if extension == 'js': return '/js'
    if extension == 'css': return '/css'
    if extension in ['png', 'ico']: return '/images'
    return ''


def print_POST_content(content: str, log=True) -> None:
    """Print content sent in POST request.
    `N: int = 17` is the max number of rendered characters.
    Appends ellipsis (`...`) if too long."""
    N: int = 17
    print_content: str = content if len(content) <= N else content[:N - 3] + '...'
    print_content = print_content.replace('\n', '\\n').replace('\r', '\\r')
    if log: print(f"\"{print_content}\"" if MINIMAL_PRINTING else f"POST Content: {print_content}")


if __name__ == '__main__':
    main()
