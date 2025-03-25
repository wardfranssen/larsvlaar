(() => {
    let score = 0;
    // Background scrolling speed
    moveSpeed = 8;

    // Gravity constant value
    let gravity = 0.4;

    let pipeDistance = 80;

    let bird = document.querySelector('.bird');
    bird.style.height = '11%';
    let jumps = 0;

    let birdProps = bird.getBoundingClientRect();
    let background = document.querySelector('#background') .getBoundingClientRect();

    // Getting reference to the score element
    let scoreVal = document.querySelector('.scoreVal');
    let highscoreVal = document.querySelector('.highscoreVal');
    let message = document.querySelector('.message');

    let lastFrameTimeMs = 0;
    let maxFPS = 80;

    // Setting initial game state to start
    window.gameState = 'Start';

    // Add an eventlistener for key presses
    document.addEventListener('keydown', start);
    document.getElementById('background').addEventListener('click', start);

    // If the player has not selected an item, set it to the default item
    if (!localStorage.getItem('background')) {
        localStorage.setItem('background', 'geertMetZonnebril');
    }
    if (!localStorage.getItem('skin')) {
        localStorage.setItem('skin', 'drake');
    }
    if (!localStorage.getItem('pipeskin')) {
        localStorage.setItem('pipeskin', 'greenPipe');
    }
    document.getElementById('background').style.backgroundImage = `url(/img/unlocked/${localStorage.getItem('background')}.jpg)`;

    document.querySelector('.bird').src = `/img/unlocked/${localStorage.getItem('skin')}.jpg`;
    document.querySelector('.bird').style.aspectRatio = '1/1';


    getToken().then((data) => {
        window.token = JSON.parse(data).token;
    });


    getUnlocked();

    async function getUnlocked() {
        // Get the items that the player has unlocked from the server
        let response = await fetch ("/unlocked", {
            method: "GET"
        });

        let unlockedItems = await response.text();
        if (unlockedItems.includes('Error: ')) {return;}

        skins = JSON.parse(unlockedItems).skins;
        backgrounds = JSON.parse(unlockedItems).backgrounds;
        pipeskins = JSON.parse(unlockedItems).pipeskins;

        // If the player has selected an item that they have not unlocked, change it to the default item
        if (!localStorage.getItem('background') || !backgrounds.includes(localStorage.getItem('background'))) {
            localStorage.setItem('background', 'geertMetZonnebril');
        }
        if (!localStorage.getItem('skin') || !skins.includes(localStorage.getItem('skin'))) {
            localStorage.setItem('skin', 'drake');
        }
        if (!localStorage.getItem('pipeskin') || !pipeskins.includes(localStorage.getItem('pipeskin'))) {
            localStorage.setItem('pipeskin', 'greenPipe');
        }
    }


    async function getToken() {
        let headers = new Headers();
        headers.append('authorization', 'lol');

        const response = await fetch('/get_token', {
            method: 'GET',
            headers: headers
        });
        const data = await response.text();
        return data;
    }


    async function updateScore(token, gap, speed, distance) {
        // Update the score on the server
        score++;
        let headers = new Headers();
        headers.append('authorization', `t${token}`);
        headers.append('Content-Type', 'application/json');
        headers.append('Accept', 'application/json');

        // Catch cheaters who try to change the window size
        if (screen.width-200 > window.innerWidth || screen.width < window.innerWidth) {
            bird.style.height = '10.99%';
        }

        // If the player is using a background that they have not unlocked, change it to the default background
        if (!localStorage.getItem('background')) {
            localStorage.setItem('background', 'geertMetZonnebril');
        }
        document.getElementById('background').style.backgroundImage = `url(/img/unlocked/${localStorage.getItem('background')}.jpg)`;

        // If the player is using a skin that they have not unlocked, change it to the default skin
        if (!localStorage.getItem('skin')) {
            localStorage.setItem('skin', 'drake');
        }
        bird.src = `/img/unlocked/${localStorage.getItem('skin')}.jpg`;
        bird.style.aspectRatio = '1/1';

        // If the player is using a pipeskin that they have not unlocked, change it to the default pipeskin
        // Don't have to set the actual pipeskin, because the pipeskin is set on creation of the pipe
        if (!localStorage.getItem('pipeskin')) {
            localStorage.setItem('pipeskin', 'greenPipe');
        }

        // Tell the server that the player has increased their score
        const size = bird.style.height;
        const response = await fetch('/update_score', {
            method: 'POST',
            credentials: 'include',
            headers: headers,
            body: JSON.stringify({score, size, gap, speed, distance})
        });

        const data = await response.text();

        return JSON.parse(data).score;
    }


    async function died(token) {
        // Tell the server that the player has died
        let headers = new Headers();
        headers.append('authorization', token);
        headers.append('Content-Type', 'application/json');
        headers.append('Accept', 'application/json');

        const response = await fetch('/died', {
            method: 'POST',
            credentials: 'include',
            headers: headers
        });
        const data = await response.text();
        return JSON.parse(data).score;
    }


    function start(e, type='keydown') {
        if (window.gameState == 'Play' || document.activeElement.id == "message") { return; }
        if (type == 'click' || e.type == 'click' || e.key == ' ') {
            // Return if there is a popup open like shop or login
            if (document.getElementById('login').innerHTML != '' || document.getElementById('register').innerHTML != '' || document.getElementById('shop').innerHTML != '' || document.querySelector('#inventory').style.display == 'block' || document.querySelector('#suggestions').style.display == 'block') { return; }
            if (window.gameState == 'Freeze') {
                window.justFroze = true;
                window.gameState = 'Play';

                message.innerHTML = '';
                scoreVal.innerHTML = score;
                play();
            }
            if (window.gameState != 'Play') {
                document.querySelectorAll('.pipeSprite') .forEach((e) => {
                    e.remove();
                });
                window.justFrozen = false;
                moveSpeed = 8;
                pipeDistance = 100;

                bird.style.top = '40vh';
                window.gameState = 'Play';
                message.innerHTML = '';
                score = 0;
                scoreVal.innerHTML = score;
                play();
            }
        }
    }

    function play() {
        function move(timestamp) {
            // Throttle the frame rate.
            if (timestamp < lastFrameTimeMs + (1000 / maxFPS)) {
                console.log('throttling');
                requestAnimationFrame(move);
                return;
            }
            lastFrameTimeMs = timestamp;

            // Detect if game has ended
            if (window.gameState != 'Play') return;

            // Getting reference to all the pipe elements
            let pipeSprite = document.querySelectorAll('.pipeSprite');
            pipeSprite.forEach((element) => {

            let pipeSpriteProps = element.getBoundingClientRect();
            birdProps = bird.getBoundingClientRect();

            // Delete the pipes if they have moved out
            // of the screen hence saving memory
            if (pipeSpriteProps.right <= 0) {
                element.remove();
            } else {
                // Collision detection with bird and pipes
                if (
                birdProps.left < pipeSpriteProps.left +
                pipeSpriteProps.width &&
                birdProps.left +
                birdProps.width > pipeSpriteProps.left &&
                birdProps.top < pipeSpriteProps.top +
                pipeSpriteProps.height &&
                birdProps.top +
                birdProps.height > pipeSpriteProps.top
                ) {
                    // Change game state and end the game
                    // if collision occurs

                    if (score > highscoreVal.innerHTML) {
                        highscoreVal.innerHTML = score;
                        localStorage.setItem('highscore', score);
                    }
                    died(window.token).then((data) => {
                        highscoreVal.innerHTML = data;
                        window.location.reload();
                    });
                    window.gameState = 'End';
                    return;
                } else {
                    // Increase the score if player
                    // has the successfully dodged the
                    if (
                        pipeSpriteProps.right < birdProps.left &&
                        pipeSpriteProps.right +
                        moveSpeed >= birdProps.left &&
                        element.increaseScore == '1'
                    ) {
                        if (score == 10) {
                            moveSpeed = 10;
                        } else if (score == 20) {
                            pipeDistance = 70;
                        } else if (score == 30) {
                            pipeGap = 35;
                        } else if (score == 40) {
                            moveSpeed = 11;
                        } else if (score == 50) {
                            pipeDistance = 60;
                        }
                        updateScore(window.token, pipeGap, moveSpeed, pipeDistance).then((data) => {
                            scoreVal.innerHTML = data;
                        });
                    }
                    element.style.left = pipeSpriteProps.left - moveSpeed + 'px';
                }
            }
            });
            requestAnimationFrame(move);
        }
        requestAnimationFrame(move);


        function moveBird(e) {
            if (e.key == 'ArrowUp' || e.key == ' ' || e.type == 'mousedown' || e.type == 'touchstart') {
                jumps++;
                if (jumps == 25) {
                    fetch('/jump', {method: 'POST'});
                    jumps = 0;
                }
                birdDy = -10;
            }
        }


        let birdDy = 0;
        function applyGravity() {
            if (window.gameState != 'Play') return;

            birdDy = birdDy + gravity;

            document.addEventListener('keydown', moveBird);
            document.addEventListener('mousedown', moveBird);

            // Collision detection with bird and
            // window top and bottom
            if (birdProps.top <= 0 || birdProps.bottom >= background.bottom) {
                if (score > highscoreVal.innerHTML) {
                    localStorage.setItem('highscore', score);
                }
                died(window.token).then((data) => {
                    highscoreVal.innerHTML = data;
                    window.location.reload();
                });

                return;
            }
            birdProps = bird.getBoundingClientRect();
            bird.style.top = birdProps.top + birdDy + 'px';
            requestAnimationFrame(applyGravity);
        }
        requestAnimationFrame(applyGravity);

        if (!window.justFroze) {
            window.pipeSeperation = 0;
        }

        // Constant value for the gap between two pipes
        let pipeGap = 42;
        function createPipe() {
            if (window.gameState != 'Play') return;


            if (window.pipeSeperation > pipeDistance) {
                window.pipeSeperation = 0

                let pipePosi = Math.floor(Math.random() * 43) + 8;
                let pipeSpriteInv = document.createElement('div');
                pipeSpriteInv.className = 'pipeSprite upperPipe';
                pipeSpriteInv.style.top = pipePosi - 70 + 'vh';
                pipeSpriteInv.style.left = '100%';

                pipeSpriteInv.style.width = '10%';
                pipeSpriteInv.style.height = '70vh';

                // Have to do this cause the pipe is a png
                if (localStorage.getItem('pipeskin') == 'greenPipe') {
                    pipeSpriteInv.style.backgroundImage = `url(/img/unlocked/${localStorage.getItem('pipeskin')}.png)`;
                } else {
                    pipeSpriteInv.style.backgroundImage = `url(/img/unlocked/${localStorage.getItem('pipeskin')}.jpg)`;
                }

                pipeSpriteInv.style.backgroundSize = "contain";

                // if (localStorage.getItem('pipeskinMode') == '100%') {
                //     pipeSpriteInv.style.backgroundSize = "100% 100%";
                // } else {
                //     pipeSpriteInv.style.backgroundSize = localStorage.getItem('pipeskinMode');
                // }

                document.body.appendChild(pipeSpriteInv);

                let pipeSprite = document.createElement('div');
                pipeSprite.className = 'pipeSprite';
                pipeSprite.style.top = pipePosi + pipeGap + 'vh';
                pipeSprite.style.left = '100%';

                pipeSprite.style.width = '10%';
                pipeSprite.style.height = '70vh';
                pipeSprite.increaseScore = '1';
                if (localStorage.getItem('pipeskin') == 'greenPipe') {
                    pipeSprite.style.backgroundImage = `url(/img/unlocked/${localStorage.getItem('pipeskin')}.png)`;
                } else {
                    pipeSprite.style.backgroundImage = `url(/img/unlocked/${localStorage.getItem('pipeskin')}.jpg)`;
                }
                pipeSprite.style.backgroundSize = "contain";

                // if (localStorage.getItem('pipeskinMode') == '100%') {
                //     pipeSprite.style.backgroundSize = "100% 100%";
                // } else {
                //     pipeSprite.style.backgroundSize = localStorage.getItem('pipeskinMode');
                // }

                document.body.appendChild(pipeSprite);
            }
            window.pipeSeperation++;
            requestAnimationFrame(createPipe);
        }
        requestAnimationFrame(createPipe);
    }
})();

