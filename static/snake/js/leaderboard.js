async function getLeaderboard(leaderboardName, offset, limit) {
    const response = await fetch(`/api/leaderboard/${leaderboardName}?offset=${offset}&limit=${limit}&game_modes=${selectedGameModeId}`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    const responseJson = await handleJsonResponse(response);
    return responseJson["leaderboard"];
}

async function selectLeaderboard(leaderboardId, leaderboardName) {
    const leaderboardData = await getLeaderboard(leaderboardId, 0, 20);
    const usersContainer = document.querySelector(".leaderboard .users");
    const currentUserDiv = document.getElementById("current-user");
    selectedLeaderboardId= leaderboardId;

    document.querySelector(".category").innerText = leaderboardName;
    usersContainer.innerHTML = "";
    currentUserDiv.innerHTML = "";
    currentUserDiv.classList.remove("show");

    let placement = 1;
    for (const userData of leaderboardData) {
        let specialPlacement = "";
        let currentUser = "";
        if (placement === 1) {
            specialPlacement = "first";
        } else if (placement === 2) {
            specialPlacement = "second";
        } else if (placement === 3) {
            specialPlacement = "third";
        }
        if (userData["user_id"] === currentUserId) {
            currentUser = "current-user";
        }

        const userDiv = `
            <div class="user ${specialPlacement} ${currentUser}">
                <div class="placement">#${placement}</div>

                <div class="user-profile">
                    <div class="pfp"><img src="/api/users/${userData["user_id"]}/pfp?v=${userData["pfp_version"]}"></div>
                    <div class="username">${userData["username"]}</div>
                </div>
                
                <div class="stat">${userData["stat"]}</div>
            </div>
        `;
        usersContainer.insertAdjacentHTML('beforeend', userDiv);


        if (userData["user_id"] === currentUserId) {
            currentUserDiv.insertAdjacentHTML('beforeend', userDiv);
        }

        placement++;
    }
    setTimeout(() => {
        checkUserVisibility();
    }, 100);
}

function selectGameMode(gameModeId, gameModeName) {
    document.querySelector(".game-mode").innerText = gameModeName;
    selectedGameModeId = gameModeId;

    const leaderboardName = document.querySelector(".category").innerText;
    selectLeaderboard(selectedLeaderboardId, leaderboardName);
}

function toggleGameModeDropdown(event) {
    event.stopPropagation();
    const dropdown = document.querySelector(".game-mode-selector .dropdown-content");
    dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";

    const categoryDropdown = document.querySelector(".category-selector .dropdown-content");
    categoryDropdown.style.display = 'none';
}


function toggleCategoryDropdown(event) {
    event.stopPropagation();
    const dropdown = document.querySelector(".category-selector .dropdown-content");
    dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";

    const gameModeDropdown = document.querySelector(".game-mode-selector .dropdown-content");
    gameModeDropdown.style.display = 'none';
}

function checkUserVisibility() {
    const usersContainer = document.querySelector(".leaderboard .users");
    const userDiv = usersContainer.querySelector(".current-user");

    if (!usersContainer || !userDiv) return;

    const containerRect = usersContainer.getBoundingClientRect();
    const userRect = userDiv.getBoundingClientRect();

    const isVisible = (
        userRect.bottom >= containerRect.top &&
        userRect.top <= containerRect.bottom
    );

    const currentUserContainer = document.getElementById("current-user");

    if (isVisible) {
        currentUserContainer.classList.remove("show");
        clearTimeout(currentUserDisplayTimeout);
    } else {
        clearTimeout(currentUserDisplayTimeout);
        currentUserDisplayTimeout = setTimeout(() => {
            currentUserContainer.classList.add("show");
        }, 100);
    }
}

document.addEventListener('click', function (event) {
    const category = document.querySelector('.category-selector');
    const gameMode = document.querySelector('.game-mode-selector');
    const categoryDropdown = category.querySelector(".dropdown-content");
    const gameModeDropdown = gameMode.querySelector(".dropdown-content");

    if (categoryDropdown && !category.contains(event.target)) {
        categoryDropdown.style.display = 'none';
    }
    if (gameModeDropdown && !gameMode.contains(event.target)) {
        gameModeDropdown.style.display = 'none';
    }
});

const currentUserId = localStorage.getItem("userId");
let selectedGameModeId = "all";
let selectedLeaderboardId;

// Set up scroll listener
const usersContainer = document.querySelector(".leaderboard .users");
let currentUserDisplayTimeout;

selectLeaderboard('game_count', 'Aantal Games').then(() => {
    setTimeout(() => {
        checkUserVisibility();
    }, 350);
});
selectGameMode('all', 'Alle Game Modes');

usersContainer.addEventListener("scroll", () => {
    checkUserVisibility();
});


