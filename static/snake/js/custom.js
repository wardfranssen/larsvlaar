function startSnake() {
    clearInterval(countdownInterval);
    countdownDiv.classList.remove("start");
}

async function sendSnakeDir(direction) {
    gameSocket.emit('snake_dir', {"snake_dir": direction});
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

    sendSnakeDir(direction);
}

function ready() {
    gameSocket.emit("ready");
    popup.querySelector(".text").innerText = "Wachten op tegenstander...";
    popup.querySelector(".button").style = "display: none;";
}

async function saveReplayThumbnail(gameId) {
    const board = document.querySelector(".snake-board");

    // Take snapshot
    const canvas = await html2canvas(board, {
        scale: 0.5,
        width: board.offsetWidth,
        height: board.offsetHeight
    });
    const dataURL = canvas.toDataURL("image/png");

    // Upload to server
    const response = await fetch(`/api/games/${gameId}/upload_thumbnail`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify({
            image: dataURL
        })
    });

    await handleJsonResponse(response);
}

function kickPlayer(userId) {
    if (isOwner) {
        gameSocket.emit("kick_user", userId);
    }
}


function createUserList(playersData, kickButtons=false) {
    const playerContainer = document.querySelector(".user-list");
    playerContainer.innerHTML = "";

    for (const [playerId, player] of Object.entries(playersData)) {
        let kickButton = "";
        let statusIcon = "";

        if (playerId !== currentUserId) {
            if (isOwner && kickButtons) {
                kickButton = `
                    <div class="friend-button">                
                        <button class="close status-button" onclick="kickPlayer('${playerId}')">
                            <img src="/icon/close_black.svg" draggable="false">
                        </button>
                    </div>
                `;
            }

            statusIcon = `
                <img src="/icon/not_connected.svg" draggable="false">
            `;

            if (player["connected"]) {
                statusIcon = `
                <img src="/icon/connected.svg" draggable="false">
            `;
            }
        }

        let placement = "";
        if (player.hasOwnProperty("placement")) {
            placement = `#${player["placement"]}`;
        }

        const playerDiv = `
            <div class="user" id="user-${playerId}">
                <div class="user-profile">
                    <div class="pfp"><img src="/api/users/${playerId}/pfp?v=${player['pfp_version']}"></div>
                    <div class="username">${player['username']}</div>
                </div>
                
                <div class="score">
                    Score: 0
                </div>
                
                <div class="status-icon">
                    ${statusIcon}
                </div>
                
                <div class="placement">
                    ${placement}
                </div>
                
                ${kickButton}
            </div>
        `;
        playerContainer.insertAdjacentHTML('afterbegin', playerDiv);
    }
}

function startGame() {
    gameSocket.emit("start_game");
}

function closePopup() {
    document.querySelector(".game-popup-background").classList.add("hidden");
}

function createLeaderboard(leaderboardData) {
    const leaderboard = document.querySelector(".leaderboard");
    const usersContainer = leaderboard.querySelector(".users");
    usersContainer.innerHTML = "";


    for (const [placement, player] of Object.entries(leaderboardData)) {
        let specialPlacement = "";
        let currentUser = "";
        if (placement === "1") {
            specialPlacement = "first";
        } else if (placement === "2") {
            specialPlacement = "second";
        } else if (placement === "3") {
            specialPlacement = "third";
        }
        if (player["user_id"] === currentUserId) {
            currentUser = "current-user";
        }

        const userDiv = `
            <div id="leaderboard-user-${player["user_id"]}" class="user ${specialPlacement} ${currentUser}">
                <div class="placement">#${placement}</div>

                <div class="user-profile">
                    <div class="pfp"><img src="/api/users/${player["user_id"]}/pfp?v=${player["pfp_version"]}"></div>
                    <div class="username">${player["username"]}</div>
                </div>
                
                <div class="rematched">
                    <img src="/icon/repeat.svg" draggable="false">
                </div>
            </div>
        `;
        usersContainer.insertAdjacentHTML('beforeend', userDiv);
    }
}

function updateScore(scoreData) {
    const [[playerId, score]] = Object.entries(scoreData);
    console.log(playerId, score);
    document.querySelector(`#user-${playerId} .score`).innerText = `Score: ${score}`;
}

function rematch() {
    gameSocket.emit("rematch");
}

const scoreSpan = document.querySelector(".score");
let snakeBoard = document.querySelector(".snake-board");
let popupBackground = document.querySelector(".game-popup-background");
let boxes;
let score;
let board;
let isOwner = false;