function vibrateAlreadyExistingAlert(dangerAlerts, alertText) {
    for (let i = 0; i < dangerAlerts.length; i++) {
        if (dangerAlerts[i].textContent.includes(alertText)) {
            deleteAllPopupsButOne(dangerAlerts[i]);
            vibrate(dangerAlerts[i]);
            return true;
        }
    }
    return false;
}


function createPopup(message, category, id='flash-messages') {
    let flashContainer = document.getElementById(id);
    let newAlert = document.createElement('div');
    newAlert.classList.add('alert');
    newAlert.classList.add('alert-' + category);
    newAlert.setAttribute('role', 'alert');
    newAlert.innerHTML = '<strong>' + message + '</strong>' + '<button type="button" class="close-btn" aria-label="Close">&#10006;</button>';
    flashContainer.appendChild(newAlert);

    newAlert.querySelector('.close-btn').addEventListener('click', function() {
        newAlert.classList.add('hidden');
        setTimeout(function() {
            newAlert.remove();
        }, 400);
    });

}


function vibrate(item) {
    item.classList.add('vibrate');
    setTimeout(function() {
        item.classList.remove('vibrate');
      }, 500);
    return;
}

function deletePopupsByCategory(category) {
    let alerts = document.querySelectorAll('.alert.alert-' + category);
    alerts.forEach(function(alert) {
        alert.remove();
    });
}

