// *** Header ***
// This file is responsible for all actions on the page: sending and receiving messages, updating visually, etc.

var chatsCache = [];

// Say "updating = false;" to terminate chat message updates.
var updating = true;
messageUpdates();
// Say "clearInterval(chatsInterval);" to terminate chat title updates.
var chatsInterval = startInterval(10, () => get('chats').then(x => x.text()).then(x => displayChats(x)));
// Change the possible randomised username colours here:
const userColors = ["f94144", "f8961e", "f9c74f", "43aa8b", "577590"];
// when a chat is unread: true = golden bell icon; false = green circle icon.
var bellNotCircle = true;

const username = document.getElementById('username').textContent;

const dom = {
    img: (content, href, filename, id) => `<img src=${content} alt="image" onclick="window.open('${href}', '_blank')" title="${filename}" onload="scrollToBottom(document.getElementById(${id}))" onerror="this.style.opacity='0'">`,
    msg: (addClass, position, color, author, displayAuthor, content, time) => `<div class="${addClass} ${position}">
                                                                                    <h4 class="name" style="color: ${color}" onclick="window.location.assign('/user/${author}')"><a class="styleless" href="/user/${author}" tabindex="-1">${displayAuthor}</a></h4>
                                                                                    <p class="message">${content}</p>
                                                                                    <div class="time">${time}</div>
                                                                                </div>`,
    subtitle: (group, length) => `${group} • ${length} participant${length > 1 ? 's' : ''}<hr>`,
    created: (name, date, time) => converter.makeHtml(`Group created by ${name}, on ${date} at ${time}`).replaceAll('@', ''),
    createdError: () => `Group created by [unknown], on [unknown] at [unknown]`,
    member: (name) => `<li><a class="styleless" href="/user/${name}" style="cursor: pointer;">${name}</a></li>`,
    invite: (id) => `<li class="add-plus"><button type="button" class="menu-invite" onclick="invite('${id}')">Add participant</button></li>`,
    quit: (id) => `<li class="add-x"><button type="button" class="menu-exit" onclick="quit('${id}')">Exit group</button></li>`,
    list: (content) => `<ul>${content}</ul>`,
    tab: (id, name) => `<div class="tab" onclick="openTab(this, '${id}')" id="tab-${id}" tabindex="0" onkeyup="if(event.keyCode == 13 || event.keyCode == 32){event.target.click()}">
                            <span>${name}</span>
                            <div class="smaller" id="last-msg-${id}">
                                <span></span>
                                <span></span>
                            </div>
                        </div>`,
    chatBase: (id, name) => `<div class="chat" id="${id}">
                                <div class="title">
                                    <span>${name}</span>
                                    <span id="menu-${id}" class="chat-menu"><i class="fa fa-ellipsis-v black-to-white reverse" title="Options"></i></span>
                                </div>
                                <div class="chat-content">
                                    <div class="loader">loading...</div>
                                </div>
                            </div>`,
    menuBase: (id, name) => `<div id="menu-chat-${id}" class="modal menu-chat" style="display: none;">
                                <div class="modal-content">
                                    <span class="close">&times;</span>
                                    <div class="menu-title">${name}</div>
                                    <div class="menu-subtitle"></div>
                                    <div class="menu-description">loading...</div>
                                    <div class="menu-created"></div>
                                    <hr>
                                    <div class="menu-members">loading...</div>
                                </div>
                            </div>`,
    privateChatTitle: (other, self) => `Chat with ${other}`
}

const converter = new showdown.Converter({
    excludeTrailingPunctuationFromURLs: true,
    literalMidWordUnderscores: true,
    strikethrough: true,
    tables: true,
    tasklists: true,
    simpleLineBreaks: true,
    requireSpaceBeforeHeadingText: true,
    ghMentions: true,
    ghMentionsLink: '/user/{u}'
});

