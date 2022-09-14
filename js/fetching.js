var errorCount = 0;
const measurePerformance = false;

// *** Communication ***
async function get(url) {
    console.log("GET " + url);
    if (measurePerformance) {const start = performance.now();}
    try {
        var res = await fetch(window.location.href + url, { headers: new Headers({ 'Chat': url }) });
    } catch (error) {
        errorCount++;
        if ((errorCount >= 2 && chatsCache == []) || errorCount >= 10) document.getElementById('internet-warning').style.display = "grid";
        throw error;
    }
    errorCount = 0;
    document.getElementById('internet-warning').style.display = "none";

    if (measurePerformance) {
        var time = Math.floor(performance.now() - start);
        if (time > 1000) time = Math.floor(time / 1000) + "s";
        else time += "ms";
        console.log("GOT " + url + "    " + time);
    } else {
        console.log("GOT " + url);
    }
    return res;
}

async function post(url, data) {
    console.log("POST " + url + "  ( " + data + " )")
    var res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'text/plain' },
        body: data
    });
    return res;
}

// Application specific GET/POST requests:
async function sendTyped(to) {
    // Does POST /message
    if (to == 'basic') {
        console.error("Cannot send message without a chat.")
        return;
    }
    const textfield = document.getElementById('message');
    let text = textfield.value.trim();
    if (text == '') {
        textfield.value = "";
        console.error("Don't send empty messages");
        document.getElementById('msg-button').style.backgroundColor = "var(--bad)";
        sleep(0.5).then(_ => document.getElementById('msg-button').style.backgroundColor = "var(--good)");
        return; // No empty messages
    }
    textfield.value = "";
    var res = await post('/message?dst=' + to, text);
    console.log(res);
}

async function invite(chat) {
    // Does POST /invite
    chat = chat.trim()
    var name = document.getElementById(chat).children[0].children[0].textContent;
    var message = "Whom do you want to invite to \"" + name + "\"?\n[username for one person; chat title for all participants]";
    var user = window.prompt(message);
    if (user == null) return;
    if (user.trim() == "") return;
    var res = await post(`invite?dst=${chat}&user=${user}`, "");
    res = await res.text();
    window.alert(res);
}

async function quit(chat) {
    // Does POST /quit
    chat = chat.trim()
    var name = document.getElementById(chat).children[0].children[0].textContent;
    var message = "Are you sure you want to quit \"" + name + "\"?";
    if (!window.confirm(message)) return;
    var res = await post(`quit?dst=${chat}`, "");
    res = await res.text();
    window.alert(res);
    window.location.reload();
}

async function sendCreateChat(form) {
    // Does POST /create
    var inputs = [...form.children].filter(ele => (ele?.type == "text" && ele?.tagName == "INPUT") || ele?.tagName == "TEXTAREA");
    var values = inputs.map(ele => ele.name.replace(/=|&/g, '') + '=' + ele.value.replace(/=|&/g, ''));
    form.parentElement.parentElement.style.display = "none";
    for (let input of inputs) input.value = "";
    try {
        var res = await post('/create', values.join('&'));
        res = await res.text();
        console.log(res);
    } catch (error) {
        console.log("New chat failed");
    }
}
