let table = {
    cols: 15,
    rows: 15
};

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
        snake.spawnX = Math.floor((table.cols / 2)) - 4;
        snake.spawnY = Math.floor((table.rows / 2));
        snake.position = [
            [snake.spawnX, snake.spawnY],
            [snake.spawnX+1, snake.spawnY],
            [snake.spawnX+2, snake.spawnY],
            [snake.spawnX+3, snake.spawnY],
            [snake.spawnX+4, snake.spawnY],
        ];
        snake.interval = document.getElementById("update-interval-input").value * 1000;
        snake.food = 0;
        snake.score = 0;
        snake.time = 0;
        snake.isAlive = true;
    },
};

const boxes = document.getElementsByClassName("box");

function renderSnake(snakePos) {
    for (const box of boxes) {
        box.classList.remove("snake");
        box.classList.remove("food");
    }

    for (let i = 0; i < snakePos.length; i++) {
        const snakePart = boxes[snakePos[i][0] + snakePos[i][1] * table.cols];

        snakePart.classList.remove("head");
        if (i === snakePos.length - 1) {
            snakePart.classList.add("head");
        }
        snakePart.classList.add("snake");
    }
}

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
        // Respawn when die
        snake.init();
        return;
    }

    // Update the snake's position
    updatePositions(newHead);
    renderSnake(snake.position);

    snake.prevDirection = snake.direction;
    snake.nextDirection = snake.direction;
}

