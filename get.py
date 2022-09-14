import json

import http_util as http
from my_colors import *
from settings import *
from util import *

__author__ = "Shaked Dan Zilberman"


def send_main_html(client, version, headers) -> None:
    """Sends `main.html` to client. Assumption: cookie is verified."""
    user = get_user_by_headers(headers)
    new_token = user_token(user)
    http.send_file('main.html', version, client, headers={"Set-Cookie": "token=" + new_token}, replacements={"USERNAME HERE": user}, log=False)


def send_chat(client, version, url, headers, log=False) -> None:
    """Sends a filtered JSON chat to a client.
    Assumption: cookie is checked."""
    try:
        document = http.get_file(f"/chats/{url}.json")
    except (FileNotFoundError, OSError):
        http.reply(client, version, 404, "Could not find chat")
        return
    user = get_user_by_headers(headers)
    chat = url.strip('/').strip('.json')
    if not can_chat(user, chat):
        http.reply(client, version, 403, "Access to this chat is forbidden to you.")
        return
    document = json.loads(document)
    for i in range(len(document["messages"])):
        document["messages"][i] = {k: document["messages"][i][k] for k in ('author', 'time', 'content')}
    http.reply(client, version, 200, json.dumps(document, indent=4))


def send_chats(client, version, headers, log=True) -> bool:
    """Sends all chats a user is allowed access to.
    Assumption: cookie is checked.
    Returns `True` if finished execution, `False` if an error occured."""
    allowed = []
    user = get_user_by_headers(headers)
    if user == "":
        http.reply(client, version, 403, "Could not identify user. Try to log in again?")
        return False
    for chat, title in chats.items():
        if can_chat(user, chat):
            allowed.append(f"{chat}={title}")
    http.reply(client, version, 200, '\n'.join(allowed))
    return True


def send_user(client, version, headers, url) -> None:
    """Sends `main.html` to client. Assumption: cookie is verified."""
    from urllib.parse import unquote as decodeURL

    user = get_user_by_headers(headers)
    name = decodeURL(url.split('/user/')[1])
    if name not in users:
        http.reply_error(client, version, "User doesn't exist.", "Check for typos?", status=404)
        return
    try:
        last_seen = lastSeen[name]
    except KeyError:
        last_seen = "Never"
    http.send_file('user.html', version, client, replacements={
        "CLIENTNAME": user,
        "USERNAME": name,
        "LASTSEEN": last_seen,
        "MUTUAL": "<li>" + "</li>\n<li>".join(mutual_chats(user, name)) + "</li>"
    })


if __name__ == '__main__':
    print("This file stores methods for handling GET requests.")
    print("    - (function) send_main_html(client, version, headers)")
    print("    - (function) send_chat(client, version, url, headers, log=False)")
    print("    - (function) send_chats(client, version, headers, log=True)")
    print("    - (function) send_user(client, version, headers, url)")
