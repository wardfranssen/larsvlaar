function startSnake() {
    clearInterval(countdownInterval);
    countdownDiv.classList.remove("start");
    popupBackground.classList.add("hidden");
    popup.querySelector(".game-popup-button").remove();
}

function stopp() {
    document.removeEventListener("keydown", turn, { passive: false });
    popup.querySelector(".opponent").remove();

    popup.innerHTML += `
        <span class="game-popup-button" onclick="window.location.href = '/snake';">Home</span>
    `;

    if (from === "matchmaking") {
        popup.innerHTML += `
            <span class="game-popup-button new-game" onclick="window.location.href = '/matchmaking?game_mode=one_vs_one';">Nieuwe game</span>
        `;
    } else if (from === "invite") {
        popup.innerHTML += `
            <span class="game-popup-button new-game" onclick="sendInvite('${opponentId}', 'one_vs_one')">Tegenstand Uitnodigen voor 1v1</span>
        `;
    }

    popupBackground.classList.remove("hidden");
}

function ready() {
    gameSocket.emit("ready");
    isReady = true;
    popup.querySelector(".text").innerText = "Wachten op tegenstander...";
    popup.querySelector(".game-popup-button").style = "display: none;";
}

const scoreSpan = document.querySelector(".score");
let snakeBoard = document.querySelector(".snake-board");
let popupBackground = document.querySelector(".game-popup-background");
let boxes;
let score;
let isReady;
let gameIsOver = false;

let board = {
    rows: 15,
    cols: 15,
    boxes: 15 * 15,
};

let gameSocket;
const urlParams = window.location.search;
const params = new URLSearchParams(urlParams);
const gameId = params.get("game_id");
const from = params.get("from");
let popup = document.querySelector(".popup");

const countdownDiv = document.querySelector('.countdown');
let countdownCount = 3;
let countdownInterval;

const opponent = JSON.parse(localStorage.getItem("opponent"));
const opponentUsername = opponent.username;
const opponentPfpVersion = opponent.pfpVersion;
const opponentId = opponent.userId;
let userPfpVersion;
const userId = localStorage.getItem("userId");

popup.querySelector(".pfp img").src = `/api/users/${opponentId}/pfp?v=${opponentPfpVersion}`;
popup.querySelector(".username").innerText = opponentUsername;
popup.querySelector(".text").innerText = "Klik op de knop om te beginnen.";

document.querySelector(".card .opponent .pfp img").src = `/api/users/${opponentId}/pfp?v=${opponentPfpVersion}`;
document.querySelector(".card .opponent .username").innerText = opponentUsername;

boardCreation()
document.addEventListener("keydown", (e) => {
    if (!e.repeat) {
        turn(e)
    }
}, { passive: false });


gameSocket = io(`/ws/one_vs_one/game?game_id=${gameId}`, { forceNew: true });

gameSocket.on('countdown_start', () => {
    popupBackground.classList.add("hidden");
    countdownDiv.classList.add("start");
    countdownInterval = setInterval(updateCountdown, 1000);
});

gameSocket.on("game_start", () => {
    startSnake();
});

gameSocket.on("game_update", (data) => {
    const foodPositions = data.food;
    const players = data.players;

    userPfpVersion = players[userId]["pfp_version"];

    for (const box of boxes) {
        box.classList.remove("snake");
        box.classList.remove("food");
        box.style.backgroundImage = "";
    }

    console.log(players);
    for (const playerId in players) {
        let pfpVersion = opponentPfpVersion;
        let ownSnake = false;
        if (playerId === userId) {
            scoreSpan.innerText = `${players[playerId]["score"] ?? 0} puntjes`;
            pfpVersion = userPfpVersion;
            ownSnake = true;
        }
        renderSnake(playerId, players[playerId]["snake_pos"], pfpVersion, players[playerId]["skin"], ownSnake);
    }

    for (const foodPos of foodPositions) {
        if (foodPos) {
            renderFood(foodPos[0], foodPos[1], players[userId]["food_skin"]);
        }
    }
});