let gameSocket;
const urlParams = window.location.search;
const params = new URLSearchParams(urlParams);
const gameId = params.get("game_id");
let popup = document.querySelector(".popup");

const countdownDiv = document.querySelector('.countdown');
let countdownCount = 5;
let countdownInterval;
let userPfpVersion;
let opponents;
let gameHasStarted = false;
const currentUserId = localStorage.getItem("userId");

document.addEventListener("keydown", (e) => {
    if (!e.repeat) {
        turn(e)
    }
}, { passive: false });

gameSocket = io(`/ws/custom/game?game_id=${gameId}`, { forceNew: true });

gameSocket.on("connect", () => {
    startChatSocket(gameId, "game_id");
});

gameSocket.on("join_lobby", () => {
    window.location.href = `/lobby/${gameId}`;
});

gameSocket.on("player_rematch", (data) => {
    const usersOnLeaderboard = document.querySelectorAll(".leaderboard .user");

    for (const user of usersOnLeaderboard) {
        const rematchedDiv = user.querySelector(".rematched");
        rematchedDiv.classList.remove("show");
    }

    for (const userId of data["users"]) {
        console.log(userId);
        const userRematchDiv = document.querySelector(`#leaderboard-user-${userId} .rematched`);
        userRematchDiv.classList.add("show");
    }
});

gameSocket.on('countdown_start', () => {
    const kickButtons = document.querySelectorAll(".friend-button");

    kickButtons.forEach(kickButton => {
        kickButton.remove();
    });

    countdownDiv.classList.add("start");
    countdownInterval = setInterval(updateCountdown, 1000);

    if (isOwner) {
        document.querySelector(".start-game").remove();
    }
});

gameSocket.on("died", (data) => {
    // Todo: Create thing like the countdown to show what place player ended
    const placement = data["placement"]

    countdownDiv.querySelector("span").innerText = `#${placement}`;
    countdownDiv.classList.add("start");
    setTimeout(() => {
        countdownDiv.classList.remove("start");
    }, 1000);

    document.removeEventListener("keydown", turn, { passive: false });
});

gameSocket.on("game_start", () => {
    startSnake();
});

gameSocket.on("score_update", (data) => {
    updateScore(data);
});

gameSocket.on("board", (data) => {
    const rows = data["rows"];
    const cols = data["cols"];

    board = {
        rows: rows,
        cols: cols,
        boxes: rows * cols,
    }

    document.documentElement.style.setProperty("--board-grid-rows", rows);
    document.documentElement.style.setProperty("--board-grid-cols", cols);

    document.documentElement.style.setProperty("--board-grid-size", "6vh");
    const sizeIndicator = Math.max(rows, cols);

    if (sizeIndicator > 10) {
        document.documentElement.style.setProperty("--board-grid-size", "5vh");
    } if (sizeIndicator > 17) {
        document.documentElement.style.setProperty("--board-grid-size", "4vh");
    } if (sizeIndicator > 20) {
        document.documentElement.style.setProperty("--board-grid-size", "3vh");
    } if (sizeIndicator > 28) {
        document.documentElement.style.setProperty("--board-grid-size", "2.5vh");
    } if (sizeIndicator > 34) {
        document.documentElement.style.setProperty("--board-grid-size", "2.2vh");
    } if (sizeIndicator > 39) {
        document.documentElement.style.setProperty("--board-grid-size", "2vh");
    } if (sizeIndicator > 49) {
        document.documentElement.style.setProperty("--board-grid-size", "1.6vh");
    } if (sizeIndicator > 59) {
        document.documentElement.style.setProperty("--board-grid-size", "1.4vh");
    } if (sizeIndicator > 64) {
        document.documentElement.style.setProperty("--board-grid-size", "1.1vh");
    }
    boardCreation();
});

gameSocket.on("players", (data) => {
    opponents = data;

    if (!Object.keys(opponents).includes(currentUserId)) {
        window.location.href = "/snake";
        return;
    }

    if (gameHasStarted) {
        createUserList(opponents);
    } else {
        createUserList(opponents, true);
    }
});

