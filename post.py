import socket
import time
import http_util as http
from my_colors import *
from settings import *
from util import *

__author__ = 'Shaked Dan Zilberman'


### POST requests ###
def do_signup(client, version, form_data):
    """Signs up a user.
    If any error occurs, sends an error message and returns True; else returns False.
    KeyError exceptions (invalid form) shall be caught in a higher scope."""
    username = form_data["username"].replace('+', ' ').strip()
    password = form_data["password"]
    confirmation = form_data["password2"]
    start = red if MINIMAL_PRINTING else f"          {red}"
    if username == "" or password.strip() == "":
        print(start, f"username or password are empty {end}")
        http.reply_error(client, version, "Username or Password are empty.", "You have to fill both fields. And no sneaky 'whitespace-only' stuff!")
        return True
    if username.lower() in prohibited_usernames:
        print(start, f"username prohibited            {end}")
        http.reply_error(client, version, "Username is prohibited.", "Please try another username!")
        return True
    if ':' in username:
        print(start, f"username prohibited            {end}")
        http.reply_error(client, version, "Username is prohibited.", "Do not use colons in your username!")
        return True
    if '@' in username:
        print(start, f"username prohibited            {end}")
        http.reply_error(client, version, "Username is prohibited.", "Do not use @ in your username!")
        return True
    if username.endswith('chats'):
        print(start, f"username prohibited            {end}")
        http.reply_error(client, version, "Username is prohibited.", "Username cannot end with \"chats\"!")
        return True
    if ':' in password:
        print(start, f"password prohibited            {end}")
        http.reply_error(client, version, "Password is prohibited.", "Please try another password, without colons!")
        return True
    if password != confirmation:
        print(start, f"password != password2          {end}")
        http.reply_error(client, version, "Password confirmation is incorrect.", "You need to enter the same password twice.")
        return True
    if len(username) > 25:
        print(start, "username too long")
        http.reply_error(client, version, "This username is too long!", "25 characters max.")
        return True
    if is_user(username):
        print(start, f"signup but user already exists {end}")
        http.reply_error(client, version, "This user already exists.", "Try logging in or choose a different username.")
        return True
    print(f"{green}User signup: {end}{underline}{username}{end}  {underline}{'*' * len(password)}{end}")
    add_user(username, password)
    return False


def do_login(client, version, form_data):
    """Verifies a user login.
    If any error occurs, sends an error message and returns True; else returns False.
    KeyError exceptions (invalid form) shall be caught in a higher scope."""
    username = form_data["username"].strip()
    password = form_data["password"]
    start = red if MINIMAL_PRINTING else f"          {red}"
    if not is_user(username):
        print(start, f"login but user don't exist {end}")
        http.reply_error(client, version, "This user doesn't exists.", "Did you spell the username right?")
        return True
    if not correct_password(username, password):
        print(start, f"login but wrong password   {end}")
        http.reply_error(client, version, "Password is incorrect.", "Did you type it right?")
        return True
    print(f"{green}Login successful by{end} {underline}{username}{end}")
    return False


def do_create(client, version, headers, content):
    if do_create_process(client, version, headers, content):
        print(f"{green}Created chat!{end}")
    else:
        print(f"{red}Failed to create chat.{end}")


