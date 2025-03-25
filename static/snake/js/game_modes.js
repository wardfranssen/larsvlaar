function openJoinGamePopup() {
    document.getElementById("join-game-popup").classList.add("show");
}

function closeJoinGamePopup() {
    document.getElementById("join-game-popup").classList.remove("show");
}

function openCreateGamePopup() {
    document.getElementById("create-game-popup").classList.add("show");
}

function closeCreateGamePopup() {
    document.getElementById("create-game-popup").classList.remove("show");
}

function createTablePreview(rows, columns) {
    const tablePreview = document.getElementById("table-preview");
    tablePreview.innerHTML = "";

    for (let i = 0; i < rows*columns; i++) {
        let divElt = document.createElement("div");
        divElt.classList.add("box");
        tablePreview.appendChild(divElt);
    }

    document.documentElement.style.setProperty("--preview-grid-rows", rows);
    document.documentElement.style.setProperty("--preview-grid-cols", columns);

}

function updateTablePreview(event) {
    const rowsInput = document.getElementById("rows-input");
    const columnsInput = document.getElementById("columns-input");

    if (isNaN(event.data)) {
        let newValue = rowsInput.value.replace(event.data, "");
        rowsInput.value = newValue;

        newValue = columnsInput.value.replace(event.data, "");
        columnsInput = newValue;
    } else {
        const rows = rowsInput.value;
        const columns = columnsInput.value;

        createTablePreview(rows, columns);
    }
}

const randomImgs = [
    "lars_met_hond.png",
    "lars_magister.jpg",
    "boze_lars.jpg",
    "lars.jpg",
    "lars_badminton.jpg",
    "lars_is_dik.png"
];

createTablePreview(15, 15);

document.querySelector(".game-modes img").src = `/img/${randomImgs[Math.floor(Math.random()*randomImgs.length)]}`;

document.getElementById("join-game-form").addEventListener("submit", async function(event) {
    event.preventDefault();
    clearCatErrors();

    const gameId = document.getElementById("game-id-input").value;

    if (gameId.length > 0) {
        document.querySelector("#join-game-form button i").style.display = "";
        await joinMatch(gameId, null);
        document.querySelector("#join-game-form button i").style.display = "none";
    }
});

document.getElementById("create-game-form").addEventListener("submit", async function(event) {
    event.preventDefault();
    clearCatErrors();

    const gameId = document.getElementById("game-id-input").value;

    if (gameId.length > 0) {
        document.querySelector("#create-game-form button i").style.display = "";
        await createMatch(gameId, null);
        document.querySelector("#create-game-form button i").style.display = "none";
    }
});

document.getElementById("rows-input").addEventListener("input", updateTablePreview);
document.getElementById("columns-input").addEventListener("input", updateTablePreview);