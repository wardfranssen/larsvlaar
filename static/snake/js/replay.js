async function getGameData(gameId) {
    const response = await fetch(`/api/games/${gameId}`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    const responseJson = await handleJsonResponse(response);
    if (responseJson) {
        return responseJson.data;
    }
}

function updatePositions(playerId, position, newHead, gameData) {
    position.push(newHead);

    for (const [i, foodPos] of Object.entries(foodPositions)) {
        if (JSON.stringify(newHead) === JSON.stringify(foodPos[0])) {
            foodPositions[i].shift();

            playersScore[playerId] += gameData["settings"]["grow"];

            return position;
        }
    }

    if (gameData["settings"]["grow"] === 1 || (gameData["settings"]["grow"] > 1 && playersScore[playerId] + gameData["settings"]["spawn_len"] <= position.length - 1)) {
        position.shift();
    }

    return position;
}

function move(playerId, position, direction, gameData) {
    // Calculate the next head position
    let head = position[position.length - 1];
    let newHead;

    switch (direction) {
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

    const newPosition = updatePositions(playerId, position, newHead, gameData);

    renderSnake(playerId, newPosition, gameData["players"][playerId]["pfp_version"], gameData["players"][playerId]["skin"]);
    return newPosition;
}

function gameUpdate(gameData) {
    const players = gameData["players"];

    for (const box of boxes) {
        box.classList.remove("food");
        box.classList.remove("snake");
        box.style.backgroundImage = "";
    }

    for (const [playerId, player] of Object.entries(players)) {
        if (!player["alive"]) {
            continue;
        }

        const position = playersPosition[playerId];
        const direction = player["moves"][updateIndex];

        if (updateIndex+1 === player["moves"].length - 1) {
            player["alive"] = false;
        }

        playersPosition[playerId] = move(playerId, position, direction, gameData);
    }

    for (const [i, foodPos] of Object.entries(foodPositions)) {
        if (foodPos[0]) {
            renderFood(foodPos[0][0], foodPos[0][1], foodSkin);
        }
    }

    let aliveCount = 0;
    for (const [playerId, player] of Object.entries(players)) {
        if (player["alive"]) {
            aliveCount++;
        }
    }
    if ((aliveCount <= 1 && Object.keys(players).length > 1) || (aliveCount === 0 && Object.keys(players).length === 1)) {
        clearInterval(updateInterval);
    }

    updateIndex += 1;
}


// Todo: Add variable update interval
let board;
let foodPositions;
let updateIndex = 0;
let playersPosition = {};
let playersScore = {};
const currentUserId = localStorage.getItem("userId");
let updateInterval;
const gameId = window.location.toString().split("/")[window.location.toString().split("/").length-1]
const snakeBoard = document.querySelector(".snake-board");
let foodSkin;

getGameData(gameId).then((gameData) => {
    const gameSettings = gameData["settings"]
    const rows = gameSettings["board"]["rows"];
    const cols = gameSettings["board"]["cols"];
    const players = gameData["players"];
    foodPositions = gameData["food"];

    board = {
        cols: cols,
        rows: rows,
        boxes: cols*rows
    };

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


    for (const [playerId, player] of Object.entries(players)) {
        playersPosition[playerId] = players[playerId]["spawn_pos"];
        playersScore[playerId] = 0;
        renderSnake(playerId, playersPosition[playerId], players[playerId]["pfp_version"], players[playerId]["skin"]);
        player["alive"] = true;

        if (playerId === currentUserId) {
            foodSkin = player["food_skin"];
        }
    }

    for (const [playerId, player] of Object.entries(gameData["players"])) {
    }


    for (const [i, foodPos] of Object.entries(foodPositions)) {
        if (foodPos[0]) {
            renderFood(foodPos[0][0], foodPos[0][1], foodSkin);
        }
    }

    setTimeout(() => {
        updateInterval = setInterval(() => {
            gameUpdate(gameData);
        }, gameSettings["update_interval"]*1000)
    }, 1000)
})