def do_create_process(client, version, headers, content) -> bool:
    """
    Act on a `POST /create` request. Creates a new chat.
    KeyError exceptions shall be caught in a higher scope.
    Returns whether chat creation was successful.
    """
    form_data = http.parse_query(content)
    # print("FORM DATA", form_data)
    title = form_data['title']
    description = form_data['description']
    if not title.isascii():
        print(f"          {red}create chat but title isn't ascii{end}")
        http.reply_error(client, version, "You cannot create a chat with non-ASCII title", "Use only ASCII characters!")
        return False
    try:
        private = form_data['private'] == "true"
    except KeyError:
        private = False
    if title.strip() == '':
        print(f"          {red}create chat but title is empty{end}")
        http.reply_error(client, version, "You cannot create a chat without a title.", "Try to... write a title. And no sneaky 'whitespace-only' stuff!")
        return False
    if title.strip().lower() in prohibited_titles:
        print(f"          {red}create chat but title is prohibited{end}")
        http.reply_error(client, version, "You cannot create a chat with this title.", "Try to write another title.")
        return False
    if not verify_cookie(client, version, headers, log=False):
        return False
    members = [get_user_by_headers(headers)]
    if private:
        members.extend(title.strip("Chat between ").split(' and '))
        members = list(set(members))
    # Select ID
    try:
        last = chats.items()[-1][0]
    except (FileNotFoundError, OSError):
        print(f"{red}Could not open chats.txt{end}")
        http.reply(client, version, 500, "Could not create chat; fatal server error")
        return False
    except IndexError:
        last = "chat0"
    try:
        id = int(last[4:]) + 1
    except ValueError:
        print(f"{red}last chat's ID \"{last[4:]}\" is not int{end}")
        http.reply(client, version, 500, "Could not create chat; fatal server error")
        return False
    # Create /chats/chat{id}.json
    info = {
        "id": f"chat{id}",
        "title": title,
        "description": description,
        "private": private,
        "members": members,
        "messages": []
    }
    if private:
        if (members[0] + '&' + members[1]) in couples.values():
            http.reply(client, version, 400, "Private chat between you two already exists.")
            return False
        couples[f"chat{id}"] = members[0] + '&' + members[1]
    try:
        with open(f"chats/chat{id}.json", "x") as file:
            file.write(json.dumps(info, indent=4))
    except FileExistsError:
        print(f"{red}chat{id}.json already exists. chats is unupdated?{end}")
        if update_chats():
            return do_create(client, version, headers, content)
        http.reply(client, version, 500, "Could not create chat; It already exists?!")
        return False
    # Add to chats.txt
    try:
        chats[f"chat{id}"] = title
    except (FileNotFoundError, OSError):
        print(f"{red}Could not open chats.txt{end}")
        http.reply(client, version, 500, "Could not create chat; fatal server error")
        return False
    # Add message "Created chat on blah blah blah".
    add_message(f"chat{id}", "Server", f"Chat created at {get_time()[0]} by @{members[0]}.", log=False)
    http.reply(client, version, 201, f"chat{id}; Chat created.")
    return True


def do_message(client, version, query, headers, content, log=True):
    """
    Act on a `POST /message` request.
    """
    chat = http.get_query(http.parse_query(query), "dst")
    if chat == "":
        if log: print("NO CHAT")
        return
    if not verify_cookie(client, version, headers, res=False, log=False):
        print("Unknown user")
        http.reply(client, version, 404, "Message not appended.")
        return
    username = get_user_by_headers(headers)
    if username == "":
        print("Unknown user.")
        http.reply(client, version, 404, "Message not appended.")
        return
    if not can_chat(username, chat):
        print("User's access to chat denied.")
        http.reply(client, version, 403, "Access to chat denied.")
        return
    print_message(user=username, content=content, dst=chat)
    if not add_message(chat, username, content):
        http.reply(client, version, 404, "Message not appended.")
        return
    http.reply(client, version, 201, "Message appended.")


def do_media(client, version, query, headers, length, content, log=True):
    """
    Act on a `POST /media` request.
    """
    content = safe_recv_binary(client, length, timeout=15)
    # print('len(content)=', len(content))
    chat = http.get_query(http.parse_query(query), "dst")
    if chat == "":
        if log: print("NO CHAT")
        return
    if not verify_cookie(client, version, headers, res=False, log=False):
        print("Unknown user")
        http.reply(client, version, 404, "Message not appended.")
        return
    username = get_user_by_headers(headers)
    if username == "":
        print("Unknown user.")
        http.reply(client, version, 404, "Message not appended.")
        return
    if not can_chat(username, chat):
        print("User's access to chat denied.")
        http.reply(client, version, 403, "Access to chat denied.")
    if add_media(client, version, headers, username, chat, content, log=True):
        http.reply(client, version, 201, "Message appended.")
        return


