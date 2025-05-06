let board = {
    cols: 15,
    rows: 15
};

const boxes = document.getElementsByClassName("box");

let snake = {
    direction: "right",
    prevDirection: "right",
    nextDirection: "right",
    position: [
        [3, 7],
        [4, 7],
        [5, 7],
        [6, 7],
        [7, 7],
    ],
    food: 0,
    init: function () {
        snake.direction = "right";
        snake.prevDirection = "right";
        snake.nextDirection = "right";
        snake.spawnLen = document.getElementById("spawn-len-input").value;
        snake.spawnX = Math.floor((board.cols / 2)) - snake.spawnLen;
        snake.spawnY = Math.floor((board.rows / 2));

        snake.position = [];
        for (let i = 0; i < snake.spawnLen; i++) {
            snake.position.push([snake.spawnX + i, snake.spawnY]);
        }

        snake.interval = document.getElementById("update-interval-input").value * 1000;
        snake.food = 0;
        snake.score = 0;
        snake.time = 0;
        snake.isAlive = true;
    },
};


function updatePositions(newHead) {
    // Remove the tail unless snake hit food, then keep the tail so the snake grows
    snake.position.shift();

    // Add the new head
    snake.position.push(newHead);
}

function move() {
    if (!snake.isAlive) return; // Stop moving if snake is dead

    snake.direction = snake.nextDirection;

    // Calculate the next head position
    let head = snake.position[snake.position.length - 1];
    let newHead;

    // Prevent opposite direction changes
    if (
        (snake.prevDirection === "left" && snake.direction === "right") ||
        (snake.prevDirection === "right" && snake.direction === "left") ||
        (snake.prevDirection === "up" && snake.direction === "down") ||
        (snake.prevDirection === "down" && snake.direction === "up")
    ) {
        snake.direction = snake.prevDirection;
    }

    switch (snake.direction) {
        case "left":
            newHead = [head[0] - 1, head[1]];
            break;
        case "up":
            newHead = [head[0], head[1] - 1];
            break;
        case "right":
            newHead = [head[0] + 1, head[1]];
            break;
        case "down":
            newHead = [head[0], head[1] + 1];
            break;
    }

    if (hitBorder(newHead) || hitSnake(newHead)) {
        snake.isAlive = false;
        renderSnake(userId, snake.position, pfpVersion);
        return;
    }


    // Update the snake's position
    updatePositions(newHead);
    renderSnake(userId, snake.position, pfpVersion);

    snake.prevDirection = snake.direction;
    snake.nextDirection = snake.direction;
}

function hitBorder(newHead) {
    return (
        newHead[0] < 0 ||
        newHead[0] >= board.cols ||
        newHead[1] < 0 ||
        newHead[1] >= board.rows
    );
}

function hitSnake(newHead) {
    for (let i = 0; i < snake.position.length; i++) {
        // LAST PART OF SNAKE SHOULD BE IGNORED
        if (i === 0) {
            continue;
        }
        if (snake.position[i][0] === newHead[0] && snake.position[i][1] === newHead[1]) {
            return true;
        }
    }
    return false;
}

function turn(e) {
    let direction;
    switch (e.keyCode) {
        case 37:
            direction = "left";
            break;
        case 38:
            direction = "up";
            break;
        case 39:
            direction = "right";
            break;
        case 40:
            direction = "down";
            break;
        default:
            return;
    }
    e.preventDefault(); // Stop scrolling issues

    // Prevent opposite direction changes
    if (
        (direction === "left" && snake.direction !== "right") ||
        (direction === "right" && snake.direction !== "left") ||
        (direction === "up" && snake.direction !== "down") ||
        (direction === "down" && snake.direction !== "up")
    ) {
        snake.nextDirection = direction;
    }
}

function previewGameLoop() {
    if (!snake.isAlive) {
        startPreview();
        return;
    }

    for (const box of boxes) {
        box.classList.remove("snake");
        box.classList.remove("food");
        box.style.backgroundImage = "";
    }

    move();
    gameLoopTimeout = setTimeout(previewGameLoop, snake.interval);
}

function startPreview() {
    clearTimeout(gameLoopTimeout);

    snake.init();
    document.addEventListener("keydown", turn, { passive: false });
    gameLoopTimeout = setTimeout(previewGameLoop, snake.interval);
}

function createBoardPreview(rows, cols) {
    const boardPreview = document.querySelector(".snake-board");
    boardPreview.innerHTML = "";

    board.rows = rows;
    board.cols = cols;
    snake.init();
    snake.isAlive = false;

    for (let i = 0; i < rows*cols; i++) {
        let divElt = document.createElement("div");
        divElt.classList.add("box");
        boardPreview.appendChild(divElt);
    }

    document.documentElement.style.setProperty("--board-grid-rows", rows);
    document.documentElement.style.setProperty("--board-grid-cols", cols);

    document.documentElement.style.setProperty("--board-grid-size", "15px");

    if (rows > 30) {
        document.documentElement.style.setProperty("--board-grid-size", `${600/Math.max(rows, cols)}px`);
    }
}

