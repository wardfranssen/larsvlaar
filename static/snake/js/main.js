function checkFlashMessages(messages) {
    // Display flash message if present
    
    if (messages.length > 0) {
        for (const [category, message] of messages) {
            createGeneralPopup(message, category);
        }
    }
}


function createGeneralPopup(message, category) {
    const errorContainer = document.getElementById("popup-messages");
    const errors = errorContainer.getElementsByClassName(category);

    for (const error of errors) {
        if (error.textContent == message) {
            error.remove()
        }
    }

    const span = document.createElement("span");
    span.classList.add(category, "popup-message");
    span.textContent = message;

    errorContainer.appendChild(span);

    setTimeout(() => {
        span.remove();
    }, 7000);
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
};

function clearCatErrors() {
    document.querySelectorAll(".cat-error.show").forEach((error) => error.classList.remove("show"));
}

function snakeCaseToTitleCase(text) {
    let result = "";
    let nextCap = false;
    
    for (let i = 0; i < text.length; i++) {
        const letter = text[i];

        if (i == 0) {
            result += letter.toUpperCase();
            continue;
        }

        if (nextCap) {
            result += letter.toUpperCase();
            nextCap = false;
            continue;
        }
        if (letter == "_") {
            result += " ";
            nextCap = true;   
        } else {
            result += letter;
        }
    }

    return result;
}

async function joinMatch(gameId, gameMode) {
    const response = await fetch("/matchmaking", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({"game_id": gameId, "game_mode": gameMode})
    });    

    if (await response.status == 429) {
        createGeneralPopup("Wow, niet zo snel", "error");
        return;
    }

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


async function clearGames() {
    const response = await fetch("/clear_games", {
        method: "POST"
    });

    const responseJson = await response.json();

    if (response.ok) {
        console.log("Sucessfully cleared all games");
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