def add_media(client, version, headers, username, chat, content, log=True) -> bool:
    """Finished uploading an image after all the security checks of `do_media`.
    Returns boolean indicating success."""
    # Remove HTTP multipart/form-data head and tail from the content
    try:
        boundary = b'\r\n--' + http.get_header(headers, "Content-Type").split('; ')[1][len("boundary="):].encode()
        head, content = tuple(content.split(b'\r\n\r\n', 1))
        content, tail = tuple(content.split(boundary, 1))
        # `head` is formatted similar to HTTP headers
        head = [line.split(':', 1) for line in head.decode().split(http.CRLF)[1:]]
        head = [(header[0], header[1].strip()) for header in head]
        # Two headers are expected
        disposition = http.get_header(head, "Content-Disposition")
        content_type = http.get_header(head, "Content-Type")
        extension = ".png" if content_type == 'image/png' else ".jpg"
        disposition = [couple.split('=') for couple in disposition.split(';')[1:]]
        disposition = [(couple[0].strip(), couple[1].strip().strip("\"")) for couple in disposition]
        filename = http.get_header(disposition, "filename")
        length = len(content)
        if length == 0:
            if log: print("Empty image uploaded.")
            http.reply(client, version, 400, "Image cannot be empty.")
            return False
        index = http.save_file("img" + extension, content, binary=True)
    except (ValueError, IndexError):
        if log: print("Error when uploading image.")
        http.reply(client, version, 400, "Critical parsing error in uploading image.")
        return False
    if index == False:
        if log: print("File system error when uploading image.")
        http.reply(client, version, 404, "Critical server error in uploading image.")
        return False
    print_message(user=username, content=f"<Media uploaded> {filename} -> uploads/img{index}{extension} ({length} bits)", dst=chat)
    return add_message(chat, username, f"uploads/img{index}{extension}", img=True, filename=filename)


def do_invite(client, version, query, headers, log=False):
    """
    Act on a `POST /invite` request.
    """
    chat = http.get_query(http.parse_query(query), "dst")
    user = http.get_query(http.parse_query(query), "user")
    if chat == "":
        if log: print("NO CHAT")
        return
    
    if not verify_cookie(client, version, headers, res=False, log=False):
        if log: print("Unknown user")
        http.reply(client, version, 400, "Unknown user. Please refresh, then log in / sign up.")
        return
    username = get_user_by_headers(headers)

    if username == "":
        if log: print("Unknown user.")
        http.reply(client, version, 400, "Unknown user. Please refresh, then log in / sign up.")
        return

    if not can_chat(username, chat):
        if log: print("User's access to chat denied.")
        http.reply(client, version, 403, "Access to this chat denied.")
        return
    
    res = add_member(chat, user)
    if res == "":
        http.reply(client, version, 200, "User successfully invited.")
    elif res == "User doesn't exist.":
        past_chat = 0
        for chat_id, title in chats.items():
            if title == user:
                past_chat = chat_id
                break
        if past_chat == 0:
            http.reply(client, version, 404, res)
        else:
            do_invite_all(client, version, past_chat, chat, username, log=log)
    else:
        http.reply(client, version, 404, res)


def do_invite_all(client, version, past_chat, chat, username, log=False):
    """Invites all members of a past chat `past_chat` to a new one `chat`,
    as if invited by `username`."""
    if not can_chat(username, past_chat):
        if log: print("User's access to chat denied.")
        http.reply(client, version, 403, "Access to this chat denied.")
        return
    
    try:
        f = http.get_file(f'chats/{past_chat}.json')
        document = json.loads(f)
    except (FileNotFoundError, OSError):
        if log: print("Past chat not found.")
        http.reply(client, version, 403, "Past chat not found.")
        return
    
    error_res = ''
    for member in document["members"]:
        res = add_member(chat, member)
        if res not in ["", "User is already in the chat."]:
            error_res += res + " "
    if error_res == '':
        http.reply(client, version, 200, "Users successfully invited.")
    else:
        http.reply(client, version, 404, error_res)


def do_quit(client, version, query, headers, log=False):
    """
    Act on a `POST /quit` request.
    """
    chat = http.get_query(http.parse_query(query), "dst")
    if chat == "":
        if log: print("NO CHAT")
        return
    if verify_cookie(client, version, headers, res=False, log=False):
        username = get_user_by_headers(headers)
        if username == "":
            if log: print("Unknown user.")
            return
        res = remove_member(chat, username)
        if res == "":
            http.reply(client, version, 200, "You successfully exited the group. The page will now refresh.")
        else:
            http.reply(client, version, 404, res)
        return
    else:
        if log: print("Unknown user")
    http.reply(client, version, 400, "Unknown user. Please refresh, then log in / sign up.")


