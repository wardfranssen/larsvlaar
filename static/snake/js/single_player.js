function startSnake() {
    clearInterval(countdownInterval);
    countdownDiv.classList.remove("start");
}

function stopp(score) {
    document.removeEventListener("keydown", turn, { passive: false });

    popup.querySelector(".text").innerText = `${score} puntjes!`;

    popupBackground.classList.remove("hidden");
}

const scoreSpan = document.querySelector(".score");
let snakeBoard = document.querySelector(".snake-board");
let popupBackground = document.querySelector(".game-popup-background");
let boxes;
let score;
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
let popup = document.querySelector(".popup");

const countdownDiv = document.querySelector('.countdown');
let countdownCount = 3;
let countdownInterval;
const userId = localStorage.getItem("userId");


boardCreation()
document.addEventListener("keydown", (e) => {
    if (!e.repeat) {
        turn(e)
    }
}, { passive: false });


gameSocket = io(`/ws/single_player/game?game_id=${gameId}`, { forceNew: true });

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

    for (const box of boxes) {
        box.classList.remove("snake");
        box.classList.remove("food");
        box.style.backgroundImage = "";
    }

    scoreSpan.innerText = `${players[userId]["score"] ?? 0} puntjes`;
    renderSnake(userId, players[userId]["snake_pos"], players[userId]["pfp_version"]);

    for (const foodPos of foodPositions) {
        renderFood(foodPos[0], foodPos[1]);
    }
});

gameSocket.on('leave_game', () => {
    gameSocket.disconnect();
    window.window.location.href = "/snake";
});

gameSocket.on('game_over', (data) => {
    saveReplayThumbnail(gameId);
    gameIsOver = true;

    stopp(data);
});


gameSocket.on("disconnect", () => {
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
