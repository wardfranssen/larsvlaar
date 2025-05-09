async function getUsers(query, limit, friendship_status=false) {
    const response = await fetch(`/api/users?query=${query.trim()}&limit=${limit}&friendship_status=${friendship_status}`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    const responseJson = await handleJsonResponse(response);
    if (responseJson) {
        return responseJson["users"];
    }
}



function checkFlashMessages(messages) {
    if (messages.length > 0) {
        for (const [category, message] of messages) {
            createGeneralPopup(message, category);
        }
    }
}

function createGeneralPopup(message, category, stack = true) {
    const errorContainer = document.querySelector("#general-popups");
    let errors = errorContainer.getElementsByClassName(category);

    if (!stack) {
        for (const error of errors) {
            if (error.textContent === message) {
                error.remove()
            }
        }
    }

    if (errors.length > 4) {
        errors[0].remove();
    }

    const span = document.createElement("span");
    span.classList.add(category, "popup-message");
    span.textContent = message;

    errorContainer.appendChild(span);

    setTimeout(() => {
        span.remove();
    }, 5000);
}


function isStrongPassword(password) {
    const requirements = document.querySelectorAll("#password-requirements span");
    let isStrong = true;

    for (requirement of requirements) {
        requirement.className = "";
    }

    if (password.length < 8) {
        requirements[0].classList.add("not-fulfilled");
        isStrong = false;
    }

    if (!/[A-Z]/.test(password)) {
        requirements[1].classList.add("not-fulfilled");
        isStrong = false;
    }

    if (!/[a-z]/.test(password)) {
        requirements[2].classList.add("not-fulfilled");
        isStrong = false;
    }

    if (!/\d/.test(password)) {
        requirements[3].classList.add("not-fulfilled");
        isStrong = false;
    }

    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
        requirements[4].classList.add("not-fulfilled");
        isStrong = false;
    }

    return isStrong;
}

function isValidEmail(email) {
    return email.match(
        /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/
    );
}

function clearCatErrors() {
    document.querySelectorAll(".cat-error.show").forEach((error) => error.classList.remove("show"));
}

async function clearGames() {
    const response = await fetch("/clear_games", {
        method: "POST"
    });

    const responseJson = await handleJsonResponse(response);
    console.log(responseJson.message);
}

async function handleJsonResponse(response, {
    onRedirect = null
} = {}) {
    if (await response.status === 429) {
        createGeneralPopup("Wow, niet zo snel", "error");
        return;
    }

    const responseJson = await response.json();

    if (response.ok) {
        if (responseJson.message && responseJson.type === "general") {
            createGeneralPopup(responseJson.message, responseJson.category);
        }

        if (responseJson.reload) {
            window.location.reload();
        }
        if (responseJson.redirect) {
            if (onRedirect) {
                await onRedirect(responseJson);
            }
            window.location.href = responseJson.redirect;
            return;
        }
        return responseJson;
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

function updateCountdown() {
    countdownCount -= 1;
    countdownDiv.querySelector("span").innerText = countdownCount;
}

function toggleDropdown(event) {
    event.stopPropagation();
    const dropdown = document.querySelector("#profile-dropdown.dropdown-content");
    dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
}

async function logout() {
    fetch("/api/auth/logout", {
        method: "POST"
    }).then((response) => {
        handleJsonResponse(response, {
            onRedirect: (json) => {
                localStorage.clear();
            }
        });
    })
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

function renderFood(x, y) {
    // Check if (x, y) is within bounds
    if (x < 0 || x >= board.cols || y < 0 || y >= board.rows) {
        console.error(`Invalid food position: (${x}, ${y})`);
        return; // Skip rendering if out of bounds
    }

    const index = x + y * board.cols;
    boxes[index].classList.add("food");
}

function renderSnake(playerId, snakePos, pfpVersion) {
    for (let i = 0; i < snakePos.length; i++) {
        const snakePart = boxes[snakePos[i][0] + snakePos[i][1] * board.cols];

        snakePart.style.backgroundImage = "";
        snakePart.classList.remove("head");
        if (i === snakePos.length - 1) {
            snakePart.style.backgroundImage = `url("/api/users/${playerId}/pfp?v=${pfpVersion}")`;
        }
        snakePart.classList.add("snake");
    }
}

async function createSinglePlayerGame() {
    const response = await fetch(`/api/single_player/create`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    await handleJsonResponse(response);
}


document.addEventListener('click', function (event) {
    const profile = document.querySelector('.profile-card');
    const dropdown = document.getElementById("profile-dropdown");

    if (dropdown && !profile.contains(event.target)) {
        dropdown.style.display = 'none';
    }
});


