async function getKritiek() {
    const response = await fetch("/api/admin/kritiek", {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    });

    const responseJson = await handleJsonResponse(response);
    return responseJson["kritiek"];
}

async function deleteKritiek(kritiekId) {
    const response = await fetch(`/api/admin/kritiek/${kritiekId}`, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    });

    await handleJsonResponse(response);
    await createKritiekList();
}

async function createKritiekList() {
    const feedback = await getKritiek();

    const kritiekContainer = document.getElementById("kritiek-container");
    kritiekContainer.innerHTML = "";

    if (!feedback) {
        return;
    }

    for (const [kritiekId, kritiek] of Object.entries(feedback)) {
        const timeAgo = ((Date.now()/1000) - kritiek["created_at"]).toFixed(0);
        const formattedTimeAgo = formatTime(timeAgo);

        const kritiekDiv = `
            <div class="kritiek">
                <div class="user">
                    <div class="user-profile">
                        <div class="status ${kritiek["status"]}"></div>
                        <div class="pfp"><img loading="lazy" src="/api/users/${kritiek["user_id"]}/pfp?v=${kritiek["pfp_version"]}"></div>
                        <div class="username">${kritiek["username"]}</div>
                    </div>
                </div>

                <div class="friend-button">
                    <button class="close status-button" onclick="deleteKritiek('${kritiekId}')">
                        <img src="/icon/close_black.svg" draggable="false">
                    </button>
                </div>

                <div class="kritiek-text">${kritiek["kritiek"]}</div>
                
                <span class="created-at">${formattedTimeAgo} geleden</span>
            </div>
        `;

        kritiekContainer.insertAdjacentHTML("beforeend", kritiekDiv);
    }
}
createKritiekList();
