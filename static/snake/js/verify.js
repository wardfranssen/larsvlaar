async function verify(code) {
    document.querySelector("#verify-form button i").style.display = "";

    const response = await fetch("/verify", {
        method: "POST",
        credentials: 'include',
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({code})
    });

    document.querySelector("#verify-form button i").style.display = "none";

    if (response.status === 429) {
        createGeneralPopup("Wow, niet zo snel", "error");
        document.querySelector("#reset-password-form button i").style.display = "none";
        document.querySelector("#verify-form button i").style.display = "none";
        return;
    }

    const responseJson = await response.json();

    if (response.ok) {
        localStorage.setItem("username", responseJson.username);
        localStorage.setItem("userId", responseJson.user_id);
        
        if (responseJson.redirect) {
            window.location.href = responseJson.redirect;
        }
    }else {
        if (responseJson.error === true) {
            if (responseJson.type === "general") {
                createGeneralPopup(responseJson.message, responseJson.category);
                return;
            }

            const error = document.getElementById(`${responseJson.type}-error`);
            error.classList.add("show");
            error.innerHTML = `<span>${responseJson.message}</span>`;
            
            document.getElementById(`${responseJson.type}-input`).focus();
        }
    }
}

document.getElementById("code-input").focus();

document.getElementById("verify-form").addEventListener("submit", async function(event) {
    event.preventDefault();
    clearCatErrors();

    const code = document.getElementById("code-input").value;

    await verify(code);
});