def get_last_message(messages, by, back=30):
    """Returns the latest message sent in `messages` by user `by`.
    Returns `{author: "", time: "", date: "", content: ""}` if not found.
    Only checks `back` (default: 30) most recent messages."""
    for message in list(reversed(messages))[:back]:
        if message["author"] == by:
            return message
    return {'author': "", 'time': "", 'date': "", 'content': ""}


def add_message(chat, username, content, img=False, log=True, filename=""):
    """Save a message to the database: from `username`, on `chat`, containing `content`.
    Time is calculated server-side.
    If message is successfully added, returns `True`. Else -- `False`.
    If `log=True`, prints red error messages or green success message."""
    try:
        document = http.get_file(f'chats/{chat}.json')
        document = json.loads(document)
        last_message = get_last_message(document["messages"], by=username)
        time, date = get_time()
        if last_message["content"] == content and last_message["time"] == time:
            # You cannot send a message with identical content at the same minute.
            # Prevents intentional and accidental douplicates
            if log: print(f"{red}Message was already sent.{end}")
            return False
        document = add_date_if_needed(document, date)
        document["messages"].append({
            "author": username,
            "time": time,
            "date": date,
            "content": content
        })
        if img:
            document["messages"][-1]["img"] = True
            document["messages"][-1]["filename"] = filename
        f = open(f'chats/{chat}.json', "w")
        f.write(json.dumps(document, indent=4))
        f.close()
        if log: print(f"{green}Successfully appended message.{end}")
        return True
    except (OSError, FileNotFoundError):
        if log: print(f"{red}Message failed.{end}")
        return False


def add_date_if_needed(document, date):
    if len(document["messages"]) == 0 or document["messages"][-1]["date"] != date:
        document["messages"].append({
            "author": "Day",
            "time": "00:00",
            "date": date,
            "content": date
        })
    return document


def add_member(chat, username, log=True) -> str:
    """Adds a member to a chat. This action is referred to as "inviting".
    If member is successfully added, returns `""`. Else -- returns the error messsage."""
    if username not in users:
        return "User doesn't exist."
    try:
        document = http.get_file(f'chats/{chat}.json')
        document = json.loads(document)
        if username in document["members"]:
            return "User is already in the chat."
        if document["private"]:
            return "Cannot invite others to a private chat."
        document["members"].append(username)
        f = open(f'chats/{chat}.json', "w")
        f.write(json.dumps(document, indent=4))
        f.close()
        if log: print(f"{green}Successfully invited user.{end}")
        add_message(chat, "Server", f"@{username} joined the chat.")
        return ""
    except (OSError, FileNotFoundError):
        if log: print(f"{red}Invite failed.{end}")
        return "Could not invite user."


def remove_member(chat, username, log=True) -> str:
    """Removes a member to a chat. This action is referred to as "quitting" or "exiting".
    If message is successfully removed, returns `""`. Else -- returns the error messsage."""
    if username not in users:
        return "User doesn't exist."
    try:
        document = http.get_file(f'chats/{chat}.json')
        document = json.loads(document)
        if username not in document["members"]:
            return "User already exited this chat."
        document["members"].remove(username)
        if len(document["members"]) == 0:
            os.remove(f'chats/{chat}.json')
            chats.pop(chat)
            update_chats()
            return ""
        f = open(f'chats/{chat}.json', "w")
        f.write(json.dumps(document, indent=4))
        f.close()
        if log: print(f"{green}Successfully removed user.{end}")
        add_message(chat, "Server", f"@{username} left the chat.")
        return ""
    except (OSError, FileNotFoundError):
        if log: print(f"{red}Exit failed.{end}")
        return "Could not remove user."


def safe_recv(client, length, content, timeout=5) -> str:
    """Recv from client; if not recvs within `timeout` seconds (default 5[s]), return the previous content."""
    client.settimeout(timeout)
    try:
        content += client.recv(length).decode()
    except socket.timeout:
        pass
    client.settimeout(None)
    return content


def safe_recv_binary(client, length, timeout=15):
    """Recv from client; if not recvs within `timeout` seconds (default 15[s]), return `b""`."""
    content = b''
    start = time.time()
    while len(content) < length:
        content += client.recv(length)
        if time.time() - start > timeout:
            break
    return content