function hitBorder(newHead) {
    return (
        newHead[0] < 0 ||
        newHead[0] >= table.cols ||
        newHead[1] < 0 ||
        newHead[1] >= table.rows
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
    if (!snake.isAlive) return;

    move();
    setTimeout(previewGameLoop, snake.interval);
}

function startPreview() {
    snake.init();
    document.addEventListener("keydown", turn, { passive: false });
    setTimeout(previewGameLoop, snake.interval);
}


function openJoinGamePopup() {
    document.getElementById("join-game-popup").classList.add("show");
}

function closeJoinGamePopup() {
    document.getElementById("join-game-popup").classList.remove("show");
}

function openCreateGamePopup() {
    document.getElementById("create-game-popup").classList.add("show");
    snake.init();
    setTimeout(startPreview, 1100);
}

function closeCreateGamePopup() {
    document.getElementById("create-game-popup").classList.remove("show");
    snake.isAlive = false;
}

function createTablePreview(rows, columns) {
    const tablePreview = document.getElementById("table-preview");
    tablePreview.innerHTML = "";

    table.rows = rows;
    table.cols = columns;
    snake.init();
    snake.isAlive = false;

    for (let i = 0; i < rows*columns; i++) {
        let divElt = document.createElement("div");
        divElt.classList.add("box");
        tablePreview.appendChild(divElt);
    }

    document.documentElement.style.setProperty("--preview-grid-rows", rows);
    document.documentElement.style.setProperty("--preview-grid-cols", columns);

    document.documentElement.style.setProperty("--preview-grid-size", `${250/Math.max(rows, columns)}px`);

    if (document.getElementById("create-game-popup").classList.contains("show")) {
        setTimeout(startPreview, 1100);
    }
}

function updateTablePreview(event) {
    const rowsInput = document.getElementById("rows-input");
    const columnsInput = document.getElementById("columns-input");

    if (isNaN(rowsInput.value)) {
        let newValue = rowsInput.value.replace(event.data, "");
        rowsInput.value = newValue;
        newValue = columnsInput.value.replace(event.data, "");
        columnsInput.value = newValue;
    } else {
        let rows = rowsInput.value;
        let columns = columnsInput.value;

        if (rows > 100) {
            rows = 100;
            rowsInput.value = rows;
        } else if (rows < 10) {
            rows = 10;
            rowsInput.value = rows;
        }
        if (columns > 100) {
            columns = 100;
            columnsInput.value = columns;
        } else if (columns < 10) {
            columns = 10;
            columnsInput.value = columns;
        }

        createTablePreview(rows, columns);
    }
}


async function createCustomGame(joinToken) {
    const rows = document.getElementById("rows-input").value;
    const columns = document.getElementById("columns-input").value;
    // const isPublic = document.getElementById("public-toggle").value;
    // const updateInterval = document.getElementById("update-interval-input").value;

    const response = await fetch("/create_custom_game", {
        method: "POST",
        body: JSON.stringify({"join_token": joinToken, "rows": rows, "columns": columns}),
        headers: {
            "Content-Type": "application/json"
        }
    });

    if (response.status === 429) {
        createGeneralPopup("Wow, niet zo snel", "error");
        document.querySelector("#reset-password-form button i").style.display = "none";
        document.querySelector("#verify-form button i").style.display = "none";
        return;
    }

    const responseJson = await response.json();

    if (response.ok) {
        if (responseJson.redirect) {
            window.location.href = responseJson.redirect;
        }
    }else {
        if (responseJson.error === true) {
            if (responseJson.type === "general") {
                createGeneralPopup(responseJson.message, responseJson.category);
                return;
            }

            const error = document.getElementById(`${responseJson.type}-error`);
            error.classList.add("show");
            error.innerHTML = `<span>${responseJson.message}</span>`;

            document.getElementById(`${responseJson.type}-input`).focus();
        }
    }
}


const randomImgs = [
    "lars_met_hond.png",
    "lars_magister.jpg",
    "boze_lars.jpg",
    "lars.jpg",
    "lars_badminton.jpg",
    "lars_is_dik.png"
];

document.querySelector(".game-modes img").src = `/img/${randomImgs[Math.floor(Math.random()*randomImgs.length)]}`;

createTablePreview(15, 15);


document.getElementById("join-game-form").addEventListener("submit", async function(event) {
    event.preventDefault();
    clearCatErrors();

    const gameId = document.getElementById("join-game-id-input").value;

    if (gameId.length > 0) {
        document.querySelector("#join-game-form button i").style.display = "";
        await joinMatch(gameId, null);
        document.querySelector("#join-game-form button i").style.display = "none";
    }
});

document.getElementById("create-game-form").addEventListener("submit", async function(event) {
    event.preventDefault();
    clearCatErrors();

    const joinToken = document.getElementById("game-id-input").value;

    if (joinToken.length > 0) {
        document.querySelector("#create-game-form button i").style.display = "";
        await createCustomGame(joinToken);
        document.querySelector("#create-game-form button i").style.display = "none";
    }
});

document.getElementById("rows-input").addEventListener("focusout", function() {
    const rowsInput = document.getElementById("rows-input");
    const columnsInput = document.getElementById("columns-input");

    let rows = rowsInput.value;
    let columns = columnsInput.value;

    if (isNaN(rows)) {
        rows = 15
        rowsInput.value = rows;

        createTablePreview(rows, columns);
    } else {
        if (rows > 100) {
            rows = 100;
            rowsInput.value = rows;
        } else if (rows < 10) {
            rows = 10;
            rowsInput.value = rows;
        }

        createTablePreview(rows, columns);
    }
});

document.getElementById("columns-input").addEventListener("focusout", function() {
    const rowsInput = document.getElementById("rows-input");
    const columnsInput = document.getElementById("columns-input");

    let rows = rowsInput.value;
    let columns = columnsInput.value;

    if (isNaN(columns)) {
        columns = 15
        columnsInput.value = columns;

        createTablePreview(rows, columns);
    } else {
        if (columns > 100) {
            columns = 100;
            columnsInput.value = columns;
        } else if (columns < 10) {
            columns = 10;
            columnsInput.value = columns;
        }

        createTablePreview(rows, columns);
    }
});

document.getElementById("update-interval-input").addEventListener("input", function() {
    snake.interval = document.getElementById("update-interval-input").value * 1000
});
