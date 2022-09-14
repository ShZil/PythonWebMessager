from FileDict import FileDict, HashedFileDict

__author__ = "Shaked Dan Zilberman"

ADDRESS: str = '0.0.0.0'
PORT: int = 8008
COLORS: bool = True
ASCII_NOT_HEX: bool = True
PRINT_GET: bool = True
MINIMAL_PRINTING: bool = True

prohibited_usernames: list[str] = ["server", "day", "*", "admin"]
prohibited_titles: list[str] = ['none', 'null', 'all', 'server']

FOLDERS: list[str] = ['chats', 'uploads', 'images', 'css', 'js', 'dicts']

# Pre-initialisation:

users = HashedFileDict("users") # FileDict {username: password}
tokens = FileDict("tokens")     # FileDict {username: token+token}
chats = FileDict("chats")       # FileDict {id: title}
couples = FileDict("couples")   # FileDict {user1: user2}
lastSeen = FileDict("lastSeen") # FileDict {user: date "YYYY-mm-dd HH:MM"}

if ASCII_NOT_HEX:
    # ASCII tokens
    token_chars: list[str] = list(set([chr(c) for c in range(ord('!'), ord('~'))]) - set([';', '=', ':', '~', '+']))
else:
    # HEX tokens
    token_chars: list[str] = [hex(i)[2:].upper() for i in range(16)]


if __name__ == '__main__':
    print("This is a module containing settins and pre-load code.")
    print("    - (constant) users: FileDict")
    print("    - (constant) tokens: FileDict")
    print("    - (constant) chats: FileDict")
    print("    - (constant) couples: FileDict")
    print("    - (constant) lastSeen: FileDict")
    print("    - (constant) prohibited_usernames: list[str]")
    print("    - (constant) prohibited_titles: list[str]")
    print("    - (constant) FOLDERS: list[str]")
    print("    - (constant) token_chars: list[str]")
    print("    - (constant) ADDRESS: str")
    print("    - (constant) PORT: int")
    print("    - (constant) COLORS: bool")
    print("    - (constant) ASCII_NOT_HEX: bool")
    print("    - (constant) PRINT_GET: bool")
    print("    - (constant) MINIMAL_PRINTING: bool")
