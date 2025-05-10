function sortUsersByCreatedAt(users) {
    const sortedEntries = Object.entries(users).sort((a, b) => b[1].created_at - a[1].created_at);
    return Object.fromEntries(sortedEntries);
}

async function getMyFriends() {
    const response = await fetch("/api/friends", {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    const responseJson = await handleJsonResponse(response);
    if (responseJson) {
        return responseJson["friends"];
    }
}

async function removeFriend(userId, removeUserFromList) {
    const response = await fetch(`/api/friends/${userId}`, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    const responseJson = await handleJsonResponse(response);
    if (responseJson) {
        if (removeUserFromList) {
            const userDiv = document.querySelector(`#user-${userId}.friend`);
            userDiv.remove();
        } else {
            const userDiv = document.querySelector(`#user-${userId}.search-user`);
            userDiv.querySelector(".friend-button").innerHTML = `<button class="status-button no-friend" onclick="sendFriendRequest('${userId}')"><img src="/icon/add.svg" draggable="false"></button>`;
        }
    }
}

async function getSentFriendRequests() {
    const response = await fetch("/api/friend_request/sent", {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    const responseJson = await handleJsonResponse(response);
    if (responseJson) {
        return responseJson["friend_requests"];
    }
}

async function getReceivedFriendRequests() {
    const response = await fetch("/api/friend_request/received", {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    const responseJson = await handleJsonResponse(response);
    if (responseJson) {
        return responseJson["friend_requests"];
    }
}

async function cancelFriendRequest(userId) {
    const response = await fetch(`/api/friend_request/${userId}/cancel`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    const responseJson = await handleJsonResponse(response);
    if (responseJson) {
        document.querySelector(`#user-${userId}.sent-friend-request`).remove();
    }
}

async function updateUserList() {
    const input = document.querySelector("#friends-search-input").value;
    const users = await getUsers(input, 15, true);

    const userList = document.querySelector(".user-list");

    userList.innerHTML = "";

    for (const user of users) {
        let button;
        if (user["friend_request_status"] === "friend") {
            button = `
                <div class="friend-button">
                    <div class="more-dropdown" onclick="toggleMore(this)">
                    <button class="status-button more"><img src="/icon/more.svg" draggable="false"></button>
    
                        <div class="dropdown-content">
                            <button onclick="sendInvite('${user['user_id']}', 'one_vs_one')">1v1</button>
                            <button onclick="removeFriend('${user['user_id']}', false)">Verwijder Vriend</button>
                        </div>
                    </div>
                </div>
            `;
        } else if (user["friend_request_status"] === "request_received") {
            button = `
                <div class="friend-button"><button class="status-button accept" onclick="acceptFriendRequest('${user['user_id']}', 'search-user')"><img src="/icon/check.svg" draggable="false"></button><button class="status-button reject" onclick="rejectFriendRequest('${user['user_id']}', 'search-user')"><img src="/icon/close.svg" draggable="false"></button></div>
            `;
        } else if (user["friend_request_status"] === "request_sent") {
            button = `
                <div class="friend-button"><button class="status-button pending"><img src="/icon/hourglass.svg" draggable="false"></button></div>
            `;
        } else {
            button = `
                <div class="friend-button"><button class="status-button no-friend" onclick="sendFriendRequest('${user['user_id']}')"><img src="/icon/add.svg" draggable="false"></button></div>
            `;
        }

        const userElement = `
            <div id="user-${user['user_id']}" class="user search-user">
                <div class="user-profile">
                    <div class="tooltip">
                        <span class="tooltip-text">${user['status']}</span>
                        <div class="status ${user['status']}"></div>
                    </div>
                    <div class="pfp"><img loading="lazy" src="/api/users/${user['user_id']}/pfp?v=${user['pfp_version']}"></div>
                    <div class="username">${user['username']}</div>
                </div>
                ${button}
            </div>
        `;
        userList.insertAdjacentHTML('beforeend', userElement);
    }
}

async function createReceivedFriendRequestsList() {
    const friendRequests = await getReceivedFriendRequests();
    const myFriendsContainer = document.querySelector(".received-friend-requests-list");

    myFriendsContainer.innerHTML = "";

    if (Object.keys(friendRequests).length === 0) {
        myFriendsContainer.innerHTML = `
            <a href="/of" target="_blank">
                <div class="lmao-no-friends"">
                    <img src="/img/no_friends_only_fans.png">
                </div>
            </a>
        `;
    }

    const sortedFriendRequests = sortUsersByCreatedAt(friendRequests);

    for (const userId in sortedFriendRequests) {
        const userElement = `
            <div id="user-${userId}" class="user received-friend-request">
                <div class="user-profile">
                    <div class="tooltip">
                        <span class="tooltip-text">${sortedFriendRequests[userId]['status']}</span>
                        <div class="status ${sortedFriendRequests[userId]['status']}"></div>
                    </div>
                    <div class="pfp"><img src="/api/users/${userId}/pfp?v=${sortedFriendRequests[userId]['pfp_version']}"></div>
                    <div class="username">${sortedFriendRequests[userId]['username']}</div>
                </div>
                <div class="friend-button"><button class="status-button accept" onclick="acceptFriendRequest('${userId}', 'received-friend-request')"><img src="/icon/check.svg" draggable="false"></button><button class="status-button reject" onclick="rejectFriendRequest('${userId}', 'received-friend-request')"><img src="/icon/close.svg" draggable="false"></button></div>
            </div>
        `;

        myFriendsContainer.insertAdjacentHTML('beforeend', userElement);
    }
}

async function createSentFriendRequestsList() {
    const friendRequests = await getSentFriendRequests();
    const myFriendsContainer = document.querySelector(".sent-friend-requests-list");

    myFriendsContainer.innerHTML = "";

    if (Object.keys(friendRequests).length === 0) {
        myFriendsContainer.innerHTML = `
            <a href="/of" target="_blank">
                <div class="lmao-no-friends"">
                    <img src="/img/no_friends_only_fans.png">
                </div>
            </a>
        `;
    }

    const sortedFriendRequests = sortUsersByCreatedAt(friendRequests);

    for (const userId in sortedFriendRequests) {
        const userElement = `
            <div id="user-${userId}" class="user sent-friend-request">
                <div class="user-profile">
                    <div class="tooltip">
                        <span class="tooltip-text">${sortedFriendRequests[userId]['status']}</span>
                        <div class="status ${sortedFriendRequests[userId]['status']}"></div>
                    </div>
                    <div class="pfp"><img src="/api/users/${userId}/pfp?v=${sortedFriendRequests[userId]['pfp_version']}"></div>
                    <div class="username">${sortedFriendRequests[userId]['username']}</div>
                </div>
                <div class="friend-button"><button class="status-button cancel" onclick="cancelFriendRequest('${userId}')"><img src="/icon/cancel.svg" draggable="false"></button></div>
            </div>
        `;

        myFriendsContainer.insertAdjacentHTML('beforeend', userElement);
    }
}

async function createMyFriendsList() {
    const friends = await getMyFriends();
    const myFriendsContainer = document.querySelector(".friend-list");

    myFriendsContainer.innerHTML = "";

    if (Object.keys(friends).length === 0) {
        myFriendsContainer.innerHTML = `
            <a href="/of" target="_blank">
                <div class="lmao-no-friends"">
                    <img src="/img/no_friends_only_fans.png">
                </div>
            </a>
        `;
    }

    for (const userId in friends) {
        const userElement = `
            <div id="user-${userId}" class="user friend">
                <div class="user-profile">
                    <div class="tooltip">
                        <span class="tooltip-text">${friends[userId]['status']}</span>
                        <div class="status ${friends[userId]['status']}"></div>
                    </div>
                    <div class="pfp"><img src="/api/users/${userId}/pfp?v=${friends[userId]['pfp_version']}"></div>
                    <div class="username">${friends[userId]['username']}</div>
                </div>
                
                <div class="friend-button">
                    <div class="more-dropdown" onclick="toggleMore(this)">
                        <button class="status-button more"><img src="/icon/more.svg" draggable="false"></button>
    
                        <div class="dropdown-content">
                            <button onclick="sendInvite('${userId}', 'one_vs_one')">1v1</button>
                            <button onclick="removeFriend('${userId}', true)">Verwijder Vriend</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        myFriendsContainer.insertAdjacentHTML('beforeend', userElement);
    }
}

async function openFriendsTab(tabName) {
    if (document.querySelector(`#${tabName}-content`).classList.contains("show")) {
        return;
    }

    if (tabName === "my-friends") {
        await createMyFriendsList();
    } else if (tabName === "add-friends") {
        await updateUserList();
    } else if (tabName === "received-friend-requests") {
        await createReceivedFriendRequestsList();
    } else if (tabName === "sent-friend-requests") {
        await createSentFriendRequestsList();
    }

    document.querySelectorAll('.friends-section').forEach(section => {
        section.classList.remove('show');
    });

    document.querySelectorAll('.nav-item').forEach(nav => {
        nav.classList.remove('selected');
    });
    document.querySelector(`#${tabName}-nav`).classList.add('selected');

    setTimeout(() => {
        document.querySelectorAll('.friends-section').forEach(section => {
            section.style.display = 'none';
        });

        const section = document.querySelector(`#${tabName}-content`);
        section.style.display = '';

        setTimeout(() => {
            section.classList.add('show');
        }, 1)
    }, 300)
}

function toggleMore(div) {
    div.classList.toggle('active');

    const actives = document.querySelectorAll(".more-dropdown.active");

    for (let i = 0; i < actives.length; i++) {
        if (actives[i] !== div) {
            actives[i].classList.remove('active');
        }
    }
}

window.isOnFriendsPage = true;

openFriendsTab("my-friends");

let userListUpdateTimeout;
document.querySelector("#friends-search-input").addEventListener("input", (e) => {
    clearTimeout(userListUpdateTimeout);

    userListUpdateTimeout = setTimeout(function () {
        updateUserList();
    }, 200)
});

document.addEventListener('click', function (event) {
    const dropdown = document.querySelector(".more-dropdown.active")

    if (!dropdown) {
        return;
    }

    const button = dropdown.parentElement;
    const dropdownContent = dropdown.querySelector(".dropdown-content");

    if (dropdownContent && !button.contains(event.target)) {
        dropdown.classList.remove('active');
    }
});
