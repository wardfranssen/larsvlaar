async function verify(code) {
    document.querySelector("#verify-form button i").style.display = "";

    const response = await fetch("/api/auth/verify", {
        method: "POST",
        credentials: 'include',
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify({code})
    });

    await handleJsonResponse(response, {
        onRedirect: (json) => {
            localStorage.setItem("username", json.username);
            localStorage.setItem("userId", json.user_id);
        }
    });
    document.querySelector("#verify-form button i").style.display = "none";
}

document.getElementById("code-input").focus();

document.getElementById("verify-form").addEventListener("submit", async function(event) {
    event.preventDefault();
    clearCatErrors();

    const code = document.getElementById("code-input").value;

    await verify(code);
});