function openPreviewPopup() {
    const rows = document.getElementById("rows-input").value;
    const cols = document.getElementById("cols-input").value;
    createBoardPreview(rows, cols);

    document.querySelector("#preview-popup").classList.add("show");
    startPreview();
}

function closePreviewPopup() {
    document.querySelector("#preview-popup").classList.remove("show");
    clearTimeout(gameLoopTimeout);
    snake.isAlive = false;
    snake.init();

    const boardPreview = document.querySelector(".snake-board");
    boardPreview.innerHTML = "";
}

async function updateUserList(query, limit) {
    const users = await getUsers(query, limit);

    const userList = document.querySelector(".user-list");

    userList.innerHTML = "";

    for (const user of users) {
        if (playerList.includes(user['user_id'])) {
            continue;
        }

        const userElement = `
            <div id="user-${user['user_id']}" class="user search-user">
                <div class="user-profile">
                    <div class="status ${user['status']}"></div>
                    <div class="pfp"><img loading="lazy" src="/api/users/${user['user_id']}/pfp?v=${user['pfp_version']}"></div>
                    <div class="username">${user['username']}</div>
                </div>
                
                <div class="friend-button">
                    <button class="status-button no-friend" onclick="sendLobbyInvite('${user['user_id']}', 'custom', lobbyId)">
                        <img src="/icon/add.svg" draggable="false">
                    </button>
                </div>
            </div>
        `;
        userList.insertAdjacentHTML('beforeend', userElement);
    }
}

