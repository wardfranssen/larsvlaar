document.addEventListener("DOMContentLoaded", function () {
    let snakeTable = document.querySelector(".snake-table");
    let boxes;
    let modul = document.querySelector(".popup-background");
    let start = document.querySelector(".popup");
    let scoreElt;
    let foodPos;

    let table = {
        rowsCols: 15,
        boxes: 15 * 15,
    };

    let snake = {
        direction: "right",
        score: 0,
        init: function () {
            snake.direction = "right";
            snake.spawnY = Math.floor(Math.random() * table.rowsCols);
            snake.position = [
                [3, snake.spawnY],
                [4, snake.spawnY],
                [5, snake.spawnY],
                [6, snake.spawnY],
                [7, snake.spawnY],
            ];
            snake.score = 0;
            snake.prevPositions = [];
            snakeTable.innerHTML = "";
            tableCreation();
        },
    };

    function tableCreation() {
        if (snakeTable.innerHTML === "") {
            for (let i = 0; i < table.boxes; i++) {
                let divElt = document.createElement("div");
                divElt.classList.add("box");
                snakeTable.appendChild(divElt);
            }
            let statusElt = document.createElement("div");
            statusElt.classList.add("status");
            snakeTable.appendChild(statusElt);
            scoreElt = document.createElement("span");
            scoreElt.classList.add("score");
            scoreElt.innerHTML = snake.score + " puntjes";
            statusElt.appendChild(scoreElt);
        }
        boxes = document.getElementsByClassName("box");
    }

    function startSnake() {
        modul.classList.add("hidden");

        socket = io("/one_vs_one", {
            query: {
                game_id: gameId
            }
        });

        sendSnakeDir("right");

        socket.on('snakes_pos', (data) => {
            // Clear all boxes
            // for (const snake_ of snake.prevPositions) {
            //     for (const position of snake_) {
            //         const snakePart = boxes[position[0] + position[1] * table.rowsCols];
            //         snakePart.classList.remove("snake");
            //     }
            // }
            for (const box of boxes) {
                box.classList.remove("snake");
            }
            
            for (const snake of data) {
                renderSnake(snake);
            }
            snake.prevPositions = data;
        });

        socket.on('game_not_exist', () => {
            console.log("Game does not exist");
            stopp();
        });
        
        socket.on('food_pos', (data) => {
            console.log(data);
            for (const box of boxes) {
                box.classList.remove("food");
            }
            spawnFood(data[0], data[1]);
        });

        socket.on('game_over', (data) => {
            console.log(data.winner);
            console.log("Game has ended");
            stopp();
        });
    }

    function stopp() {
        if (!snake.isAlive) return;
        
        socket.disconnect();

        start.querySelector("span").innerHTML = snake.score + " Puntjes! Druk op enter om opnieuw te beginnen";

        modul.querySelector(".quote").innerHTML = "";
        typingIndex = 0;
        typeEffect(`<br>"${motivationalQuotes[Math.floor(Math.random()*motivationalQuotes.length)]}"`);
        
        modul.classList.remove("hidden");
    }

    async function sendSnakeDir(direction) {
        socket.emit('snake_dir', {"snake_dir": direction, "time": Date.now()/1000});
    }

    function spawnFood(x, y) {
        boxes[x + y * table.rowsCols].classList.add("food");
        foodPos = [x, y];
    }

    function renderSnake(snakePos) {
        for (let i = 0; i < snakePos.length; i++) {
            const snakePart = boxes[snakePos[i][0] + snakePos[i][1] * table.rowsCols];

            snakePart.classList.remove("head");
            if (i === snakePos.length - 1) {
                snakePart.classList.add("head");
            }
            snakePart.classList.add("snake");
        }
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
            case 13: // Enter key
                if (!snake.isAlive) {
                    snake.init();
                    startSnake();
                }
                return;
            default:
                return;
        }
        e.preventDefault(); // Stop scrolling issues

        sendSnakeDir(direction);
    }

    start.addEventListener("click", function () {
        snake.init();
        startSnake();
    });

    snake.init();
    document.addEventListener("keydown", turn, { passive: false });

    function typeEffect(text) {
        if (typingIndex < text.length && !snake.isAlive) {
            // Append the current character or HTML element
            if (text.charAt(typingIndex) === '<' && text.slice(typingIndex, typingIndex + 4) === '<br>') {
                document.getElementById("typing").innerHTML += "<br>";
                typingIndex += 4; // Skip past the '<br>' tag
            } else {
                document.getElementById("typing").innerHTML += text.charAt(typingIndex);
                typingIndex++;
            }
            
            setTimeout(function() {
                typeEffect(text);
            }, Math.random() * 30 + typingSpeed);
        } else {
            document.getElementById("typing").style.borderRight = "none";
        }
    }
});


async function fetchMotivationalQuotes() {
    const response = await fetch("/motivational_quotes");

    if (response.ok) {
        return await response.json();
    }
}

const typingSpeed = 15;
let typingIndex = 0;
let motivationalQuotes;

let socket;
const urlParams = window.location.search;
const params = new URLSearchParams(urlParams);
const gameId = params.get("game_id");

fetchMotivationalQuotes().then((quotes) => {
    motivationalQuotes = quotes
});

async function clearMoves() {
    await fetch("/clear_moves", {method: "POST"})
}

async function joinMatch() {
    const gameId = document.getElementById("game-id").value;

    const response = await fetch("/matchmaking", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({"game_id": gameId, "game_mode": "one_vs_one"})
    });

    const responseJson = await response.json();

    if (response.ok) {
        console.log("Successfully joined a match");
    } else {
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