function deleteAllPopupsButOne(notDelete) {
    const alerts = document.getElementsByClassName('alert');
    for (let i = 0; i < alerts.length; i++) {
        if (alerts[i] !== notDelete) {
            alerts[i].remove();
        }
    }
}

async function logout() {
    await fetch('/clear_session', {
        method: 'POST',
    });

    window.location.reload();
}

function escapeListener(e) {
    if (e.key === 'Escape') {
        closeRegister();
        closeLogin();
        closeShop();
        closeInventory();
        closeSuggestions();
    }
}

function showPassword(checkBox, inputField) {
    let passwordInput = document.getElementById(inputField);
    let end = passwordInput.value.length;

    if (checkBox.checked) {
        passwordInput.type = 'text';
    } else {
        passwordInput.type = 'password';
    }

    // set foces on the end of the input
    passwordInput.setSelectionRange(end, end);
    passwordInput.focus();
}

async function login(username, password) {
    let headers = new Headers();
    headers.append('Content-Type', 'application/json');
    headers.append('Accept', 'application/json');

    const response = await fetch(`/login/${username}`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({password})
    });

    console.log(await response.text());
    if (response.ok) {
        window.location.reload();
    }
}


function loadJS(url, async=false, defer=false) {
    if (document.querySelector('script[src="' + url + '"]')) {
        return;
    } else {
        let script = document.createElement("script");
        script.src = url;
        script.defer = defer;
        script.async = async;
        document.head.appendChild(script);
    }
}

