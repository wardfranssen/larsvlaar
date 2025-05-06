async function changePassword(password, token, userId) {
    document.querySelector("#change-password-form button i").style.display = "";

    const response = await fetch("/api/auth/change_password", {
        method: "POST",
        credentials: 'include',
        headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        body: JSON.stringify({password, token, 'user_id': userId})
    });

    await handleJsonResponse(response);
    document.querySelector("#change-password-form button i").style.display = "none";
}


document.getElementById("change-password-form").addEventListener("submit", async function(event) {
    event.preventDefault();
    clearCatErrors();

    document.getElementById("password-dont-match").classList.remove("show");

    const password = document.getElementById("password-input").value;
    const confirmPassword = document.getElementById("confirm-password-input").value;

    if (!isStrongPassword(password)) {
        document.getElementById("password-input").focus();
        return;
    }

    if (password !== confirmPassword) {
        document.getElementById("confirm-password-input").focus();
        document.getElementById("password-dont-match").classList.add("show");
        return;
    }

    const parameters = new URLSearchParams(window.location.search);

    const token = parameters.get("token")
    const userId = parameters.get("user_id")

    await changePassword(password, token, userId);
});

document.getElementById("password-input").addEventListener("input", function() {
    const password = document.getElementById("password-input").value;
    const confirmPassword = document.getElementById("confirm-password-input").value;
    isStrongPassword(password);

    if (password === confirmPassword) {
        document.getElementById("password-dont-match").classList.remove("show");
    }
});

document.getElementById("confirm-password-input").addEventListener("input", function() {
    const password = document.getElementById("password-input").value;
    const confirmPassword = document.getElementById("confirm-password-input").value;

    if (password === confirmPassword) {
        document.getElementById("password-dont-match").classList.remove("show");
    }
});

