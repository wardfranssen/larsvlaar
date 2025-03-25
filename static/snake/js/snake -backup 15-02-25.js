document.addEventListener("DOMContentLoaded", function () {
    let snakeTable = document.querySelector(".snakeTable");
    let boxes;
    let modul = document.querySelector(".popup-background");
    let start = document.querySelector(".popup");
    let scoreElt;
    let setInt;
    let foodPos;

    let table = {
        rowsCols: 15,
        boxes: 15 * 15,
    };

    let snake = {
        score: 0,
        init: function () {
            snake.score = 0;
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

        socket = io();

        socket.on('game_not_exist', () => {
            console.log("Game does not exist");
            stopp();
        });

        socket.on('game_over', (data) => {
            console.log(data.winner);
            stopp();
        });

        socket.on('game_state', (state) => {
            gameState = state

            // Clear all boxes
            for (const box of boxes) {
                box.classList.remove("snake");
                box.classList.remove("food");
            }
            
            // Render Players
            for (const playerId in state.players) {            
                renderSnake(state.players[playerId].snake_pos);
                renderSnake(state.players[playerId].snake_pos);
            }

            // Render Food
            const foodPos = state.food_pos;
            spawnFood(foodPos[0], foodPos[1]);
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

        // Send current time(time of input)
        const inputTime = Date.now()
        const stateUpdateCount = gameState.update_count;

        socket.emit('game_input', {
            direction,
            "input_time": inputTime,
            "update_count": stateUpdateCount
        });
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
let gameState;

fetchMotivationalQuotes().then((quotes) => {
    motivationalQuotes = quotes
});


async function joinMatch(gameId) {
    const response = await fetch("/matchmaking", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({"game_id": gameId})
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