// *** Interesting code ***
function displayMessage(id, message, prev, next) {
    // Returns the DOM string containing the message.
    // message: JSON, prev: boolean, next: boolean.
    var {content, author, time, img, filename} = message;

    let position = prev ? (next ? "middle" : "bottom") : (next ? "top" : "");

    if (img) {
        content = dom.img(content, window.location.href + content, filename, id);
    } else {
        author = author.replaceAll("<", "&lt;").replaceAll(">", "&gt;");
        content = content.replaceAll("<", "&lt;").replaceAll('\n\n', '<br><br>');
        time = time.replaceAll("<", "&lt;").replaceAll(">", "&gt;");
    }

    var addClass = "message";
    switch (author) {
        case username:
            addClass += " right";
            break;
        case "Day":
            addClass = "date";
            break;
        case "Server":
            addClass = "date server";
            break;
        default:
            addClass += " left";
    }

    const color = randomColor(author);
    var _author = author == username ? "You" : author;
    
    var _content = converter.makeHtml(content);
    if (author == "Server") _content = _content.replaceAll('@', '');

    return dom.msg(addClass, position, color, author, _author, _content, time);
}

function displayChat(json) {
    // Display a chat's contents and metadata.
    if (json == {} || json === "") {
        console.error("JSON data is empty");
        return;
    }

    var id = json["id"];
    const chat = document.getElementById(id);

    if (chat == null) {
        console.error("Couldn't find chat.");
        return;
    }

    const [title, messages] = chat.children;
    const loader = chat.getElementsByClassName('loader')[0];

    json["title"] = perspective(json["title"]);

    title.children[0].textContent = json["title"];
    if (loader != undefined) loader.style.display = "none";

    // Parse all the messages
    var content = "";
    for (let i = 0; i < json["messages"].length; i++) {
        const message = json["messages"][i];

        let prev = i == 0 ?
                    false :
                    json["messages"][i - 1]["author"] == message["author"];
        let next = i == json["messages"].length - 1 ?
                    false :
                    json["messages"][i + 1]["author"] == message["author"];

        content += displayMessage(id, message, prev, next);
    }

    // Check for unread messages
    const prevLength = messages.childElementCount;
    messages.innerHTML = content;
    if (prevLength != messages.childElementCount) {
        setTimeout(() => { scrollToBottom(messages) }, 100);
        // if (chat is not currently open) and (this is not the first update) and (last person who sent a message isn't me) then .unread
        if (current != id && prevLength > 1 && json["messages"][json["messages"].length - 1]["author"] != username) {
            document.getElementById('tab-' + id).className += ' unread' + (bellNotCircle ? ' bell' : '');
        }
    }

    // Update last message at tab button
    if (json["messages"].length > 0) {
        messages.style.overflowY = 'auto';
        const lastMessage = json["messages"][json["messages"].length - 1];
        if (lastMessage["author"] != "Day") {
            const tab = document.getElementById('tab-' + id);
            const last = document.getElementById('last-msg-' + id);

            tab.style.lineHeight = "1.25";
            var [auth, text] = last.children;
            auth.textContent = lastMessage["author"] == "Server" ? "" : lastMessage["author"] + ":";
            if (lastMessage["img"]) {
                text.textContent = "<Media uploaded>";
                text.title = lastMessage["filename"];
            } else {
                text.textContent = lastMessage["content"];
                text.title = lastMessage["content"];
            }
        }
    }
    
    // Update metadata menu
    const menu = document.getElementById(`menu-chat-${id}`).children[0];
    const [close, menu_title, subtitle, description, created, hr, members, exit] = menu.children;
    menu_title.textContent = json["title"];

    const len = json["members"].length;
    var group = "Group";
    if (len == 0) group = "Empty Chat";
    if (len == 1) group = "Personal Chat";
    if (len == 2) group = "Private Chat"
    subtitle.innerHTML = dom.subtitle(group, len);

    description.innerHTML = converter.makeHtml(json["description"].replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('\n', '<br>'));

    try {
        const creation = json["messages"][1];
        creation.date = json["messages"][0].content;
        creation.name = creation.content.split('by ').slice(1).join('');
        if (creation.name.charAt(creation.name.length - 1) == '.') {
            creation.name = creation.name.substr(0, creation.name.length - 1);
        }
        created.innerHTML = dom.created(creation.name, creation.date, creation.time);
    } catch (error) {
        created.textContent = dom.createdError();
    }

    var memberList = json["members"].map(member => dom.member(member));
    memberList.push(dom.invite(id));
    memberList.push(dom.quit(id));
    members.innerHTML = dom.list(memberList.join('\n'));

    document.querySelectorAll('.chat a').forEach(node => node.tabIndex = -1);
}

