async function stopp() {
    document.removeEventListener("keydown", turn, { passive: false });
    popup.querySelector(".opponent").remove();

    popup.innerHTML += `
    <span class="button" onclick="window.location.href = '/snake';">Home</span>
    `;

    popup.innerHTML += `
    <span class="button new-game" onclick="window.location.href = '/matchmaking?game_mode=one_vs_one';">Nieuwe game</span>
    `;

    popupBackground.classList.remove("hidden");
}

function boardCreation() {
    if (snakeBoard.innerHTML === "") {
        for (let i = 0; i < board.boxes; i++) {
            let divElt = document.createElement("div");
            divElt.classList.add("box");
            snakeBoard.appendChild(divElt);
        }
    }
    boxes = document.getElementsByClassName("box");
}

function gameUpdate(gameData) {
    const foodPosition = gameData["food_pos"];
    const players = gameData["players"];

    for (const box of boxes) {
        box.classList.remove("food");
        box.classList.remove("snake");
    }

    for (const playerId in players) {
        const position = players[playerId]["snake_pos"];
        renderSnake(playerId, position, players[playerId]["pfp_version"]);
    }

    if (foodPosition) {
        renderFood(foodPosition[0], foodPosition[1]);
    }
}

const urlParams = window.location.search;
const params = new URLSearchParams(urlParams);
const returnTo = params.get("return_to");

const snakeBoard = document.querySelector(".snake-board");
const gameId = window.location.toString().split("/")[window.location.toString().split("/").length-1]
const spectateSocket = io(`/ws/spectate?game_id=${gameId}`, { forceNew: true });

spectateSocket.on("game_settings", (gameData) => {
    console.log(gameData);
    // Todo: Make box size dependent on board size(for custom games)
    // Todo: Make sure this is the first thing the client receives e.g. using a isInitialized flag
    const gameSettings = gameData["settings"]
    const rows = gameSettings["board"]["rows"];
    const cols = gameSettings["board"]["cols"];

    // Todo: Load players profiles
    board = {
        cols: cols,
        rows: rows,
        boxes: cols*rows
    };
    boardCreation();
});

spectateSocket.on("game_start", () => {
    startSnake();
});

spectateSocket.on("game_update", (data) => {
    gameUpdate(data);
});

spectateSocket.on("game_not_exist", () => {
    window.location.href = returnTo;
});

spectateSocket.on('game_over', (data) => {
    const winner = data.winner;
    // const userId = localStorage.getItem("userId")
    // const username = localStorage.getItem("username")
    gameIsOver = true;
    console.log(winner);
});
