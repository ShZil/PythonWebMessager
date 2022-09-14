import json
from time import sleep
from FileDict import FileDict, HashedFileDict, _hashing
from util import print_message as fancy_message
from util import get_time as current_time
import os
import glob

__author__ = 'Shaked Dan Zilberman'

users = HashedFileDict("users") # FileDict {username: password}
tokens = FileDict("tokens")     # FileDict {username: token+token}
chats = FileDict("chats")       # FileDict {id: title}
couples = FileDict("couples")   # FileDict {user1: user2}
lastSeen = FileDict("lastSeen") # FileDict {user: date "YYYY-mm-dd HH:MM"}

def print_chats() -> str:
    for id, title in chats.items(): print(f"  {id} = {title}")
    chat = input('Choose chat id: ')
    if not chat.startswith('chat'): chat = 'chat' + chat
    return chat


def do_clear():
    if input("Are you sure? This will delete all data. [Y/N] ") != "Y":
        return
    users.clear()
    tokens.clear()
    chats.clear()
    couples.clear()
    lastSeen.clear()

    images = glob.glob('uploads/*')
    for f in images:
        os.remove(f)
    
    files = glob.glob('chats/*')
    for f in files:
        os.remove(f)
    
    print(f"\n{len(files) + len(images)} files were deleted:")
    print(f"    {len(files)} chats.")
    print(f"    {len(images)} images.")


def do_view():
    chat = print_chats()
    print()
    try:
        f = open(f'chats/{chat}.json', 'r')
    except (OSError, FileNotFoundError):
        print("Chat not found.")
        return
    document = json.loads(f.read())
    f.close()

    print("METADATA:")
    for datum in ['id', 'title', 'description', 'private']:
        print(f"    {datum.upper()}:", document[datum])
    
    print("    MEMBERS:")
    for member in document["members"]:
        print(f"        {member}")
        
    print("MESSAGES:")
    i = 0
    for message in document["messages"]:
        try:
            img = message["img"]
        except KeyError:
            img = False
        try:
            print(f"({i}) {message['date']}, {message['time']} - {message['author']}:", end=" ")
            if img:
                print(f"<Media omitted> {message['filename']} ->", end=" ")
            print(message['content'])
        except KeyError:
            print("[Unknown structure]".upper())
        i += 1
    f.close()


def do_update(log=True):
    chats.clear()
    couples.clear()
    for path in glob.glob("chats/*.json"):
        with open(path, 'r') as f:
            document = json.loads(f.read())
            chats[document["id"]] = document["title"]
            if document["private"]:
                couples[document["id"]] = document["members"][0] + '&' + document["members"][1]
    if log: print("Updated.")


def do_delete():
    chat = print_chats()
    if input("Are you sure you want to delete this entire chat and all linked images? [Y/N] ") != 'Y':
        return
    print(f'/chats/{chat}.json')
    print("Exists:", os.path.exists(f'./chats/{chat}.json'))
    try:
        if os.path.exists(f'./chats/{chat}.json'):
            try:
                f = open(f'./chats/{chat}.json', 'r')
                document = json.loads(f.read())
                f.close()
            # print(document)

                deletedImages = 0
                unknownImages = 0
                try:
                    for message in document["messages"]:
                        try:
                            img = message["img"]
                        except KeyError:
                            img = False
                        if img:
                            if os.path.exists('./' + message["content"]):
                                try:
                                    os.remove('./' + message["content"])
                                    deletedImages += 1
                                except (OSError, FileNotFoundError):
                                    unknownImages += 1
                except (TypeError, KeyError):
                    print("Something went wrong while deleting images.")
            except json.decoder.JSONDecodeError:
                print("Corrupted JSON.")
            for _ in range(10):
                try:
                    os.remove(f'./chats/{chat}.json')
                    break
                except PermissionError:
                    sleep(0.1)
                    continue
            print("Deleted chat.")
            print(f"    Deleted {deletedImages} image(s) referenced in chat.")
            if unknownImages > 0:
                print(f"    Failed to delete {unknownImages} image(S).")
            do_update(log=False)
        else:
            raise FileNotFoundError()
    except (OSError, FileNotFoundError):
        print("Chat not found.")
        raise


