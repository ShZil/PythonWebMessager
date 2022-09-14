const container = document.getElementsByClassName('search')[0];
const [input, button] = container.children;
const chatsList = document.getElementById('chats-list');

input.addEventListener('input', () => {
    var value = input.value;
    var resultsCount = 0;
    for (const chat of chatsList.getElementsByClassName('tab')) {
        var name = chat.textContent;
        if (isin(name, value)) {
            resultsCount++;
            chat.style.display = "block";
        } else chat.style.display = "none";
    }
    if (resultsCount == 0) {
        if (value.length == 0) {
            document.getElementById('have-no-chats').style.display = "flex";
            document.getElementById('no-chats').style.display = "none";
        } else {
            document.getElementById('no-chats').style.display = "flex";
            document.getElementById('have-no-chats').style.display = "none";
        }
    } else {
        document.getElementById('have-no-chats').style.display = "none";
        document.getElementById('no-chats').style.display = "none";
    }
});

function isin(str, sub) {
    return str.toLowerCase().includes(sub.toLowerCase());
}