gameSocket.on("game_update", (data) => {
    const foodPositions = data.food;
    const players = data.players;

    gameHasStarted = true;

    if (!userPfpVersion && players.hasOwnProperty(currentUserId)) {
        userPfpVersion = players[currentUserId]["pfp_version"];
    }

    const startButton = document.querySelector(".start-game");
    if (startButton) {
        startButton.remove();
    }
    const kickButtons = document.querySelectorAll(".user-list .friend-button");
    kickButtons.forEach(kickButton => {
        kickButton.remove();
    });

    for (const box of boxes) {
        box.classList.remove("snake");
        box.classList.remove("food");
        box.style.backgroundImage = "";
    }

    console.log(players);
    for (const playerId in players) {
        if (playerId === currentUserId) {
            scoreSpan.innerText = `${players[playerId]["score"] ?? 0} puntjes`;
        }
        renderSnake(playerId, players[playerId]["snake_pos"], players[playerId]["pfp_version"]);
    }

    for (const foodPos of foodPositions) {
        renderFood(foodPos[0], foodPos[1]);
    }
});

gameSocket.on("leave_game", () => {
    gameSocket.disconnect();
    window.window.location.href = "/snake";
});

gameSocket.on("owner_status", () => {
    isOwner = true;
    const startButton = `
        <div class="buttons start-game">
            <button onclick="startGame()">Start Game</button>
        </div>
    `;

    document.querySelector(".side-panel").insertAdjacentHTML("beforeend", startButton);
});

gameSocket.on("game_over", (data) => {
    saveReplayThumbnail(gameId);

    if (data["leaderboard"][1]["user_id"] === currentUserId) {
        confettiEffect(30);
    }

    popupBackground.classList.remove("hidden");
    createLeaderboard(data["leaderboard"]);
});

gameSocket.on("disconnect", () => {
    console.log("gameSocket disconnected");
    createGeneralPopup("Connectie is getermineerd", "error");
});


function confettiEffect(duration) {
    const end = Date.now() + duration * 1000;

    const colors = ["#ff0000", "#ff8000", "#ffd500", "#8cff00", "#00ebff", "#002aff", "#7300ff", "#ee00ff"];
    (function frame() {
        confetti({
            particleCount: 1,
            angle: 60,
            spread: 55,
            origin: { x: 0 },
            colors: colors,
        });

        confetti({
            particleCount: 2,
            angle: 60,
            spread: 30,
            origin: { x: 0 },
            colors: colors,
            shapes: ["image"],
            scalar: 3,
            shapeOptions: {
                image: [
                    {
                        src: "/img/lars.jpg",
                        width: 32,
                        height: 32,
                    },
                    {
                        src: "/img/lars_is_dik.png",
                        width: 32,
                        height: 32,
                    },
                    {
                        src: "/img/jon_rans.png",
                        width: 32,
                        height: 32,
                    },
                    {
                        src: "/img/lars_magister.jpg",
                        width: 32,
                        height: 32,
                    },
                    {
                        src: "/img/boze_lars.jpg",
                        width: 32,
                        height: 32,
                    },
                    {
                        src: "/img/vandalisme.jpg",
                        width: 32,
                        height: 32,
                    },
                    {
                        src: "/img/lars_badminton.jpg",
                        width: 32,
                        height: 32,
                    },
                    {
                        src: "/img/dikke_akka_veel_grip.jpg",
                        width: 32,
                        height: 32,
                    }
                ]
            }
        });

        confetti({
            particleCount: 1,
            angle: 120,
            spread: 55,
            origin: { x: 1 },
            colors: colors,
        });

        confetti({
            particleCount: 2,
            angle: 120,
            spread: 30,
            origin: { x: 1 },
            colors: colors,
            shapes: ["image"],
            scalar: 3,
            shapeOptions: {
                image: [
                    {
                        src: "/img/lars.jpg",
                        width: 32,
                        height: 32,
                    },
                    {
                        src: "/img/lars_is_dik.png",
                        width: 32,
                        height: 32,
                    },
                    {
                        src: "/img/jon_rans.png",
                        width: 32,
                        height: 32,
                    },
                    {
                        src: "/img/lars_magister.jpg",
                        width: 32,
                        height: 32,
                    },
                    {
                        src: "/img/boze_lars.jpg",
                        width: 32,
                        height: 32,
                    },
                    {
                        src: "/img/vandalisme.jpg",
                        width: 32,
                        height: 32,
                    },
                    {
                        src: "/img/lars_badminton.jpg",
                        width: 32,
                        height: 32,
                    },
                    {
                        src: "/img/dikke_akka_veel_grip.jpg",
                        width: 32,
                        height: 32,
                    }
                ]
            }
        });

        if (Date.now() < end) {
            requestAnimationFrame(frame);
        }
    })();
}
