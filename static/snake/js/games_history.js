async function getGamesHistory(userId) {
    const response = await fetch(`/api/users/${userId}/games_history`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    });

    return await handleJsonResponse(response);
}

function snakeCaseToTitleCase(text) {
    let result = "";
    let nextCap = false;

    for (let i = 0; i < text.length; i++) {
        const letter = text[i];

        if (i === 0) {
            result += letter.toUpperCase();
            continue;
        }

        if (nextCap) {
            result += letter.toUpperCase();
            nextCap = false;
            continue;
        }
        if (letter === "_") {
            result += " ";
            nextCap = true;
        } else {
            result += letter;
        }
    }

    return result;
}

function createGameCard(gameId, opponentUsername, gameMode, outcome, score, duration, timeAgo) {
    const gameCard = `
        <div class="game-card" onclick="window.location.href = '/replay/${gameId}'">
            <img loading="lazy" class="game-thumbnail" src="/api/games/${gameId}/thumbnail" crossorigin="anonymous">
            <span class="game-mode game-info">${gameMode}</span>
            <span class="opponent game-info">${opponentUsername}</span>
            <span class="outcome game-info">${outcome}</span>
            <span class="score game-info">Score: <span class="score-value">${score}</span></span>
            <span class="game-duration game-info">Duur: ${duration}</span>
            <span class="game-end-time game-info">${timeAgo} geleden</span>
        </div>
    `;

    document.querySelector(".games-container").insertAdjacentHTML('beforeend', gameCard);
}

function parseGamesHistory(games) {
    const userId = localStorage.getItem("userId");
    if (!games) {
        return;
    }

    const sortedEntries = Object.entries(games).sort((a, b) => b[1].ended_at - a[1].ended_at);
    const sortedGames = Object.fromEntries(sortedEntries);

    for (const [gameId, game] of Object.entries(sortedGames)) {
        let opponentUsername = ``;

        const winner = game["winner"];
        const gameMode = game["game_mode"];
        const formattedGameMode = snakeCaseToTitleCase(gameMode);

        let outcome;
        if (gameMode === "one_vs_one") {
            if (!winner["user_id"]) {
                outcome = "Gelijkspel";
            } else if (game["winner"]["user_id"] === userId) {
                outcome = "Gewonnen";
            } else {
                outcome = "Verloren";
            }

            for (const playerId in game["players"]) {
                if (userId !== playerId) {
                    opponentUsername = `Opp: ${game["players"][playerId]["username"]}`;
                    break;
                }
            }
        } else {
            let opps = [];
            for (const playerId in game["players"]) {
                if (userId !== playerId) {
                    opps.push(game["players"][playerId]["username"]);
                }
            }

            if (opps.length > 0) {
                if (!winner["user_id"]) {
                    outcome = "Gelijkspel";
                } else {
                    outcome = `Winnaar: ${game["winner"]["username"]}`;
                }

                if (opps.length > 3) {
                    opponentUsername = `Opps: ${opps[0]}, ${opps[1]}, ${opps[2]} en meer`;
                } else {
                    for (let i =0; i < opps.length; i += 1) {
                        opponentUsername += `${opps[i]}`;
                        if (i === 0 && opps.length === 3) {
                            opponentUsername += `, `;
                        } else if (i === opps.length-2) {
                            opponentUsername += ` en `;
                        }
                    }

                    if (opps.length === 1) {
                        opponentUsername = `Opp: ${opponentUsername}`;
                    } else {
                        opponentUsername = `Opps: ${opponentUsername}`;
                    }
                }
            } else {
                outcome = "";
                opponentUsername = "";
            }
        }
        const score = game["score"];

        const duration = (game["ended_at"] - game["started_at"]).toFixed(0);
        const formattedDuration = formatTime(duration);

        const timeAgo = ((Date.now()/1000) - game["ended_at"]).toFixed(0);
        const formattedTimeAgo = formatTime(timeAgo);

        createGameCard(gameId, opponentUsername, formattedGameMode, outcome, score, formattedDuration, formattedTimeAgo);
    }

    document.querySelector(".games-container").innerHTML += `
        <div class="fade"></div>
    `;
}

const userId = window.location.toString().split("/")[window.location.toString().split("/").length-1]

getGamesHistory(userId).then((gamesHistory) => {
    parseGamesHistory(gamesHistory["data"]);
});
