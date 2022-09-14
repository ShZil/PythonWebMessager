import glob
import json
import random
import sys

import http_util as http
from my_colors import *
from settings import *
from FileDict import _hashing

__author__ = 'Shaked Dan Zilberman'


def get_time() -> tuple[str, str]:
    """Return current time & date in `(HH:MM, YYYY-mm-dd)` format."""
    import datetime
    now = datetime.datetime.now()
    year = '{:04d}'.format(now.year)
    month = '{:02d}'.format(now.month)
    day = '{:02d}'.format(now.day)
    hour = '{:02d}'.format(now.hour)
    minute = '{:02d}'.format(now.minute)
    return f"{hour}:{minute}", f"{year}-{month}-{day}"


def print_message(user: str, content: str, dst: str) -> None:
    """Prints ASCII art of a chat bubble containing `content`;
    with `user` and `chat` above and below respectively, with appropriate padding."""
    back = '\\'
    N = 59
    content = [content[i:i+N] for i in range(0, len(content), N)]
    lines = []
    for line in content:
        lines.extend(line.split('\n'))
    if len(lines) > 10:
        lines = lines[:10]
        lines.append('...')
    lines = [line.ljust(N) for line in lines]
    content = '\n'.join([f"        | {line} |" for line in lines])
    dst = ('→' + dst[:11]).center(11)
    print(f"""\"{user}\" says:
          ___________________________________________________________
         /                                                           {back}
{content}
         {back}__  _______________________________________________________/
            {back}/
        {dst}""")


### Interaction with users' info ###
def user_token(username: str, depth: int = 0) -> str:
    """Selects and saves a random 32 characters long ASCII/HEX string; NOT returns from cache if exists."""
    if depth > 10:
        print(f"{red}Practical Impossibility.{end}")
        return ""
    # if username in tokens:
    #     return tokens[username]
    # random.seed(username)
    token = ''.join(random.choices(token_chars, k=32))
    if token in tokens.values():
        return user_token(username, depth+1)
    try:
        tokens[username] = tokens[username].split('+')[1] + '+' + token
    except KeyError:
        tokens[username] = '+' + token
    return token


def add_user(username: str, password: str) -> None:
    """Adds a new `(username, password)` pair."""
    users[username] = password


def is_user(username: str) -> bool:
    """Answers 'Is there a user with this `username`?'"""
    return username in users


def correct_password(username: str, password: str) -> bool:
    """Returns whether the password matches the username."""
    return users.correct(username, password)

    
def get_user_by_cookie(cookie: str) -> str:
    """Get a username according to a cookie token.
    Returns `""` if not found, string of the name if found."""
    for user, token in tokens.items():
        if cookie in token.split('+'):
            t = ' '.join(reversed(list(get_time())))
            lastSeen[user] = t
            return user
    return ""


def get_user_by_headers(headers: list[tuple[str, str]]) -> str:
    """Wrapper for get_user_by_cookie.
    Get a username according to a cookie token.
    Returns `""` if not found, string of the name if found."""
    return get_user_by_cookie(http.parse_cookie(http.get_header(headers, "Cookie"))["token"])


def token_exists(token: str) -> bool:
    """Answers 'Is there a user associated with this token?'"""
    everyone = [token.split('+') for token in tokens.values()]
    return token in [token for l in everyone for token in l]


def mutual_chats(user1: str, user2: str) -> list:
    """Returns a list containing the titles of all chats,
    where `user1` and `user2` participate.
    If no chats are found, returns `["None"]`.
    If `user1 == user2`, returns `["All"]`"""
    if user1 == user2: return ["All"]
    mutuals = []
    try:
        for path in glob.glob("chats/*.json"):
            with open(path, 'r') as f:
                document = json.loads(f.read())
                members = document["members"]
                if user1 in members and user2 in members:
                    mutuals.append(document["title"])
    except (OSError, FileNotFoundError):
        pass
    return mutuals if len(mutuals) > 0 else ["None"]


def can_chat(username: str, chat: str) -> bool:
    """Returns a boolean specifing whether a user can send a message in a specific chat.
    (A chat should be the id from the path: `chats/{chat}.json`)"""
    try:
        document = http.get_file(f'chats/{chat}.json')
    except (FileNotFoundError, OSError):
        return False
    document = json.loads(document)
    return username in document["members"] or document["members"] == ["*"]


### Disable / Enable console output ###
def unprint() -> None:
    sys.stdout = open(os.devnull, 'w')


def reprint() -> None:
    sys.stdout = sys.__stdout__


if __name__ == '__main__':
    print("This is a module for general utilities.")
    print("    - (function) get_time() -> tuple[str, str]")
    print("    - (function) print_message(user: Any, content: Any, dst: str) -> None")
    print("    - (function) user_token(username: str, depth: int = 0)")
    print("    - (function) add_user(username: str, password: str) -> None")
    print("    - (function) is_user(username: str) -> bool")
    print("    - (function) correct_password(username: str) -> str")
    print("    - (function) get_user_by_cookie(cookie: str) -> str")
    print("    - (function) get_user_by_headers(headers: list[tuple[str, str]]) -> str")
    print("    - (function) token_exists(token: str) -> bool")
    print("    - (function) mutual_chats(user1: str, user2: str) -> list")
    print("    - (function) can_chat(username: str, chat: str) -> bool")
    print("    - (function) unprint() -> None")
    print("    - (function) reprint() -> None")

    # print_message("Shaked", "I'm sending a message\nHello world!", "chat20")
