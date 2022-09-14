# Messager Application
## Created by ShZil

#### General Information:
  No, this is not a typo, it's intentionally without the 'n'.

  This application combines Python (socket), HTML, CSS, and JS,
  to create a functional messaging website, similar to WhatsApp Web.

  It's original and made as a school assignment.


#### Execute:
- SERVER: Open the server with a double click on `run.bat`.
- CLIENT(S): Open a browser (like Google Chrome) and enter ____
- - If you're on the same computer: `localhost:8008`;
- - If not, the address shown at the top of the console. (similar to `123.456.789.000:8008`)

#### Technical Details:
**Entry point:**

- Serverside: either `run.bat` or `main.py`.
- Clientside: `index.html` for login page; `main.html` for application.
- - If the server is running, just go to address `localhost:8008`.

#### Dependencies:
- `python 3.10+`
- `pip install socket` for handling TCP communication with Python.
- A browser with Chromium (tested on Google Chrome & Opera)

#### Protocol Specifications (Communication):
**Start:**
```
~> GET / HTTP/1.1
<~ 200 OK (index.html)
... (more GETs and files of CSS and JS)
~> POST /signup HTTP/1.1  or  POST /login HTTP/1.1
<~ 301 Moved Permanently (Set-Cookie)
~> GET / HTTP/1.1
<~ 200 OK (main.html)
... (more GETs and files of CSS and JS)
```

**Displaying chats and messages:**
```
~> GET /chats HTTP/1.1
<~ 200 OK (txt with list: newline separated, items of format "id=title")
```

```
~> GET /chat?chat_id HTTP/1.1  (where 'chat_id' was given by a `GET /chats` requests)
<~ 200 OK (JSON file containing metadata about the chat & its content, aka messages)
```

**Actions:**
**Sending a message:**
```
~> POST /message?dst=chat_id HTTP/1.1 (Message content)
<~ HTTP/1.1 201 Created
```

**Creating a chat:**
```
~> POST /create HTTP/1.1 (title={title}&description={description}[?&private=true])
<~ HTTP/1.1 201 Created
```


#### Ideas Paper -> Digital Copy

_Implementations:_
- [X] Update Interval ("Get /new_messages" every 500ms(?))
- [ ] WebSocket -- HTTP Upgrade
- [ ] Client software (python:socket) & locally-hosted HTML file
- [ ] Socket.IO -- Websocket Upgrade
- [ ] XMPP Protocol [the one WhatsApp uses]


* Change token randomly for security. [DONE]

#### Additional ideas:
- [X] make: POST /invite?dst={chat_id}&user={username}
- [X] merge: POST /login and POST /signup
- [X] Add color solving for dummies
- [X] Move post handling helpers from main.py to post.py
- [X] Unread chat style
- [X] Chat tabs with last message
- [X] Enter should send message; Shift+Enter should enter
- [X] Delete user from `/user/self`
- [ ] Store password hash as HEX

#### Ideas that needn't be implemented
- [ ] Send chat in segments (constant max length); send most recent segment first. Implementation: Store chats as separate JSON with "ref" property?
- [ ] if fetch (/chat) stops working again, supply the user with a different chat every time they ask to GET /chat. Iterate.