def verify_cookie(client, version, headers, res=True, log=True) -> bool:
    """If cookie is valid, return true. Else, send error and return false.
    `res` defines whether to send an error response."""
    ending = f'{end}     ' if MINIMAL_PRINTING else f'{end}\n'
    msgs = {
        "success": f"{green} Valid cookie   ",
        "no cookie": f"{red} No cookie      ",
        "no token":  f"{red} No token       ",
        "bad":       f"{red} Invalid cookie "
    } if MINIMAL_PRINTING else {
        "success": f"{green}Valid cookie",
        "no cookie": f"{red}No cookies sent",
        "no token": f"{red}No cookie named token",
        "bad": f"{red}Cookie's token is not in allowed tokens"
    }
    cookies = http.get_header(headers, "Cookie")
    if cookies == '':
        if log: print(msgs["no cookie"], end=ending)
        return False
    cookie_dict = http.parse_cookie(cookies)
    if "token" not in cookie_dict:
        if log: print(msgs["no token"], end=ending)
        if res: http.reply_error(client, version, "Request must contain a token cookie.", "Try to log in / sign up again.")
        return False
    token = cookie_dict["token"]
    if not token_exists(token):
        if log: print(msgs["bad"], end=ending)
        if res: http.reply_error(client, version, "Invalid token cookie.", "Try to log in / sign up again.")
        return False
    if log: print(msgs["success"], end=ending)
    return True


def do_delete(client, version, headers) -> bool:
    """Acts on POST /delete, and deletes the user's data.
    Note: doesn't remove them as participating in chats, nor does it delete their messages.
    Returns boolean indicating success."""
    user = get_user_by_headers(headers)
    if user == '':
        http.reply(client, version, 400, "Unknown user.")
        return False
    for filedict in [users, tokens, lastSeen]:
        try:
            filedict.pop(user)
        except KeyError:
            pass
    http.reply(client, version, 200, "User deleted.")
    return True


def unknown_POST_error(client, version):
    """Reply with an error to an unrecognised POST request."""
    print(f"          {red}Unrecognised POST request;{end}")
    http.reply(client, version, 400, "Unrecognised POST request.")


def update_chats() -> bool:
    """
    Updates the chats FileDict and the couples FileDict according to the files which exist.
    Returns boolean indicating success.
    """
    try:
        chats.clear()
        couples.clear()
        for path in glob.glob("chats/*.json"):
            with open(path, 'r') as f:
                document = json.loads(f.read())
                chats[document["id"]] = document["title"]
                if document["private"]:
                    couples[document["id"]] = document["members"][0] + '&' + document["members"][1]
    except (KeyError, OSError, FileNotFoundError):
        return False
    return True


def send_refresh_page(client, version, token) -> None:
    http.reply(client, version, 301,
            "<html><head><meta http-equiv=\"refresh\" content=\"1\"></head><body>Redirecting to website...</body></html>",
            headers={"Set-Cookie": f"token={token}", "Location": "/"})


if __name__ == '__main__':
    print("This file stores methods for handling POST requests.")
    print("    - (function) do_signup(client, version, form_data)")
    print("    - (function) do_login(client, version, form_data)")
    print("    - (function) do_create(client, version, headers, content)")
    print("    - (function) do_create_process(client, version, headers, content) -> bool")
    print("    - (function) do_message(client, version, query, headers, content, log=True)")
    print("    - (function) do_media(client, version, query, headers, length, content, log=True)")
    print("    - (function) add_media(client, version, headers, username, chat, content, log=True) -> bool")
    print("    - (function) do_invite(client, version, query, headers, log=False)")
    print("    - (function) do_invite_all(client, version, past_chat, chat, username, log=False)")
    print("    - (function) do_quit(client, version, query, headers, log=False)")
    print("    - (function) get_last_message(messages, by, back=30)")
    print("    - (function) add_message(chat, username, content, img=False, log=True, filename=\"\")")
    print("    - (function) add_date_if_needed(document, date)")
    print("    - (function) add_member(chat, username, log=True) -> str")
    print("    - (function) remove_member(chat, username, log=True) -> str")
    print("    - (function) safe_recv(client, length, content, timeout=5) -> str")
    print("    - (function) safe_recv_binary(client, length, timeout=15)")
    print("    - (function) verify_cookie(client, version, headers, res=True, log=True) -> bool")
    print("    - (function) do_delete(client, version, headers) -> bool")
    print("    - (function) unknown_POST_error(client, version)")
    print("    - (function) update_chats() -> bool")
    print("    - (function) send_refresh_page(client, version, token) -> None")
