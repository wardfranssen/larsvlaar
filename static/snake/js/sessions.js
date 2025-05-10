async function getSessions() {
    const response = await fetch("/api/admin/sessions", {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    });

    return await handleJsonResponse(response);
}

async function deleteSession(sessionId, event) {
    event.stopPropagation();

    const response = await fetch(`/api/admin/sessions/${sessionId}`, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    });

    await handleJsonResponse(response);
    await createSessionsList();
}

function calculateRps(timestamps, timeWindow, now) {
    const windowMs = timeWindow * 1000;
    const filtered = timestamps.filter(ts => now - ts <= windowMs);
    return Math.round(filtered.length / timeWindow * 100) / 100;
}

async function createSessionsList() {
    const responseJson = await getSessions();
    const sessions = responseJson["sessions"];
    const serverTime = responseJson["server_time"];

    const sessionsContainer = document.getElementById("sessions-container");
    sessionsContainer.innerHTML = "";

    for (const [sessionId, session] of Object.entries(sessions)) {
        let rps10Sec = 0;
        let rps60Sec = 0;
        let totalRequests = 0;

        if (session.hasOwnProperty("requests") && session["requests"]) {
            rps10Sec = calculateRps(session["requests"]["total"], 10, serverTime);
            rps60Sec = calculateRps(session["requests"]["total"], 60, serverTime);
            totalRequests = session["requests"]["total"].length;
        }

        const sessionDiv = `
            <div class="session" onclick="window.open('/admin/sessions/${sessionId}', '_blank').focus();">
                <div class="user">
                    <div class="user-profile">
                        <div class="status ${session["status"]}"></div>
                        <div class="pfp"><img loading="lazy" src="/api/users/${session["user_id"]}/pfp?v=${session["pfp_version"]}"></div>
                        <div class="username">${session["username"]}</div>
                    </div>
                    
                    <div class="friend-button">                
                        <button class="close status-button" onclick="deleteSession('${sessionId}', event)">
                            <img src="/icon/close_black.svg" draggable="false">
                        </button>
                    </div>
                </div>

                <div class="rps-10-sec">${rps10Sec} rps afgelopen 10 sec</div>
                <div class="rps-60-sec">${rps60Sec} rps afgelopen minuut</div>
                <div class="total-requests">Totaal aantal requests: ${totalRequests}</div>
            </div>
        `;

        sessionsContainer.insertAdjacentHTML("beforeend", sessionDiv);
    }
}
createSessionsList();