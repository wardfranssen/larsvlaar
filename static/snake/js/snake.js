async function saveReplayThumbnail(gameId) {
    const board = document.querySelector(".snake-board");

    // Take snapshot
    const canvas = await html2canvas(board, {
        scale: 0.5,
        width: board.offsetWidth,
        height: board.offsetHeight
    });
    const dataURL = canvas.toDataURL("image/png");

    // Upload to server
    await fetch(`/api/games/${gameId}/upload_thumbnail`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify({
            image: dataURL
        })
    });
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
        default:
            return;
    }
    e.preventDefault(); // Stop scrolling issues

    sendSnakeDir(direction);
}

function sendSnakeDir(direction) {
    gameSocket.emit('snake_dir', {"snake_dir": direction});
}