gameSocket.on('leave_game', () => {
    gameSocket.disconnect();
    window.window.location.href = "/snake";
});

gameSocket.on('game_over', (data) => {
    saveReplayThumbnail(gameId);

    const winner = data.winner;
    const username = localStorage.getItem("username")
    gameIsOver = true;


    // Todo: Add some amazing music
    if (winner === "draw") {
        popup.querySelector(".text").innerText = "Als je niet ken winnen, moet je zorgen dat je niet verliest.";
        popup.querySelector(".title").innerText = "Gelijkspel";
    } else if (winner === userId) {
        confettiEffect(30);
        popup.querySelector(".text").innerText = "MASSIVE W";
        popup.querySelector(".title").innerText = "Gewonnen";
    } else {
        // Todo: Make sure text fits on tombstone
        // Todo: Make tombstone is positioned right on chromebook/smaller screen
        const date = new Date();
        const yyyy = date.getFullYear();
        let mm = date.getMonth() + 1; // Months start at 0
        let dd = date.getDate();

        if (dd < 10) dd = '0' + dd;
        if (mm < 10) mm = '0' + mm;

        const formattedDate = dd + '-' + mm + '-' + yyyy;

        const tombstone =
            `<div class="tombstone">
                <div class="tombstone-text">
                    <br><br><br>
                    ${username}
                    <br><br>
                    11-09-2001
                    <br>
                    ${formattedDate}
                </div>
            </div>`;

        document.querySelector(".container").innerHTML += tombstone;

        // Have to re-query
        popup = document.querySelector(".popup");
        popupBackground = document.querySelector(".game-popup-background");

        popup.querySelector(".text").innerText = "Meedoen is nog kutter als je verliest";
        popup.querySelector(".title").innerText = "Verloren";
    }

    stopp();
});

gameSocket.on("not_ready", () => {
    popup.querySelector(".text").innerText = "Klik op de knop om te beginnen.";
    popup.querySelector(".game-popup-button").style = "display: block;";
    console.log("not_ready");
});

gameSocket.on('opp_ready', () => {
    popup.querySelector(".text").innerText = "Tegenstander is klaar om te beginnen, nu jij nog.";
    console.log(opponentUsername);
});

gameSocket.on("opp_connected", () => {
    if (!isReady) {
        popup.querySelector(".text").innerText = "Klik op de knop om te beginnen.";
        popup.querySelector(".game-popup-button").style = "display: block;";
    }
    console.log("Opponent connected");
    createGeneralPopup("Tegenstander is verbonden", "success");
});

gameSocket.on("opp_disconnected", () => {
    if (!gameIsOver) {
        popup.querySelector(".text").innerText = "Klik op de knop om te beginnen.";
        popup.querySelector(".game-popup-button").style = "display: block;";
    }
    isReady = false;

    createGeneralPopup("Verbinding met tegenstander is verbroken", "error");
});

gameSocket.on("disconnect", () => {
    isReady = false;
    console.log("gameSocket disconnected");
    createGeneralPopup("Connectie is getermineerd", "error");
});


function confettiEffect(duration) {
    const end = Date.now() + duration * 1000;

    const colors = ["#ff0000", "#ff8000", "#ffd500", "#8cff00", "#00ebff", "#002aff", "#7300ff", "#ee00ff"];
    (function frame() {
        confetti({
            particleCount: 2,
            angle: 60,
            spread: 55,
            origin: { x: 0 },
            colors: colors,
        });

        confetti({
            particleCount: 1,
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
                        src: "/img/massive.jpg",
                        width: 32,
                        height: 32,
                    }
                ]
            }
        });

        confetti({
            particleCount: 2,
            angle: 120,
            spread: 55,
            origin: { x: 1 },
            colors: colors,
        });

        confetti({
            particleCount: 1,
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
                        src: "/img/massive.jpg",
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
