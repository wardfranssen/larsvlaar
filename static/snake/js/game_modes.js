async function joinLobby(join_token) {
    const response = await fetch(`/api/lobby/${join_token}/join`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    });

    await handleJsonResponse(response);
}

function openJoinLobbyPopup() {
    document.getElementById("join-lobby-popup").classList.add("show");
    document.getElementById("join-token-input").focus();
}

function closeJoinLobbyPopup() {
    document.getElementById("join-lobby-popup").classList.remove("show");
}

function openFeedbackPopup() {
    document.querySelector(".feed-back-popup").classList.add("show");
    document.getElementById("feedback-input").focus();
}

function closeFeedbackPopup() {
    document.querySelector(".feed-back-popup").classList.remove("show");
}

async function sendKritiek(kritiek) {
    const response = await fetch(`/api/feedback`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify({ kritiek })
    });

    await handleJsonResponse(response);
}

const randomImgs = [
    "lars_met_hond.png",
    "lars_magister.jpg",
    "lars.jpg",
    "lars_badminton.jpg",
    "lars_is_dik.png",
    "vandalisme.jpg"
];

document.querySelector(".game-modes .circle-img").src = `/img/${randomImgs[Math.floor(Math.random()*randomImgs.length)]}`;

document.getElementById("join-lobby-form").addEventListener("submit", async function(event) {
    event.preventDefault();
    clearCatErrors();

    const join_token = document.getElementById("join-token-input").value;
    if (join_token.length > 0) {
        document.querySelector("#join-lobby-form button i").style.display = "";
        await joinLobby(join_token);
        document.querySelector("#join-lobby-form button i").style.display = "none";
    }
});

document.getElementById("feedback-form").addEventListener("submit", async function(event) {
    event.preventDefault();

    const kritiek = document.getElementById("feedback-input").value;
    if (kritiek.length > 10) {
        document.querySelector("#feedback-form button i").style.display = "";
        await sendKritiek(kritiek);
        document.querySelector("#feedback-form button i").style.display = "none";
    } else {
        const error = document.getElementById("feedback-error");
        error.classList.add("show");
        error.innerHTML = `<span>Feedback is te kort</span>`;
    }
});