document.addEventListener("DOMContentLoaded", function () {
    var snakeTable = document.querySelector(".snakeTable");
    var boxes;
    var modul = document.querySelector(".popup-background");
    var start = document.querySelector(".popup");
    var scoreElt;
    var setInt;
    var foodPos;

    var table = {
        rowsCols: 15,
        boxes: 15 * 15,
    };

    var snake = {
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
        interval: 175,
        food: 0,
        score: 0,
        final: 0,
        time: 0,
        isAlive: true, 
        init: function () {
            snake.direction = "right";
            snake.prevDirection = "right";
            snake.nextDirection = "right";
            snake.position = [
                [3, 7],
                [4, 7],
                [5, 7],
                [6, 7],
                [7, 7],
            ];
            snake.interval = 200; 
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
            for (var i = 0; i < table.boxes; i++) {
                var divElt = document.createElement("div");
                divElt.classList.add("gridBox");
                snakeTable.appendChild(divElt);
            }
            var statusElt = document.createElement("div");
            statusElt.classList.add("status");
            snakeTable.appendChild(statusElt);
            scoreElt = document.createElement("span");
            scoreElt.classList.add("snakeScore");
            scoreElt.innerHTML = snake.score + " puntjes";
            statusElt.appendChild(scoreElt);
        }
        boxes = document.getElementsByClassName("gridBox");
    }

    function startSnake() {
        modul.classList.add("hidden");
        snake.time = 1;
        
        setInt = setInterval(move, snake.interval);

        socket = io();

        // Handle game updates from the server
        socket.on('spawn_food', (data) => {
            spawnFood(data[0], data[1]);
        });
    }

    function stopp() {
        if (!snake.isAlive) return; // Prevent multiple calls
        snake.isAlive = false;

        clearInterval(setInt);
        snake.final = snake.score;
        start.querySelector("span").innerHTML = snake.final + " Puntjes! Druk op enter om opnieuw te beginnen";

        modul.querySelector(".quote").innerHTML = "";
        typingIndex = 0;
        typeEffect(`<br>"${motivationalQuotes[Math.floor(Math.random()*motivationalQuotes.length)]}"`);
        
        modul.classList.remove("hidden");
    }

    async function sendDirection(direction) {
        socket.emit('game_input', {direction});

        snake.last5Moves = [];

        // const response = await fetch("/move", {
        //     method: "POST",
        //     headers: {
        //         "content-type": "application/json"
        //     },
        //     body: JSON.stringify({direction}),
        //     credentials: "include"
        // });

        // if (response.ok) {
        //     return true;
        // } 
        // return false;
    }

    function move() {
        if (!snake.isAlive) return; // Stop moving if snake is dead

        snake.direction = snake.nextDirection;

        // Calculate the next head position
        var head = snake.position[snake.position.length - 1];
        var newHead;

        // Prevent opposite direction changes
        if (
            (snake.prevDirection === "left" && snake.direction === "right") ||
            (snake.prevDirection === "right" && snake.direction === "left") ||
            (snake.prevDirection === "up" && snake.direction === "down") ||
            (snake.prevDirection === "down" && snake.direction === "up")
        ) {
            snake.direction = snake.prevDirection;
        }

        // snake.last5Moves.unshift(snake.direction);
        snake.last5Moves.push(snake.direction);

        sendDirection(snake.direction)

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
        hitFood();
        renderSnake();
        
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
        for (var i = 0; i < snake.position.length; i++) {
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
        var head = snake.position[snake.position.length - 1];
        if (head.toString() === foodPos.toString()) {
            boxes[foodPos[0] + foodPos[1] * table.rowsCols].classList.remove("food");
            snake.position.unshift([...snake.position[0]]);
            // randomFood();
            snake.food++;
            snake.score += 1;
            scoreElt.innerHTML = snake.score + " puntjes";
            clearInterval(setInt);
            snake.interval *= 0.999;
            setInt = setInterval(move, snake.interval);
        }
    }

    async function sendFoodPos(foodPos) {
        const response = await fetch("/food_pos", {
            method: "POST",
            headers: {
                "content-type": "application/json"
            },
            body: JSON.stringify({foodPos}),
            credentials: "include"
        });

        if (response.ok) {
            return true;
        } 
        return false;
    }

    function spawnFood(x, y) {
        // var randomX, randomY, random;
        // var isOccupied;

        // do {
        //     isOccupied = false;
        //     randomX = Math.floor(Math.random() * table.rowsCols);
        //     randomY = Math.floor(Math.random() * table.rowsCols);
        //     random = randomX + randomY * table.rowsCols;

        //     // Check if the random position is occupied by the snake's body
        //     for (var i = 0; i < snake.position.length; i++) {
        //         if (snake.position[i][0] === randomX && snake.position[i][1] === randomY) {
        //             isOccupied = true;
        //             break;
        //         }
        //     }
        // } while (isOccupied);

        boxes[x + y * table.rowsCols].classList.add("food");
        foodPos = [x, y];
        // socket.emit('food_pos', {foodPos});
    }

    function renderSnake() {
        for (var i = 0; i < snake.position.length; i++) {
            const snakePart = boxes[snake.position[i][0] + snake.position[i][1] * table.rowsCols];

            snakePart.classList.remove("head");
            if (i == snake.position.length - 1) {
                snakePart.classList.add("head");
            }
            snakePart.classList.add("snake");
        }
    }

    function turn(e) {
        var direction;
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