function displayChats(chats) {
    chats = chats.split('\n');
    if (chats[0].startsWith("<!DOCTYPE html>") || (!chats[0].includes("=") && chats[0].length > 0)) {
        console.error("Got an HTML page where there should've been a txt linefeed-separated file.")
        console.log(chats)
        return;
    }
    if (chats.length == 1 && chats[0] == "") chats = [];
    newChats = chats.filter(x => !chatsCache.includes(x));
    chatsCache = chats;

    if (chatsCache.length == 0) {
        // You have no chats
        document.getElementById('chats-list').getElementsByClassName('loader')[0].style.display = "none";
        document.getElementById('have-no-chats').style.display = "flex";
        return;
    }

    if (newChats.length == 0) return;
    console.log(newChats);

    document.getElementById('have-no-chats').style.display = "none";
    document.getElementsByClassName('chat-container')[0].style.overflowY = "auto";

    const container = document.getElementById('chats-list');
    const basicChat = document.getElementById('basic');
    const modal = document.getElementById('new-chat');

    const loader = container.getElementsByClassName('loader')[0];
    if (loader != undefined) loader.style.display = "none";

    // Create the tabs
    for (var chat of newChats) {
        var [id, name] = chat.split('=');

        name = perspective(name);

        container.innerHTML += dom.tab(id, name);
        basicChat.insertAdjacentHTML("afterend", dom.chatBase(id, name));
        modal.insertAdjacentHTML("afterend", dom.menuBase(id, name));
        createModal(document.getElementById(`menu-${id}`), document.getElementById(`menu-chat-${id}`));
    }
}

async function messageUpdates() {
    while (updating) {
        var chats = [...chatsCache];
        for (var chat of chats) {
            var [id, name] = chat.split('=');

            try {
                get('chats/' + id + '.json').then(x => x.json()).then(content => displayChat(content));
            } catch (error) {
                await sleep(0.1);
                continue;
            }
        }
        await sleep(0.5);
    }
}

// *** DOM Updates ***
function scrollToBottom(element) {
    if (element == null) return;
    element.scroll({ top: element.scrollHeight, behavior: "instant" })
}

function auto_grow(element) {
    element.style.height = "5px";
    element.style.height = (element.scrollHeight) + "px";
}

// *** Between ***
function disableColons(input) {
    input.value = input.value.replaceAll(':', '').replaceAll('~', '');
}

function userNav() {
    var user = window.prompt("Which user would you like to look up?", "");
    if (user == null) return;
    if (user.trim() == "") return;
    window.location.assign('/user/' + user.trim());
}

// *** Others ***
function sleep(s) {
    return new Promise(resolve => setTimeout(resolve, s * 1000));
}

function logout() {
    if (!window.confirm("Are you sure you want to log out?")) return;
    deleteAllCookies();
    location.reload();
}

function deleteAllCookies() {
    var cookies = document.cookie.split(";");

    for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i];
        var eqPos = cookie.indexOf("=");
        var name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
        document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT";
    }
}

function startInterval(sec, callback) {
    callback();
    return setInterval(callback, sec * 1000);
}

function randomColor(seed) {
    var index = Math.floor(new Random(hashOf(seed)).nextFloat() * userColors.length);
    return '#' + userColors[index];
}

function Random(seed) {
    this._seed = seed % 2147483647;
    if (this._seed <= 0) this._seed += 2147483646;
}

Random.prototype.next = function () {
    return this._seed = this._seed * 16807 % 2147483647;
};

Random.prototype.nextFloat = function () {
    return (this.next() - 1) / 2147483646;
};

function hashOf(string) {
    var hash = 0;
    if (string.length == 0) return hash;

    for (i = 0; i < string.length; i++) {
        char = string.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }

    return hash;
}

function perspective(name) {
    if (name == undefined) return name;
    var me = username.trim();
    if (name.startsWith('Chat between')) {
        var names = name.substring('Chat between'.length).split(' and ');
        for (var n of names) {
            n = n.trim();
            if (n != me) {
                return dom.privateChatTitle(n, me);
            }
        }
    }
    return name;
}