function openRegister() {
    closeLogin();
    if (window.gameState == 'Play') {
        window.gameState = 'Freeze';
    }
    if (!document.getElementById('register_page')) {
        registerLoad();
    }
    document.getElementById('register').style.display = 'block';
    addEventListener('keydown', escapeListener);
    loadJS('/js/register.js');
}


async function registerLoad() {
    response = await fetch('/register_form');

    html = await response.text();

    if (response.ok) {
        document.getElementById('register').innerHTML = html;
    } else {
        console.error('Error fetching registration form:', html);
    }
}

function closeRegister() {
    document.getElementById('register').innerHTML = '';
    removeEventListener('keydown', escapeListener);
}



function openLogin() {
    closeRegister();
    if (window.gameState == 'Play') {
        window.gameState = 'Freeze';
    }
    if (!document.getElementById('login_page')) {
        loginLoad();
    }
    document.getElementById('login').style.display = 'block';
    addEventListener('keydown', escapeListener);
    loadJS('/js/login.js');
}


async function loginLoad() {
    response = await fetch('/login_form');

    html = await response.text();

    if (response.ok) {
        document.getElementById('login').innerHTML = html;
    } else {
        console.error('Error fetching registration form:', html);
    }
}

function closeLogin() {
    document.getElementById('login').innerHTML = '';
    removeEventListener('keydown', escapeListener);
}


function openShop() {
    if (window.gameState == 'Play') {
        window.gameState = 'Freeze';
    }
    if (!document.getElementById('shop_page')) {
        shopLoad();
    }
    document.getElementById('shop').style.display = 'block';
    addEventListener('keydown', escapeListener);
    setTimeout(onLoadShop, 250);
}


async function shopLoad() {
    response = await fetch('/shop');

    html = await response.text();

    if (response.ok) {
        document.getElementById('shop').innerHTML = html;
    } else {
        console.error('Error fetching shop:', html);
    }
}


function closeShop() {
    document.getElementById('shop').innerHTML = '';
    removeEventListener('keydown', escapeListener);
}

async function openInventory() {
    if (window.gameState == 'Play') {
        window.gameState = 'Freeze';
    }
    if (!document.getElementById('inventory_page')) {
        await inventoryLoad();
        document.getElementById('inventory').style.display = 'block';
        onLoadInventory();
    } else {
        document.getElementById('inventory').style.display = 'block';
        onLoadInventory();
    }
    addEventListener('keydown', escapeListener);
}


async function inventoryLoad() {
    response = await fetch('/inventory');

    html = await response.text();

    if (response.ok) {
        document.getElementById('inventory').innerHTML = html;
    } else {
        console.error('Error fetching shop:', html);
    }
}


