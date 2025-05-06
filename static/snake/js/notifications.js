const notifySocket = io("/ws/notifications", { forceNew: true });
let friendRequestTimeout;

let lastActivitySent = 0;
const activityInterval = 15000;

notifySocket.on("received_friend_request", (data) => {
    const userId = data["user_id"];
    const username = data["username"];
    const pfpVersion = data["pfp_version"];

    if (window.isOnFriendsPage) {
        const activeTab = document.querySelector(".nav .selected").id

        if (activeTab === "received-friend-requests-nav") {
            createReceivedFriendRequestsList();
        } else if (activeTab === "add-friends-nav") {
            updateUserList();
        }
    }

    createFriendRequestPopup(userId, username, pfpVersion);
});

notifySocket.on("friend_request_accepted", (data) => {
    createGeneralPopup(`${data["username"]} heeft je vriendschapsverzoek geaccepteerd`, "success");

    if (window.isOnFriendsPage) {
        const activeTab = document.querySelector(".nav .selected").id

        if (activeTab === "received-friend-requests-nav") {
            createReceivedFriendRequestsList();
        } else if (activeTab === "my-friends-nav") {
            createMyFriendsList();
        } else if (activeTab === "add-friends-nav") {
            updateUserList();
        } else if (activeTab === "sent-friend-requests-nav") {
            createSentFriendRequestsList()
        }
    }
});

notifySocket.on("friend_request_rejected", (data) => {
    createGeneralPopup(`${data["username"]} heeft je vriendschapsverzoek afgewezen`, "error");

    if (window.isOnFriendsPage) {
        const activeTab = document.querySelector(".nav .selected").id

        if (activeTab === "received-friend-requests-nav") {
            createReceivedFriendRequestsList();
        } else if (activeTab === "add-friends-nav") {
            updateUserList();
        } else if (activeTab === "sent-friend-requests-nav") {
            createSentFriendRequestsList()
        }
    }
});

notifySocket.on("friend_request_canceled", (data) => {
    closeFriendRequestPopup(data["user_id"]);

    if (window.isOnFriendsPage) {
        const activeTab = document.querySelector(".nav .selected").id

        if (activeTab === "received-friend-requests-nav") {
            createReceivedFriendRequestsList();
        } else if (activeTab === "add-friends-nav") {
            updateUserList();
        }
    }
});

notifySocket.on("friend_removed", (data) => {
    const invitePopup = document.querySelector(`#invite-${data["user_id"]}`);
    if (invitePopup) {
        invitePopup.remove();
    }

    if (window.isOnFriendsPage) {
        const activeTab = document.querySelector(".nav .selected").id;

        if (activeTab === "my-friends-nav") {
            createMyFriendsList();
        } else if (activeTab === "add-friends-nav") {
            updateUserList();
        }
    }
});

notifySocket.on("received_invite", (data) => {
    const userId = data["user_id"];
    const username = data["username"];
    const pfpVersion = data["pfp_version"];
    const inviteId = data["invite_id"];
    const createdAt = data["created_at"];
    const serverTime = data["server_time"];
    const gameMode = data["game_mode"];
    const lobbyId = data["lobby_id"];

    createReceivedInvitePopup(inviteId, userId, username, pfpVersion, lobbyId, gameMode, createdAt, serverTime);
});

notifySocket.on("invite_accepted", (data) => {
    if (data["lobby_id"]) {
        const popup = document.querySelector(`#sent-invite-${data["invite_id"]}`);
        if (popup) {
            popup.remove();
        }
    } else {
        const opponent = data["opponent"];
        const opponentId = opponent["user_id"];
        const opponentUsername = opponent["username"];
        const opponentPfpVersion = opponent["pfp_version"];
        localStorage.setItem("opponent", JSON.stringify({"userId": opponentId, "username": opponentUsername, "pfpVersion": opponentPfpVersion}));

        window.location.href = data["redirect"];
    }
});