def do_remove():
    chat = print_chats()
    print()
    while True:
        index = input("Select index (if unsure, cancel and run `view`): ")
        try:
            index = int(index)
            break
        except ValueError:
            print("Not a number.")
            continue
    try:
        f = open(f'chats/{chat}.json', 'r')
    except (OSError, FileNotFoundError):
        print("Chat not found.")
        return
    document = json.loads(f.read())
    f.close()
    message = document["messages"][index]
    print("\n\n")
    fancy_message(message["author"], message["content"], chat)
    print(f"Sent on {message['date']} at {message['time']}.\n\n")
    if index < 2: print("This message is chat creation -- it's vital.", end=" ")
    if input("Are you sure you want to proceed? [Y/N] ") != "Y":
        print("Canceling.")
        return
    document["messages"].pop(index)
    try:
        f = open(f'chats/{chat}.json', 'w')
    except (OSError, FileNotFoundError):
        print("Chat not found.")
        return
    f.write(json.dumps(document, indent=4))
    f.close()
    print("Successfully deleted message")


def do_kick():
    chat = print_chats()
    print()
    name = input("Select participant: ")
    try:
        f = open(f'chats/{chat}.json', 'r')
    except (OSError, FileNotFoundError):
        print("Chat not found.")
        return
    document = json.loads(f.read())
    f.close()
    if name not in document["members"]:
        print("Participant is not in this chat.")
        return
    print("\n\n")
    if input("Are you sure you want to proceed? [Y/N] ") != "Y":
        print("Canceling.")
        return
    try:
        document["members"].remove(name)
    except ValueError:
        print("Participant is not in this chat.")
        return
    try:
        f = open(f'chats/{chat}.json', 'w')
    except (OSError, FileNotFoundError):
        print("Chat not found.")
        return
    f.write(json.dumps(document, indent=4))
    f.close()
    print("Successfully kicked user")


def do_invite():
    chat = print_chats()
    print()
    name = input("Select participant: ")
    try:
        f = open(f'chats/{chat}.json', 'r')
        document = json.loads(f.read())
        f.close()
        print("\n\n")
        document["members"].append(name)
        f = open(f'chats/{chat}.json', 'w')
        f.write(json.dumps(document, indent=4))
        f.close()
    except (OSError, FileNotFoundError):
        print("Chat not found.")
        return
    if name not in users: print("Username not recognised.")
    print("Successfully invited user")


def do_images():
    images = glob.glob('uploads\\*')
    chats = glob.glob('chats\\*')
    safe = []

    for chat in chats:
        try:
            f = open(chat, 'r')
        except (OSError, FileNotFoundError):
            print(f"Chat {chat} not found.")
            return
        document = json.loads(f.read())
        f.close()
        for message in document["messages"]:
            try:
                img = message["img"]
            except KeyError:
                img = False
            if img:
                safe.append(message["content"])
    
    deletedImages = 0
    unknownImages = 0
    # print("Safe:", safe)
    for image in images:
        # print(image)
        if image.replace('\\', '/') in safe: continue
        if os.path.exists(f'./{image}'):
            try:
                os.remove(f'./{image}')
                deletedImages += 1
            except (OSError, FileNotFoundError):
                unknownImages += 1
    now = glob.glob('uploads\\*')
    print("Finished cleaning images:")
    print(f"    {deletedImages} image(s) were deleted.")
    print(f"    {unknownImages} image(s) couldn't be deleted.")
    print(f"    {len(safe)} image(s) are mentioned in chats.")
    print(f"    {len(images)} image(s) existed at the start.")
    print(f"    {len(now)} image(s) exist now.")


def do_users():
    print("Users:")
    for username, _ in users.items():
        print("   ", username)
    print()


def do_send():
    chat = print_chats()
    content = input("Type in your message: ")
    name = input("Select username [leave empty for \"Server\"]: ")
    if name.strip() == "": name = "Server"
    date = input("Select date [leave empty for automatic; format YYYY-MM-DD]: ")
    if date.strip() == "": date = current_time()[1]
    time = input("Select time [leave empty for automatic; format HH:mm]: ")
    if time.strip() == "": time = current_time()[0]

    fancy_message(name, content, chat)
    print(f"Sent on {date} at {time}.\n\n")

    if input("Are you sure you want to proceed? [Y/N] ") != "Y":
        print("Canceling.")
        return

    try:
        f = open(f'chats/{chat}.json', 'r')
        document = json.loads(f.read())
        f.close()
        if len(document["messages"]) == 0 or document["messages"][-1]["date"] != date:
            document["messages"].append({
                "author": "Day",
                "time": "00:00",
                "date": date,
                "content": date
            })
        document["messages"].append({
            "author": name,
            "time": time,
            "date": date,
            "content": content
        })
        f = open(f'chats/{chat}.json', "w")
        f.write(json.dumps(document, indent=4))
        f.close()
        print("Successfully appended message.")
    except (OSError, FileNotFoundError):
        print("Could not open chat")


