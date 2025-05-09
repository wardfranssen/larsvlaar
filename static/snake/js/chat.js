function ronJans() {
    // Todo: Play audio
    const ronJans = `
        <div class="jon-rans">
            <img src="/img/jon_rans.png">
        </div>
    `;

    document.body.insertAdjacentHTML("beforeend", ronJans);
}

function larsVlaar() {
    const ronJansInterval = setInterval(() => {
        ronJans();
    }, 150);

    setTimeout(() => {
        clearInterval(ronJansInterval);
    }, 5000);

    document.body.classList.add("monster-impact");

    const monster = document.createElement("img");
    monster.src = "/img/lars_is_dik.png";
    monster.id = "larsvlaar";
    document.body.appendChild(monster);

    setTimeout(() => {
        document.body.classList.remove("lars-impact");
        document.body.classList.add("lars-landed");
        let shockwave = document.createElement("div");
        shockwave.className = "shockwave";

        for (let i = 0; i < 10; i++) {
            shockwave = document.createElement("div");
            shockwave.className = "shockwave";
            document.body.appendChild(shockwave);
        }

        document.body.classList.add("lars-impact");
        document.body.classList.remove("lars-landed");
    }, 850)

    const flashInterval = setInterval(() => {
        const explosion = document.createElement("div");
        explosion.className = "explosion";
        document.body.appendChild(explosion);

        explosion.classList.add("explode");

        const flash = document.createElement("div");
        flash.className = "flash";
        document.body.appendChild(flash);

        flash.classList.add("active");
    }, 3000);

    setTimeout(() => {
        clearInterval(flashInterval);

        monster.classList.add("lars-exit");

        setTimeout(() => {
            const flash = document.createElement("div");
            flash.className = "flash";
            document.body.appendChild(flash);
            flash.classList.add("active");

            const ronJans = document.querySelectorAll(".jon-rans");
            for (const ron of ronJans) {
                ron.remove();
            }

        }, 3000)


        setTimeout(() => {
            document.body.classList.remove("lars-impact");
            monster.remove();
        }, 3000)
    }, 10000);
}




async function getChatHistory(id, idType) {
    const response = await fetch(`/api/chat/history?${idType}=${id}`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    const responseJson = await handleJsonResponse(response);
    return responseJson["messages"];
}

async function initializeChat(id, idType) {
    const chatHistory = await getChatHistory(id, idType);
    const messageContainer = document.querySelector("#messages-container");

    for (const message of chatHistory) {
        let username = "";
        if (message["username"]) {
            username = `<div class="username">${message["username"]}:</div>`;
        }

        const messageDiv = `
            <div class="message">
                <div class="message-body">
                    ${username}
                    <div class="text">
                        ${message["message"]}
                    </div>
                </div>
            </div>
        `;

        messageContainer.insertAdjacentHTML("afterbegin", messageDiv);
    }
}

function sendMessage() {
    const input = document.getElementById("chat-input");
    const message = input.value;

    input.value = "";

    if (!message.trim()) return;

    chatSocket.emit("send_message", message);
}

async function startChatSocket(id, idType) {
    await initializeChat(id, idType);
    chatScrollDown();

    chatSocket = io(`/ws/chat?${idType}=${id}`, { forceNew: true });

    chatSocket.on("message_received", (data) => {
        const messageContainer = document.querySelector("#messages-container");
        let scroll = false;

        if (messageContainer.scrollTop + messageContainer.clientHeight === messageContainer.scrollHeight) {
            scroll = true;
        }

        const messageDiv = `
            <div class="message">
                <div class="message-body">
                    <div class="username">${data["username"]}:</div>
    
                    <div class="text">
                        ${data["message"]}
                    </div>
                </div>
            </div>
        `;

        messageContainer.insertAdjacentHTML("beforeend", messageDiv);

        if (scroll) {
            chatScrollDown();
        }
    });

    // Todo: Make function
    chatSocket.on("server_message", (data) => {
        const messageContainer = document.querySelector("#messages-container");
        let scroll = false;

        if (messageContainer.scrollTop + messageContainer.clientHeight === messageContainer.scrollHeight) {
            scroll = true;
        }

        const messageDiv = document.createElement("div");
        messageDiv.className = "message";

        const messageBody = document.createElement("div");
        messageBody.className = "message-body";

        const textDiv = document.createElement("div");
        textDiv.className = "text";
        textDiv.textContent = data["message"];

        messageBody.appendChild(textDiv);
        messageDiv.appendChild(messageBody);
        messageContainer.appendChild(messageDiv);

        if (data["exp"]) {
            setTimeout(() => {
                messageDiv.remove();
            }, data["exp"] * 1000);
        }

        if (scroll) {
            chatScrollDown();
        }
    });
}

function chatScrollDown() {
    const messageContainer = document.querySelector("#messages-container");
    messageContainer.scrollTop = messageContainer.scrollHeight;
}

let chatSocket;

document.getElementById("chat-input").addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});

document.getElementById("messages-container").addEventListener("scroll", function (event) {
    const messageContainer = document.getElementById("messages-container");

    if (messageContainer.scrollHeight - messageContainer.scrollTop >= 2 * messageContainer.clientHeight) {
        document.getElementById("scroll-down").classList.add("show");
    } else {
        document.getElementById("scroll-down").classList.remove("show");
    }
});
