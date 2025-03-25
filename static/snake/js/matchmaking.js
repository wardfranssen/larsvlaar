const urlParams = window.location.search;
const params = new URLSearchParams(urlParams);
const gameMode = params.get("game_mode");
let redirectToGame;

// Convert game mode to title case
document.getElementById("game-mode-title").innerText = snakeCaseToTitleCase(gameMode);

const socket = io(`/matchmaking_${gameMode}`);

socket.on("found_match", (data) => {
    console.log(data);
});

socket.on("game_start", (data) => {
    const status = document.getElementById("status");
    const gameTips = document.getElementById("game-tips");
    const playerId = localStorage.getItem("userId");
    const players = data.players;
    const gameId = data.game_id;

    console.log(players);

    // Only works for 1v1
    const opponentId = Object.keys(players).find(key => key !== playerId);
    const opponentUsername = players[opponentId].username;

    status.innerText = "Tegenstander gevonden";
    gameTips.innerText = `Tegenstander: ${opponentUsername}`;

    redirectToGame = setTimeout(function () {
        // Tell server that player is leaving to join the game
        socket.emit("joining_game", {"game_id": gameId});
        
        // Need a timeout because otherwise disconnect might execute before joining_game is done
        setTimeout(function () {
            window.location.href = `/snake/${gameMode}?game_id=${data.game_id}`;
        }, 200);
    }, 2800);
});

socket.on("looking_for_players", function() {
    console.log("Waiting for players...");
});

socket.on("player_left", (data) => {
    if (redirectToGame) {
        // When other player leaves because the get redirected it also calls this function eventhough the other player is actually already in the game
        clearInterval(redirectToGame);
    }
    console.log();
});

window.dotsGoingUp = true;
const dots = window.setInterval( function() {
    const wait = document.getElementById("wait");
    if (!wait) {
        return;
    }
    if (window.dotsGoingUp){
        wait.innerHTML += ".";
    } else {
        wait.innerHTML = wait.innerHTML.substring(1, wait.innerHTML.length);
        if (wait.innerHTML === ".") {
            window.dotsGoingUp = true;
        }
    }
    if (wait.innerHTML.length > 3) {
        window.dotsGoingUp = false;
    }
}, 500);

const gameTips = [
    "Doneer! <a href='https://dev.larsvlaar.nl/doneer' target='_blank'>https://dev.larsvlaar.nl/doneer</a>",
    "Geniet van Lars' lichaam: <a href='https://dev.larsvlaar.nl/of' target='_blank'>https://dev.larsvlaar.nl/of</a>",
    "Lars is echt heel lekker!",
    "LOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOW!",
    "Imagine...",
    "Pro tip: Ga niet dood!",
    "Lars' buik is echt massive",
    "Hoe langer je slang, hoe moeilijker het wordt!",
    "Speel samen met vrienden voor extra plezier!",
    "Lars' droom: Een slang zo lang als zijn eetlust.",
    "Lars' slang is altijd de grootste in de kamer. Net als zijn eetlust.",
    "Lars heeft honger",
    "Keukenrol Jans",
    "Macaron Jans",
    "Pantalon Jans",
    "Lebron Jans",
    "Lars' eetlust is oneindig, net zoals zijn wijsheid.",
    "Lars heeft nog nooit een fout gemaakt. Fouten zijn bang voor hem."
];

// Display a random game tip
document.getElementById("game-tips").innerHTML = gameTips[Math.floor(Math.random() * gameTips.length)];