def do_fake():
    print("\n\n\n")
    username = input("Select username: ")
    password = input("Select password: ")
    if username in users:
        print("User already exists")
        return
    users[username] = password
    lastSeen[username] = ' '.join(reversed(current_time()))
    print(f"Fake user called \"{username}\" successfully created!")


def do_create():
    print("\n\n\n")
    title = input("Type title: ")
    description = input("Type description (\\n for [Enter]): ").replace('\\n', '\n')
    private = input("Is private [T/F]: ") == 'T'
    creator = input("Choose creator's username (default: Admin): ")
    if creator.strip() == "": creator = "Admin"
    members = []
    try:
        last = chats.items()[-1][0]
    except IndexError:
        last = "chat0"
    id = int(last[4:]) + 1
    time, date = current_time()
    info = {
        "id": f"chat{id}",
        "title": title,
        "description": description,
        "private": private,
        "members": members,
        "messages": [
            {
                "author": "Day",
                "time": "00:00",
                "date": date,
                "content": date
            },
            {
                "author": "Server",
                "time": time,
                "date": date,
                "content": f"Chat created at {time} by @{creator}."
            }
        ]
    }
    try:
        with open(f"chats/chat{id}.json", "x") as file:
            file.write(json.dumps(info, indent=4))
    except FileExistsError:
        print(f"chats/chat{id}.json already exists. chats is unupdated?")
    do_update(log = False)
    print("Successfully created chat.")


def do_hash():
    print('\n\n' + str(_hashing(input("\n\nType string to hash: "))), end="\n\n\n")


if __name__ == '__main__':
    print("""
              _           _          _____                      _      
     /\      | |         (_)        / ____|                    | |     
    /  \   __| |_ __ ___  _ _ __   | |     ___  _ __  ___  ___ | | ___ 
   / /\ \ / _` | '_ ` _ \| | '_ \  | |    / _ \| '_ \/ __|/ _ \| |/ _ \\
  / ____ \ (_| | | | | | | | | | | | |___| (_) | | | \__ \ (_) | |  __/
 /_/    \_\__,_|_| |_| |_|_|_| |_|  \_____\___/|_| |_|___/\___/|_|\___|
                                                                       
                                                                       
    """)

    print("Welcome to your Admin Console!", end=" ")
    print(' '.join(current_time()))

    while True:
        print("\n\n\n\n=====================================================================================")
        print("\n\nActions:")
        print("    clear -- deletes all chats, users, cookies, messages, media, etc. - Basically a factory reset.")
        print("    view -- selects a chat and prints all its metadata & contents.")
        print("    delete -- deletes a chat.")
        print("    remove -- removes a specific message from a chat.")
        print("    kick -- removes a user from a chat.")
        print("    invite -- forcibly adds a participant to a chat.")
        print("    update -- updates summaries which might be outdated.")
        print("    images -- removes images not referenced in any chat.")
        print("    send -- sends a message from the Server.")
        print("    users -- get the names of all users.")
        print("    fake -- create a fake account.")
        print("    create -- create a chat.")
        print("    hash -- hashes a string.")
        print("    exit -- finish execution of Admin Console.")

        try:
            action = input("Select action: ")
            match action:
                case 'clear':
                    do_clear()
                case 'view':
                    do_view()
                case 'delete':
                    do_delete()
                case 'remove':
                    do_remove()
                case 'kick':
                    do_kick()
                case 'invite':
                    do_invite()
                case 'update':
                    do_update()
                case 'images':
                    do_images()
                case 'send':
                    do_send()
                case 'users':
                    do_users()
                case 'fake':
                    do_fake()
                case 'create':
                    do_create()
                case 'hash':
                    do_hash()
                case 'exit':
                    break
                case _:
                    print("Unsupported action. Check your spelling.")
        except KeyboardInterrupt:
            print("\n(^C) Stop execution.")
        except (IOError, OSError, FileExistsError, FileNotFoundError):
            print("\nFile System error. :(")
        except:
            print("\n\nSomething went wrong.")