notifySocket.on("invite_rejected", (data) => {
    createGeneralPopup(`${data["username"]} heeft je uitnodiging afgewezen`, "error");

    const popup = document.querySelector(`#sent-invite-${data["invite_id"]}`);
    if (popup) {
        popup.remove();
    }
});

notifySocket.on("invite_canceled", (data) => {
    createGeneralPopup(`${data["username"]} heeft zijn uitnodiging geannuleerd`, "error");

    const popup = document.querySelector(`#received-invite-${data["invite_id"]}`);
    if (popup) {
        popup.remove();
    }
});


function sendActivity() {
    const now = Date.now();
    if (now - lastActivitySent > activityInterval) {
        notifySocket.emit("activity");
        lastActivitySent = now;
    }
}

["click", "keydown", "touchstart"].forEach(event => {
    document.addEventListener(event, sendActivity);
});


async function sendFriendRequest(userId) {
    const response = await fetch(`/api/friend_request/${userId}/send`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    const responseJson = await handleJsonResponse(response);
    if (responseJson) {
        const userDiv = document.querySelector(`#user-${userId}.search-user .friend-button`);
        if (userDiv) {
            userDiv.innerHTML = `<button class="status-button pending"><img src="/icon/hourglass.svg" draggable="false"></button>`;
        }
    }
}

async function acceptFriendRequest(userId, type) {
    const response = await fetch(`/api/friend_request/${userId}/accept`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    const responseJson = await handleJsonResponse(response);
    if (responseJson) {
        const requestPopup = document.querySelector(`#friend-request-${userId}`);
        if (requestPopup) {
            requestPopup.remove();
        }

        if (!window.isOnFriendsPage) {
            return;
        }

        let userDiv = document.querySelector(`#user-${userId}.${type}`);

        if (type === "friend-request-popup") {
            const activeTab = document.querySelector(".nav .selected").id
            userDiv = document.querySelector(`#user-${userId}.search-user`);

            if (activeTab === "received-friend-requests-nav") {
                createReceivedFriendRequestsList();
            } else if (activeTab === "my-friends-nav") {
                createMyFriendsList();
            } else if (activeTab === "add-friends-nav") {
                if (userDiv) {
                    userDiv.querySelector(".friend-button").innerHTML = `
                        <div class="more-dropdown" onclick="toggleMore(this)">
                        <button class="status-button more"><img src="/icon/more.svg" draggable="false"></button>
        
                            <div class="dropdown-content">
                                <button onclick="sendInvite('${userId}', 'one_vs_one')">1v1</button>
                                <button onclick="removeFriend('${userId}', false)">Verwijder Vriend</button>
                            </div>
                        </div>
                    `;
                }
            }
        } else if (type === "received-friend-request") {
            userDiv.remove();
        } else if (type === "search-user") {
            userDiv.querySelector(".friend-button").innerHTML = `
                <div class="more-dropdown" onclick="toggleMore(this)">
                <button class="status-button more"><img src="/icon/more.svg" draggable="false"></button>

                    <div class="dropdown-content">
                        <button onclick="sendInvite('${userId}', 'one_vs_one')">1v1</button>
                        <button onclick="removeFriend('${userId}', false)">Verwijder Vriend</button>
                    </div>
                </div>
            `;
        }
    }
}

async function rejectFriendRequest(userId, type) {
    const response = await fetch(`/api/friend_request/${userId}/reject`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    const responseJson = await handleJsonResponse(response);
    if (responseJson) {
        const requestPopup = document.querySelector(`#friend-request-${userId}`);
        if (requestPopup) {
            requestPopup.remove();
        }

        if (!window.isOnFriendsPage) {
            return;
        }


        if (type === "friend-request-popup") {
            const activeTab = document.querySelector(".nav .selected").id

            if (activeTab === "received-friend-requests-nav") {
                const userDiv = document.querySelector(`#user-${userId}.received-friend-request`);
                if (userDiv) {
                    userDiv.remove();
                }
            } else if (activeTab === "add-friends-nav") {
                const userDiv = document.querySelector(`#user-${userId}.search-user`);
                userDiv.querySelector(".friend-button").innerHTML = `<button class="status-button no-friend" onclick="sendFriendRequest('${userId}')"><img src="/icon/add.svg" draggable="false"></button>`;
            }
            return;
        }

        const userDiv = document.querySelector(`#user-${userId}.${type}`);
        if (type === "received-friend-request") {
            userDiv.remove();
        } else if (type === "search-user") {
            userDiv.querySelector(".friend-button").innerHTML = `<button class="status-button no-friend" onclick="sendFriendRequest('${userId}')"><img src="/icon/add.svg" draggable="false"></button>`;
        }
    }
}

async function acceptInvite(inviteId, lobbyId){
    const response = await fetch(`/api/invites/${inviteId}/accept`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });
    let responseJson;
    if (lobbyId === "null") {
        responseJson = await handleJsonResponse(response, {
            onRedirect: (json) => {
                const opponent = json["opponent"];
                const opponentId = opponent["user_id"];
                const opponentUsername = opponent["username"];
                const opponentPfpVersion = opponent["pfp_version"];

                localStorage.setItem("opponent", JSON.stringify({"userId": opponentId, "username": opponentUsername, "pfpVersion": opponentPfpVersion}));
            }
        });
    } else {
        responseJson = await handleJsonResponse(response);
    }

    if (!responseJson) {
        const popup = document.querySelector(`#received-invite-${inviteId}`);
        if (popup) {
            popup.remove();
        }
    }
}


function sentInviteCountdown(inviteId, i) {
    const title = document.querySelector(`#sent-invite-${inviteId} h3`);
    if (!title) {
        return
    }
    if (i === 0) {
        const popup = document.querySelector(`#sent-invite-${inviteId}`);
        if (popup) {
            popup.remove();
        }
        return;
    }

    title.innerText = `Verloopt over ${i} sec`;
    i -= 1;

    setTimeout(() => {
        sentInviteCountdown(inviteId, i);
    }, 1000);
}

function createSentInvitePopup(inviteId, userId, username, pfpVersion, createdAt=null, serverTime=null) {
    const invitePopupContainer = document.querySelector("#sent-invite-popup .invites-container");
    // invitePopupContainer.innerHTML = "";

    const invitePopup = `
        <div id="sent-invite-${inviteId}" class="sent-invite-popup" inviteId="${inviteId}" userId="${userId}">
            <h3>Verloopt over 15 sec</h3>

            <div class="content">
                <div class="profile-card">
                    <div class="pfp"><img src="/api/users/${userId}/pfp?v=${pfpVersion}"></div>
                    <div class="username">${username}</div>
                </div>
                <button class="status-button pending">
                    <img src="/icon/hourglass.svg" draggable="false">
                </button>
            </div>

            <div class="close-button" onclick="cancelInvite('${inviteId}')">
                <img src="/icon/close_black.svg" draggable="false"></button>
            </div>
        </div>
    `;
    invitePopupContainer.insertAdjacentHTML('beforeend', invitePopup);

    const offset = Date.now() / 1000 - serverTime;
    const adjustedCreatedAt = createdAt + offset;

    sentInviteCountdown(inviteId, Math.floor(15 - (Date.now()/1000 - adjustedCreatedAt)));
}

async function cancelInvite(inviteId) {
    const response = await fetch(`/api/invites/${inviteId}`, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });
    await handleJsonResponse(response);

    const popup = document.querySelector(`#sent-invite-${inviteId}`);
    if (popup) {
        popup.remove();
    }
}

function createReceivedInvitePopup(inviteId, userId, username, pfpVersion, lobbyId, gameMode, createdAt, serverTime) {
    const invitePopupContainer = document.querySelector("#received-invite-popup .invites-container");
    // invitePopupContainer.innerHTML = "";

    if (gameMode === "custom") {
        gameMode = "Custom Game";
    } else if (gameMode === "one_vs_one") {
        gameMode = "1v1";
    }

    const invitePopup = `
        <div id="received-invite-${inviteId}" class="received-invite-popup">
            <h3>${gameMode} Uitnodiging</h3>

            <div class="content">
                <div class="profile-card">
                    <div class="pfp"><img src="/api/users/${userId}/pfp?v=${pfpVersion}"></div>
                    <div class="username">${username}</div>
                </div>
                <div class="friend-button">
                    <button class="status-button accept" onclick="acceptInvite('${inviteId}', '${lobbyId}')">
                        <img src="/icon/check.svg" draggable="false">
                    </button>
                    <button class="status-button reject" onclick="closeReceivedInvitePopup('${inviteId}')">
                        <img src="/icon/close.svg" draggable="false">
                    </button>
                </div>
            </div>
        </div>
    `;
    invitePopupContainer.insertAdjacentHTML('beforeend', invitePopup);

    let offset;
    if (!createdAt) {
        offset = Date.now()/1000;
    } else {
        offset = Date.now() / 1000 - serverTime;
    }
    const adjustedCreatedAt = createdAt + offset;

    setTimeout(function() {
        const popup = document.querySelector(`#received-invite-${inviteId}`);
        if (popup) {
            popup.remove();
        }
    }, (15 - (Date.now()/1000 - adjustedCreatedAt))*1000);
}

function closeReceivedInvitePopup(inviteId) {
    const popup = document.querySelector(`#received-invite-${inviteId}`);
    if (popup) {
        popup.remove();
    }

    rejectInvite(inviteId);
}

function createFriendRequestPopup(userId, username, pfpVersion) {
    clearTimeout(friendRequestTimeout);

    const friendRequest = document.querySelector("#friend-request-popup");

    friendRequest.innerHTML = "";

    const friendRequestPopup = `
        <div id="friend-request-${userId}" class="friend-request-popup">
            <h3>Vriendschapsverzoek</h3>

            <div class="content">
                <div class="profile-card">
                    <div class="pfp"><img src="/api/users/${userId}/pfp?v=${pfpVersion}"></div>
                    <div class="username">${username}</div>
                </div>
                <div class="friend-button">
                    <button class="status-button accept" onclick="acceptFriendRequest('${userId}', 'friend-request-popup')">
                        <img src="/icon/check.svg" draggable="false">
                    </button>
                    <button class="status-button reject" onclick="rejectFriendRequest('${userId}', 'friend-request-popup')">
                        <img src="/icon/close.svg" draggable="false">
                    </button>
                </div>
            </div>
            
            <div class="close-button" onclick="closeFriendRequestPopup('${userId}')">
                <img src="/icon/close_black.svg" draggable="false"></button>
            </div>
        </div>
    `;
    friendRequest.insertAdjacentHTML('beforeend', friendRequestPopup);

    friendRequestTimeout = setTimeout(function() {
        closeFriendRequestPopup(userId);
    }, 7500);
}

function closeFriendRequestPopup(userId) {
    clearTimeout(friendRequestTimeout);

    const popup = document.querySelector(`#friend-request-${userId}`);
    if (popup) {
        popup.remove();
    }
}

async function sendInvite(userId, gameMode, lobbyId=null) {
    const invitePopupContainer = document.querySelector("#sent-invite-popup");

    const invites = invitePopupContainer.querySelectorAll(".sent-invite-popup");
    for (const invite of invites) {
        const oldUserId = invite.getAttribute("userId");

        if (oldUserId === userId) {
            createGeneralPopup("Je hebt al een uitnodiging gestuurd naar deze persoon", "error")
            return;
        }
    }

    const response = await fetch(`/api/users/${userId}/invite`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify({game_mode: gameMode, lobby_id: lobbyId})
    });

    const responseJson = await handleJsonResponse(response);
    if (responseJson) {
        const data = responseJson.data;
        createSentInvitePopup(data["invite_id"], data["user_id"], data["username"], data["pfp_version"]);
    }
}

async function rejectInvite(inviteId){
    const response = await fetch(`/api/invites/${inviteId}/reject`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    await handleJsonResponse(response);
}