function closeInventory() {
    document.querySelector('#inventory').style.display = 'none';
    removeEventListener('keydown', escapeListener);
}

async function openSuggestions() {
    if (window.gameState == 'Play') {
        window.gameState = 'Freeze';
    }
    if (!document.getElementById('suggestions_page')) {
        await suggestionsLoad();
        document.getElementById('suggestions').style.display = 'block';
    } else {
        document.getElementById('suggestions').style.display = 'block';
    }
    addEventListener('keydown', escapeListener);
}


async function suggestionsLoad() {
    response = await fetch('/suggestions_form');

    html = await response.text();

    if (response.ok) {
        document.getElementById('suggestions').innerHTML = html;
    } else {
        console.error('Error fetching suggestions form:', html);
    }
}


function closeSuggestions() {
    document.querySelector('#suggestions').style.display = 'none';
    removeEventListener('keydown', escapeListener);
}


function camelCaseToSpaces(str) {
    let name = str.replace(/([a-z])([A-Z])/g, '$1 $2').toLowerCase();
    if (name.includes('nine eleven')) {
        name = name.replace('nine eleven', '9/11');
    }
    return name;
}

function openLeaderboard() {
    // Open the leaderboard and close the chat
    localStorage.setItem('selectedChat', 'leaderboard');
    document.querySelector('#leaderboard').style.display = 'block';
    document.querySelector('#chat').style.display = 'none';

    const navlinks = document.querySelectorAll('#chatToggle .navlink');

    // Change the selected link in the navigation bar
    for (let i = 0; i < navlinks.length; i++) {
        if (navlinks[i].innerHTML != 'Leaderboard') {
            navlinks[i].classList.remove('selectedLink');
        } else {
            navlinks[i].classList.add('selectedLink');
        }
    }
}

function openChat() {
    // Open the chat and close the leaderboard
    localStorage.setItem('selectedChat', 'chat');
    document.querySelector('#leaderboard').style.display = 'none';
    document.querySelector('#chat').style.display = 'block';

    loadMessages();

    // Change the selected link in the navigation bar
    const navlinks = document.querySelectorAll('.navlink');
    for (let i = 0; i < navlinks.length; i++) {
        if (navlinks[i].innerHTML != 'Chat') {
            navlinks[i].classList.remove('selectedLink');
        } else {
            navlinks[i].classList.add('selectedLink');
        }
    }

}


function loadMessages() {
    // If the messages are already loaded, don't load them again
    if (messagesLoaded) {
        return;
    }
    messagesLoaded = true;

    // Fetch the messages from the server and add them to the chat
    // Then create the socket connection to the server, so you can receive messages
    fetch('/messages')
        .then(response => response.json())
        .then(data => {
            let messages = document.getElementById('messages');
            data.forEach(msg => {
                let li = document.createElement('li');
                li.textContent = msg;
                messages.appendChild(li);
            });

            // Create the socket connection
            window.socket = io();

            // When a message is received, add it to the chat
            window.socket.on('message', function(msg){
                if (msg.includes('Error: ')) {
                    // create a message an delete it after 5 seconds
                    let li = document.createElement('li');
                    li.textContent = msg;
                    let ul = document.getElementById('messages');
                    ul.insertBefore(li, ul.firstChild);
                    setTimeout(function() {
                        li.remove();
                    }, 1000);
                } else {
                    let li = document.createElement('li');
                    li.textContent = msg;
                    let ul = document.getElementById('messages');
                    ul.insertBefore(li, ul.firstChild);
                }
            });
        });
}

function sendMessage(){
    // Get the message from the input field and send it to the server
    let input = document.getElementById('message');
    if (input.value == '') {return;}

    window.socket.send(input.value);
    input.value = '';
}

// On load of the page, check if there is an alert and add the event listener to the close button
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.alert')) {
        document.querySelector('.close-btn').addEventListener('click', function() {
            document.querySelector('.alert').classList.add('hidden');
        });
    }
});


let messagesLoaded = false;

if (!localStorage.getItem('selectedChat')) {
    openLeaderboard();
} else if (localStorage.getItem('selectedChat') == 'chat') {
    openChat();
} else if (localStorage.getItem('selectedChat') == 'leaderboard') {
    openLeaderboard();
}

// Add an event listener to the message input field, so you can send a message by pressing enter
document.getElementById('message').addEventListener('keydown', function(e) {
    if (e.key == 'Enter') {
        sendMessage();
    }
});