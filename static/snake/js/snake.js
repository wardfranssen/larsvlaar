document.addEventListener("DOMContentLoaded", function () {
    let snakeTable = document.querySelector(".snakeTable");
    let boxes;
    let modul = document.querySelector(".popup-background");
    let start = document.querySelector(".popup");
    let scoreElt;
    let setInt;
    let sendInt;
    let foodPos;

    let table = {
        rowsCols: 15,
        boxes: 15 * 15,
    };

    let snake = {
        direction: "right",
        prevDirection: "right",
        nextDirection: "right",
        last5Moves: [],
        position: [
            [3, 7],
            [4, 7],
            [5, 7],
            [6, 7],
            [7, 7],
        ],
        interval: 200,
        food: 0,
        score: 0,
        final: 0,
        time: 0,
        isAlive: true, 
        init: function () {
            snake.direction = "right";
            snake.prevDirection = "right";
            snake.nextDirection = "right";
            snake.spawnY = Math.floor(Math.random() * table.rowsCols);
            snake.position = [
                [3, snake.spawnY],
                [4, snake.spawnY],
                [5, snake.spawnY],
                [6, snake.spawnY],
                [7, snake.spawnY],
            ];
            snake.interval = 1200; 
            snake.food = 0;
            snake.score = 0;
            snake.time = 0;
            snake.isAlive = true; 
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
        snake.time = 1;
        
        // setInt = setInterval(move, snake.interval);
        sendInt = setInterval(sendSnakePos, 1000);

        socket = io("/one_vs_one");

        // Handle game updates from the server
        socket.on('opponent_pos', (data) => {
            // Clear all boxes
            for (const box of boxes) {
                box.classList.remove("snake");
            }

            renderSnake(data);
            renderSnake(snake.position);
            // move();
            clearInterval(setInt);
            setInt = setInterval(move, snake.interval-155);
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
        if (!snake.isAlive) return; // Prevent multiple calls
        
        
        socket.disconnect();


        snake.isAlive = false;

        clearInterval(setInt);
        clearInterval(sendInt);
        snake.final = snake.score;
        start.querySelector("span").innerHTML = snake.final + " Puntjes! Druk op enter om opnieuw te beginnen";

        modul.querySelector(".quote").innerHTML = "";
        typingIndex = 0;
        typeEffect(`<br>"${motivationalQuotes[Math.floor(Math.random()*motivationalQuotes.length)]}"`);
        
        modul.classList.remove("hidden");
    }

    async function sendSnakePos() {
        socket.emit('snake_pos', {"snake_pos": snake.position});
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
            stopp();
            return; 
        }

        // Update the snake's position
        updatePositions(newHead);
        
        sendSnakePos();

        hitFood();

        renderSnake(snake.position);
        
        snake.prevDirection = snake.direction;
        snake.nextDirection = snake.direction;
    }

    function updatePositions(newHead) {
        // Remove the tail
        boxes[snake.position[0][0] + snake.position[0][1] * table.rowsCols].classList.remove("snake");
        snake.position.shift();

        // Add the new head
        snake.position.push(newHead);
    }

    function hitBorder(newHead) {
        return (
            newHead[0] < 0 ||
            newHead[0] >= table.rowsCols ||
            newHead[1] < 0 ||
            newHead[1] >= table.rowsCols
        );
    }

    function hitSnake(newHead) {
        for (let i = 0; i < snake.position.length; i++) {
            // LAST PART OF SNAKE SHOULD BE IGNORED
            if (i == 0) {
                continue;
            }
            if (snake.position[i][0] === newHead[0] && snake.position[i][1] === newHead[1]) {
                return true;
            }
        }
        return false;
    }

    function hitFood() {
        if (!foodPos) return;
        let head = snake.position[snake.position.length - 1];
        if (head.toString() === foodPos.toString()) {
            boxes[foodPos[0] + foodPos[1] * table.rowsCols].classList.remove("food");
            snake.position.unshift([...snake.position[0]]);
            snake.food++;
            snake.score += 1;
            scoreElt.innerHTML = snake.score + " puntjes";
            // clearInterval(setInt);
            // clearInterval(sendInt);
            // snake.interval *= 0.999;
            // setInt = setInterval(move, snake.interval);
            // sendInt = setInterval(sendSnakePos, 50);
        }
    }

    function spawnFood(x, y) {
        boxes[x + y * table.rowsCols].classList.add("food");
        foodPos = [x, y];
    }

    function renderSnake(snakePos) {
        for (let i = 0; i < snakePos.length; i++) {
            const snakePart = boxes[snakePos[i][0] + snakePos[i][1] * table.rowsCols];

            snakePart.classList.remove("head");
            if (i == snakePos.length - 1) {
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
        const quotes = await response.json();
        return quotes;
    }
}

const typingSpeed = 15;
let typingIndex = 0;
let motivationalQuotes;

let socket;

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
        return;
    } else {
        if (responseJson.error == true) {
            if (responseJson.type == "general") {
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