async function createGame() {
    sendFormData();

    const response = await fetch(`/api/lobby/${lobbyId}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    await handleJsonResponse(response);
}

async function sendLobbyInvite(userId, gameMode, lobbyId=null) {
    if (playerList.includes(userId)) {
        createGeneralPopup("Speler zit al in deze lobby", "error")
        return;
    }

    await sendInvite(userId, gameMode, lobbyId);
}

function toggleMore(div) {
    const dropDown = div.querySelector(".more-dropdown");
    dropDown.classList.toggle('active');

    const actives = document.querySelectorAll(".more-dropdown.active");

    for (let i = 0; i < actives.length; i++) {
        if (actives[i] !== dropDown) {
            actives[i].classList.remove('active');
        }
    }
}

async function kickPlayer(userId) {
    const response = await fetch(`/api/lobby/${lobbyId}/players/${userId}`, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    await handleJsonResponse(response);
}

function createJoinedUserList(playersData) {
    const playerContainer = document.querySelector(".joined-players .user-list");
    playerContainer.innerHTML = "";

    for (const playerId in playersData) {
        let kickButton = ``;
        let friendButton = ``;
        let ownerIcon = ``;

        if (playerId !== userId) {
            if (isOwner) {
                kickButton = `
                    <button onclick="kickPlayer('${playerId}')">Kicken</button>
                `;
            }

            if (playersData[playerId]["owner"]) {
                ownerIcon = `
                    <img class="owner" src="/icon/crown.svg" draggable="false">
                `;
            }

            friendButton = `
                <div class="friend-button" onclick="toggleMore(this)">                
                    ${ownerIcon}
                    <button class="more status-button">
                        <img src="/icon/more.svg" draggable="false">
                    </button>
        
                    <div class="more-dropdown">
                        <div class="dropdown-content">
                            <button onclick="sendFriendRequest('${playerId}')">Vriendschapsverzoek Sturen</button>
                            <button onclick="">Profiel Bekijken</button>
                            ${kickButton}
                        </div>
                    </div>
                </div>
            `;
        }

        const playerDiv = `
            <div class="user">
                <div class="user-profile">
                    <div class="pfp"><img src="/api/users/${playerId}/pfp?v=${playersData[playerId]['pfp_version']}"></div>
                    <div class="username">${playersData[playerId]['username']}</div>
                </div>
                ${friendButton}
            </div>
        `;
        playerContainer.insertAdjacentHTML('afterbegin', playerDiv);
    }
}


function rowsUpdate() {
    sanitizeNumericInputs("rows-input", 15, 10, 75);
}

function colsUpdate() {
    sanitizeNumericInputs("cols-input", 15, 10, 75);
}

function growUpdate() {
    sanitizeNumericInputs("snake-grow-input", 1, 1, 15);
}

function foodAmountUpdate() {
    sanitizeNumericInputs("food-amount-input", 1, 1, 15);
}

function spawnLenUpdate() {
    const rows = document.getElementById("rows-input").value;
    const cols = document.getElementById("cols-input").value;
    const maxSpawnLen = Math.floor(Math.max(rows, cols) / 2) - 1;

    sanitizeNumericInputs("spawn-len-input", 4, 1, maxSpawnLen);
}

function sanitizeNumericInputs(inputId, defaultValue, min, max) {
    const input = document.getElementById(inputId);
    let value = input.value;

    if (isNaN(value)) {
        value = defaultValue
        input.value = value;
    } else {
        if (value > max) {
            value = max;
            input.value = value;
        } else if (value < min) {
            value = min;
            input.value = value;
        }
    }
}

function sendFormData() {
    const cols = document.querySelector("#cols-input").value;
    const rows = document.querySelector("#rows-input").value;
    const updateInterval = document.querySelector("#update-interval-input").value;
    const spawnLen = document.querySelector("#spawn-len-input").value;
    const grow = document.querySelector("#snake-grow-input").value;
    const foodAmount = document.querySelector("#food-amount-input").value;

    const formData = {
        "board": {
            "cols": cols,
            "rows": rows,
        },
        "update_interval": updateInterval,
        "spawn_len": spawnLen,
        "grow": grow,
        "food_amount": foodAmount
    }

    lobbySocket.emit("settings_update", formData);
}

function toggleVisibility() {
    const tokenInput = document.querySelector("#join-token");
    const visibilityIcon = document.querySelector(".visibility img");

    if (tokenInput.type === "text") {
        tokenInput.type = "password";
        visibilityIcon.src = "/icon/visibility_off.svg";
    } else {
        tokenInput.type = "text";
        visibilityIcon.src = "/icon/visibility.svg";
    }
}

let isOwner = false;
let playerList;
let pfpVersion;
let gameLoopTimeout;
let userListUpdateTimeout;
const lobbyId = window.location.pathname.split("/")[2];
const userId = localStorage.getItem("userId");
createBoardPreview(15, 15);

const lobbySocket = io(`/ws/lobby?lobby_id=${lobbyId}`, { forceNew: true });

lobbySocket.on("connect", () => {
    console.log("Connected!")
});

lobbySocket.on("game_start", (data) => {
    window.location.href = data["redirect_url"];
});

lobbySocket.on("player_update", (playersData) => {
    if (!Object.keys(playersData).includes(userId)) {
        window.location.href = "/snake";
        return;
    }
    playerList = Object.keys(playersData);

    createJoinedUserList(playersData);
    pfpVersion = playersData[userId]["pfp_version"];

    if (isOwner) {
        const input = document.querySelector("#user-search-input").value;
        updateUserList(input, 8);
    }
});

lobbySocket.on("owner_status", () => {
    isOwner = true;

    document.querySelector(".place-holder").outerHTML = `
        <div class="invite-users">
            <div class="player-search">
                <div class="input search-input">
                    <input id="user-search-input" type="text" placeholder="Nodig spelers uit" name="user-search">
                </div>
            </div>

            <div class="user-list"></div>
        </div>
    `;

    const form = document.querySelector("#create-game-form")

    const submitButton = `
        <button type="submit" >
            <i style="display: none;" class="fa fa-circle-o-notch fa-spin"></i> Maak Game
        </button>
    `;

    form.insertAdjacentHTML('beforeend', submitButton);

    // Enable all inputs in form
    const inputs = form.querySelectorAll("input");
    for (let i = 0; i < inputs.length; i++) {
        const input = inputs[i];
        input.disabled = false;
    }

    form.addEventListener("change", function (e) {
        sendFormData();
    });

    updateUserList("", 8);

    document.querySelector("#user-search-input").addEventListener("input", (e) => {
        clearTimeout(userListUpdateTimeout);

        userListUpdateTimeout = setTimeout(function () {
            const input = document.querySelector("#user-search-input").value;
            updateUserList(input, 8);
        }, 200)
    });
});

lobbySocket.on("settings_update", (data) => {
    document.querySelector("#cols-input").value = data["board"]["cols"];
    document.querySelector("#rows-input").value = data["board"]["rows"];
    document.querySelector("#update-interval-input").value = data["update_interval"];
    document.querySelector("#spawn-len-input").value = data["spawn_len"];
    document.querySelector("#snake-grow-input").value = data["grow"];
    document.querySelector("#food-amount-input").value = data["food_amount"];

    snake.interval = document.getElementById("update-interval-input").value * 1000;
    rowsUpdate();
    colsUpdate();
    spawnLenUpdate();
    growUpdate();
    foodAmountUpdate();
});

lobbySocket.on("leave_lobby", () => {
    console.log("Need to leave lobby");
    window.location.href = "/snake";
});

document.getElementById("create-game-form").addEventListener("submit", async function(event) {
    event.preventDefault();
    clearCatErrors();

    document.querySelector("#create-game-form button i").style.display = "";
    await createGame();
    document.querySelector("#create-game-form button i").style.display = "none";
});

document.getElementById("rows-input").addEventListener("focusout", function() {
    rowsUpdate();
});

document.getElementById("cols-input").addEventListener("focusout", function() {
    colsUpdate();
});

document.getElementById("spawn-len-input").addEventListener("focusout", function() {
    spawnLenUpdate();
});

document.getElementById("snake-grow-input").addEventListener("focusout", function() {
    growUpdate();
});

document.getElementById("food-amount-input").addEventListener("focusout", function() {
    foodAmountUpdate();
});

document.getElementById("update-interval-input").addEventListener("input", function() {
    snake.interval = document.getElementById("update-interval-input").value * 1000;
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
