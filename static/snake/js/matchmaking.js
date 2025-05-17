const urlParams = window.location.search;
const params = new URLSearchParams(urlParams);
let redirectToGame;

// Convert game mode to title case
document.getElementById("game-mode-title").innerText = "One Vs One";

const matchmakingSocket = io(`/ws/one_vs_one/matchmaking`, { forceNew: true });

matchmakingSocket.on("found_match", (data) => {
    console.log(data);
});

matchmakingSocket.on("game_start", (data) => {
    const status = document.getElementById("status");
    const gameTips = document.getElementById("game-tips");
    const playerId = localStorage.getItem("userId");
    const players = data.players;

    console.log(players);

    // Only works for 1v1
    const opponentId = Object.keys(players).find(key => key !== playerId);
    const opponentUsername = players[opponentId].username;
    const opponentPfpVersion = players[opponentId].pfp_version;

    localStorage.setItem("opponent", JSON.stringify({"userId": opponentId, "username": opponentUsername, "pfpVersion": opponentPfpVersion}));

    status.innerText = "Tegenstander gevonden";
    gameTips.innerText = `Tegenstander: ${opponentUsername}`;

    redirectToGame = setTimeout(function () {
        // Tell server that player is leaving to join the game
        matchmakingSocket.emit("joining_game");
        
        // Need a timeout because otherwise disconnect might execute before joining_game is done
        setTimeout(function () {
            window.location.href = `/snake/one_vs_one?game_id=${data.game_id}&from=matchmaking`;
        }, 200);
    }, 2800);
});

matchmakingSocket.on("player_left", (data) => {
    if (redirectToGame) {
        clearInterval(redirectToGame);
    }
    document.getElementById("game-tips").innerHTML = gameTips[Math.floor(Math.random() * gameTips.length)];
        document.getElementById("status").innerHTML = `Lars is hard op zoek naar spelers <span id="wait"></span>`;

    console.log("player_left");
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
    "Lars' droom: Een slang zo lang als zijn eetlust",
    "Lars' slang is altijd de grootste in de kamer. Net als zijn eetlust",
    "Lars heeft honger",
    "Keukenrol Jans",
    "Macaron Jans",
    "Pantalon Jans",
    "Lebron Jans",
    "Lars' eetlust is oneindig, net zoals zijn wijsheid",
    "Investeer in je toekomst: zet alles op rood!",
    "Zet nooit in op zwart, zwart steelt je geld",
    "Klik op pijltje omhoog om omhoog te gaan",
    "Blijf als laatste over om te winnen!"
];

// Display a random game tip
document.getElementById("game-tips").innerHTML = gameTips[Math.floor(Math.random() * gameTips.length)];
